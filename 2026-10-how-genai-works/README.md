# How does generative AI work? Measured demos

**Status: done, 2026-10-31.** Not an experiment with hypotheses: a set of measurements on a real model, so that an
explainer article and video can show real numbers for each step of "what happens when you send a prompt", instead of
illustrative ones.

## What was measured

All on **Qwen/Qwen3-0.6B-Base** (Apache 2.0; 596,049,920 parameters, 28 layers, 16 attention heads per layer,
vectors of 1,024 numbers, a vocabulary of 151,936 tokens), run locally with Hugging Face transformers on a Radeon
8060S. It's a *base* model: trained to continue text, without the extra training that makes chat models answer
questions. One comparison uses a 27B model (qwen3.8:27b, Q4_K_M, local Ollama).

| Step | Demo | Result (results/demos.json, demos2.json) |
| --- | --- | --- |
| Tokens | "Why is the sky blue?" | 6 tokens: `Why`, `·is`, `·the`, `·sky`, `·blue`, `?` (ids 10234, 374, 279, 12884, 6303, 30); "unbelievably" splits into `·unbelie` + `vably` |
| Vectors | The vector for the last word of "A picture of a <word>", 20 words picked before looking (animals, vehicles, fruit, colours), cosine similarity to "cat" | Middle layer (14 of 28), centred: kitten 0.55, dog 0.42, mouse 0.24, car 0.14; furthest yellow −0.31, orange −0.29, lemon −0.27 |
| Attention | "The animal didn't cross the street because it was too tired": for "it", each of the 448 heads' most-attended earlier token (first token excluded) | because 206, 't 64, street 53, animal 42, cross 38, didn 24, the 21 |
| Next-token odds | "The cat sat on the" | 0.6B: chair 6.3%, edge 4.6%, window 3.9%, couch 3.7%, mat 3.2%. 27B: mat 84.3%, `______` 1.8%, table 0.8% |
| | "The capital of France is" | Paris 34.6%; then blanks (`____` 11.0%) |
| The loop | "The sky is blue because", top choice 10 times | "…the molecules in the air are ________.\nAnswer": a quiz sheet, which is a common shape in training text |
| Temperature | "My favourite colour is", 20 samples (seeds 1–20) at each temperature | 0: blue ×20 (1 distinct); 0.7: 7 distinct; 1.5: 17 distinct, including Guinness, liver and vinegar |
| Made-up facts | "Q: What is the capital of Zarnovia?\nA: The capital of Zarnovia is" (no such country), greedy | " Zarnovia City." |

## Honest notes

- **The first vector run was unclear.** At the last layer every vector points in nearly the same direction (cat to
  anything: 0.89 to 0.98), and dog edged out kitten. `demos2.py` was written after seeing that: it compares layers 1,
  14 and 28, with and without centring (subtracting the 20 vectors' mean). Every version puts animals nearest cat and
  colours or fruit furthest; the exact numbers depend on the layer. The article uses layer 14 centred, and says so.
- **The attention result isn't the textbook one.** The usual illustration shows "it" attending to "animal"; here 42
  of 448 heads did that most, and 206 looked hardest at "because". Reported as found. "Most-attended token per head"
  is one simple view of attention, not a full analysis.
- **A small base model is not a chat assistant.** Its odds and its quiz-sheet continuation show what the underlying
  machinery does; chat models add instruction training on top.

## Reproduce

```bash
python -I src/demos.py    # results/demos.json (downloads Qwen/Qwen3-0.6B-Base, ~1.1 GB, on first run)
python -I src/demos2.py   # results/demos2.json (needs a local Ollama with qwen3.8:27b for the 27B comparison)
bash diagrams/render.sh   # the article's diagrams, with headless Chrome
```

Needs torch and transformers (here: torch 2.12 ROCm nightly for gfx1151, transformers 5.22.1).
