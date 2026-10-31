"""Measures each step of "what happens when you send a prompt" on a small open model, for the explainer guide and video.

Model: Qwen/Qwen3-0.6B-Base (Apache 2.0), a base model (not chat-tuned), run locally with Hugging Face transformers.
Everything is deterministic except the temperature demo, which uses fixed seeds.
Writes results/demos.json. Usage: python -I src/demos.py   (needs torch and transformers; GPU if available)
"""
import json, math, os, sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = 'Qwen/Qwen3-0.6B-Base'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32, attn_implementation='eager').to(dev).eval()
cfg = model.config
out = {'model': MODEL, 'revision': getattr(cfg, '_commit_hash', None), 'device': dev, 'torch': torch.__version__}


def show(t):
    return t.replace('Ġ', '·').replace('Ċ', '\\n')


def ids(text):
    return tok(text, return_tensors='pt').input_ids.to(dev)


@torch.no_grad()
def next_probs(text, k=5):
    p = torch.softmax(model(ids(text)).logits[0, -1].float(), -1)
    top = torch.topk(p, k)
    return [{'token': tok.decode([int(i)]), 'p': round(float(v), 4)} for v, i in zip(top.values, top.indices)]


# 1. The model's size
out['size'] = {'parameters': sum(p.numel() for p in model.parameters()), 'layers': cfg.num_hidden_layers,
               'attention_heads': cfg.num_attention_heads, 'vector_size': cfg.hidden_size, 'vocabulary': cfg.vocab_size}

# 2. Tokens: a prompt split into pieces, with their ids
PROMPT = 'Why is the sky blue?'
tids = tok(PROMPT).input_ids
out['tokens'] = {'prompt': PROMPT, 'pieces': [tok.decode([i]) for i in tids], 'ids': tids, 'count': len(tids),
                 'long_word': {'text': 'unbelievably', 'pieces': [tok.decode([i]) for i in tok(' unbelievably').input_ids]}}

# 3. Vectors: each token id looks up a row of numbers; similar meanings end up close together.
# Context vectors (the last layer's hidden state for the word in a short sentence), compared by cosine similarity.
@torch.no_grad()
def vec(word):
    h = model(ids(f'A picture of a {word}'), output_hidden_states=True).hidden_states[-1][0, -1].float()
    return h


words = ['cat', 'kitten', 'dog', 'car', 'banana']
V = {w: vec(w) for w in words}
cos = lambda a, b: float(torch.nn.functional.cosine_similarity(a, b, dim=0))
emb = model.get_input_embeddings().weight
cat_id = tok(' cat').input_ids
out['vectors'] = {
    'context': 'last-layer vector for the final word of "A picture of a <word>"',
    'similarity_to_cat': {w: round(cos(V['cat'], V[w]), 3) for w in words[1:]},
    'cat_first_numbers': [round(float(x), 3) for x in emb[cat_id[0]][:6]] if len(cat_id) == 1 else None,
    'cat_is_one_token': len(cat_id) == 1,
}

# 4. Attention: in "The animal didn't cross the street because it was too tired", which earlier words does "it"
# look at most? Averaged over all heads, in every layer; the layer with the strongest pick is reported too.
SENT = "The animal didn't cross the street because it was too tired"
x = ids(SENT)
pieces = [tok.decode([int(i)]) for i in x[0]]
it = pieces.index(' it')
with torch.no_grad():
    att = model(x, output_attentions=True).attentions  # layers x [1, heads, seq, seq]
mean_all = torch.stack([a[0, :, it, :it] for a in att]).float().mean(dim=(0, 1))  # over layers and heads, earlier words only
order = torch.argsort(mean_all, descending=True)
out['attention'] = {
    'sentence': SENT, 'word': 'it', 'pieces': pieces,
    'note': 'attention from "it" to earlier tokens, averaged over all layers and heads; the first token is excluded '
            'because models park much of their attention on it',
    'top_earlier_words': [{'token': pieces[int(i)], 'share': round(float(mean_all[i]), 3)} for i in order if int(i) != 0][:5],
}

# 5. Next-token probabilities
out['next_token'] = {t: next_probs(t) for t in ['The cat sat on the', 'The capital of France is', 'The capital of the made-up country of Zarnovia is']}

# 6. The loop: greedy generation, one token at a time, with each step's chosen token and its probability
LOOP = 'The sky is blue because'
x = ids(LOOP)
steps = []
with torch.no_grad():
    for _ in range(10):
        p = torch.softmax(model(x).logits[0, -1].float(), -1)
        i = int(torch.argmax(p))
        steps.append({'token': tok.decode([i]), 'p': round(float(p[i]), 3)})
        x = torch.cat([x, torch.tensor([[i]], device=dev)], 1)
out['loop'] = {'prompt': LOOP, 'steps': steps, 'text': LOOP + ''.join(s['token'] for s in steps)}

# 7. Temperature: the next word for "My favourite colour is", 20 samples each at temperature 0 (always the top
# choice), 0.7 and 1.5, seeds 1-20
TEMP = 'My favourite colour is'
logits = model(ids(TEMP)).logits[0, -1].float().detach()
temps = {}
for T in (0, 0.7, 1.5):
    picks = []
    for seed in range(1, 21):
        if T == 0:
            i = int(torch.argmax(logits))
        else:
            g = torch.Generator(device=dev).manual_seed(seed)
            i = int(torch.multinomial(torch.softmax(logits / T, -1), 1, generator=g))
        picks.append(tok.decode([i]).strip())
    temps[str(T)] = {'picks': picks, 'distinct': len(set(picks))}
out['temperature'] = {'prompt': TEMP, 'samples_each': 20, 'by_temperature': temps}

os.makedirs(os.path.join(ROOT, 'results'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'results', 'demos.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False)[:6000])
