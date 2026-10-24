"""Builds the vector index and retrieves the documents for every question (README, "Retrieval").

Corpus: every distinct paragraph in HotpotQA dev (distractor setting), as "<title>: <sentences joined>". Embedded with
bge-m3 through Ollama (/api/embed), batches of 64, vectors normalised; cached as <cache dir>/vectors.npy and corpus.json.
For each question, the query vector is the question text, and paragraphs are ranked by cosine similarity.
  clean    the top 5. If no poisoned (answer-bearing gold) paragraph is in it, the best-ranked one replaces rank 5.
           The natural top-5 and whether it held the answer paragraph are recorded.
  miss     the top 5 after removing every paragraph that contains the answer's number.
Output: items/retrieved.json (paragraph texts per condition, in rank order), so the runs need no index.
Usage: uv run --with numpy python3 -I retrieve.py <hotpot dev json> <items.json> <cache dir> <out.json>
"""
import json, os, re, sys, time, urllib.request
import numpy as np

URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"
K = 5


def embed(texts):
    body = json.dumps({"model": MODEL, "input": texts}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(URL, body, {"Content-Type": "application/json"}), timeout=1200))
    v = np.array(r["embeddings"], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def contains(text, tok):
    return re.search(rf"(?<![\w.,]){re.escape(tok)}(?![\w]|[.,]\d)", text) is not None


def main():
    src, items_f, cache, out = sys.argv[1:5]
    os.makedirs(cache, exist_ok=True)
    cf, vf = os.path.join(cache, "corpus.json"), os.path.join(cache, "vectors.npy")
    if os.path.exists(vf):
        corpus, V = json.load(open(cf)), np.load(vf)
    else:
        seen, corpus = set(), []
        for d in json.load(open(src)):
            for title, sents in d["context"]:
                text = f"{title}: {''.join(sents).strip()}"
                if text not in seen:
                    seen.add(text); corpus.append(dict(title=title, text=text))
        t = time.time(); parts = []
        for i in range(0, len(corpus), 64):
            parts.append(embed([c["text"] for c in corpus[i:i + 64]]))
            if i % 6400 == 0:
                print(f"embedded {i}/{len(corpus)} in {time.time() - t:.0f}s", flush=True)
        V = np.vstack(parts)
        json.dump(corpus, open(cf, "w")); np.save(vf, V)
        print(f"index: {len(corpus)} paragraphs, {time.time() - t:.0f}s", flush=True)
    items = json.load(open(items_f))
    data = {d["_id"]: d for d in json.load(open(src))}
    res = []
    for it in items:
        d = data[it["id"]]
        own = {f"{t}: {''.join(s).strip()}" for t, s in d["context"] if t in it["poison"]}
        q = embed([it["question"]])[0]
        order = np.argsort(-(V @ q))
        top = [int(j) for j in order[:K]]
        hit = any(corpus[j]["text"] in own for j in top)
        clean = list(top)
        if not hit:
            best = next(int(j) for j in order if corpus[j]["text"] in own)
            clean[-1] = best
        miss = [int(j) for j in order if not contains(corpus[j]["text"], it["number"])][:K]
        res.append(dict(id=it["id"], natural_hit=hit, natural_top=[corpus[j]["text"] for j in top],
                        clean=[corpus[j]["text"] for j in clean], poisoned_paragraphs=[t for t in (corpus[j]["text"] for j in clean) if t in own],
                        miss=[corpus[j]["text"] for j in miss]))
    json.dump(res, open(out, "w"), indent=1)
    print(f"retrieved {len(res)} questions; answer paragraph in the natural top {K}: {sum(r['natural_hit'] for r in res)}")


main()
