"""Follow-up measurements, written after demos.py's first run (see README): vectors at several layers, attention per
head, a made-up-fact continuation, and the same next-token question on a 27B model via a local Ollama server.

Writes results/demos2.json. Usage: python -I src/demos2.py
"""
import json, math, os, urllib.request

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = 'Qwen/Qwen3-0.6B-Base'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32, attn_implementation='eager').to(dev).eval()
out = {'model': MODEL}


def ids(text):
    return tok(text, return_tensors='pt').input_ids.to(dev)


# 1. Vectors at several layers. Words chosen before looking at any result: animals, vehicles, fruit, colours.
WORDS = ['cat', 'kitten', 'dog', 'puppy', 'horse', 'mouse', 'car', 'bus', 'train', 'bicycle', 'truck', 'banana',
         'apple', 'orange', 'grape', 'lemon', 'red', 'green', 'purple', 'yellow']
with torch.no_grad():
    H = {w: model(ids(f'A picture of a {w}'), output_hidden_states=True).hidden_states for w in WORDS}
L = model.config.num_hidden_layers
vec_results = {}
for layer in (1, L // 2, L):
    M = torch.stack([H[w][layer][0, -1].float() for w in WORDS])
    for centred in (False, True):
        X = M - M.mean(0) if centred else M
        X = torch.nn.functional.normalize(X, dim=1)
        S = X @ X.T
        i = WORDS.index('cat')
        order = [int(j) for j in torch.argsort(S[i], descending=True) if int(j) != i]
        vec_results[f'layer {layer}{" centred" if centred else ""}'] = {
            'nearest_to_cat': [(WORDS[j], round(float(S[i, j]), 3)) for j in order[:5]],
            'farthest_from_cat': [(WORDS[j], round(float(S[i, j]), 3)) for j in order[-3:]],
            'cat_kitten': round(float(S[i, WORDS.index('kitten')]), 3), 'cat_car': round(float(S[i, WORDS.index('car')]), 3),
            'cat_banana': round(float(S[i, WORDS.index('banana')]), 3)}
out['vectors'] = {'words': WORDS, 'sentence': 'A picture of a <word>', 'note': 'centred: the mean of the 20 vectors '
                  'subtracted first, which removes the direction every vector shares', 'by_layer': vec_results}

# 2. Attention per head: for "it", each head's most-attended earlier word (excluding the first token)
SENT = "The animal didn't cross the street because it was too tired"
x = ids(SENT)
pieces = [tok.decode([int(i)]) for i in x[0]]
it = pieces.index(' it')
with torch.no_grad():
    att = model(x, output_attentions=True).attentions
picks = {}
for a in att:
    for h in range(a.shape[1]):
        row = a[0, h, it, 1:it].float()
        w = pieces[1 + int(torch.argmax(row))]
        picks[w] = picks.get(w, 0) + 1
out['attention_heads'] = {'sentence': SENT, 'heads': sum(picks.values()),
                          'top_pick_counts': dict(sorted(picks.items(), key=lambda kv: -kv[1]))}

# 3. A made-up fact: greedy continuation of a question about a country that doesn't exist
Z = 'Q: What is the capital of Zarnovia?\nA: The capital of Zarnovia is'
x = ids(Z)
with torch.no_grad():
    g = model.generate(x, max_new_tokens=12, do_sample=False)
out['made_up'] = {'prompt': Z, 'continuation': tok.decode(g[0, x.shape[1]:])}

# 4. The same next-token question on a 27B model (local Ollama, qwen3.8:27b, raw prompt, temperature 0)
def ollama(prompt):
    body = {'model': 'qwen3.8:27b', 'prompt': prompt, 'raw': True, 'stream': False, 'logprobs': True, 'top_logprobs': 5,
            'options': {'num_predict': 1, 'temperature': 0}}
    d = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:11434/api/generate',
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}), timeout=600))
    return [{'token': t['token'], 'p': round(math.exp(t['logprob']), 4)} for t in d['logprobs'][0]['top_logprobs']]

try:
    out['big_model'] = {'model': 'qwen3.8:27b (Ollama, Q4_K_M)', 'The cat sat on the': ollama('The cat sat on the'),
                        Z: ollama(Z)}
except Exception as e:
    out['big_model'] = {'error': str(e)}

json.dump(out, open(os.path.join(ROOT, 'results', 'demos2.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
