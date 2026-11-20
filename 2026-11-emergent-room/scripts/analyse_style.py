#!/usr/bin/env python3
"""Measures 1 and 2 (README section 6): can a text-only classifier tell the agents apart, and does style follow the
model or the agent's memory after the A/C swap? Exploratory. python3 -I scripts/analyse_style.py [db] -> results/analysis_style.json"""
import json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DB = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "results" / "events.sqlite")
rng = np.random.default_rng(1)


def clean(t):
    t = t.lower()
    t = re.sub(r"agent\s+[abc]\b'?s?", " ", t)      # no agent names
    t = re.sub(r"\b[abc]'s\b", " ", t)
    t = re.sub(r"\bv\d+\b", " ", t)
    return t


def load():
    c = sqlite3.connect(DB)
    rows = c.execute("select session,agent,text,id from events where kind='message' and session between 1 and 5 order by id").fetchall()
    out, rank = [], Counter()
    for s, a, t, i in rows:
        rank[(s, a)] += 1
        out.append(dict(session=s, agent=a, text=clean(t), rank=rank[(s, a)]))
    return out


def toks(t):
    w = re.findall(r"[a-z']+|[?!:;()*#\-]", t)
    return w + [f"{x} {y}" for x, y in zip(w, w[1:])]


def tfidf(msgs):
    docs = [Counter(toks(m["text"])) for m in msgs]
    df = Counter(k for d in docs for k in d)
    vocab = {k: i for i, k in enumerate(sorted(k for k, v in df.items() if v >= 3))}
    X = np.zeros((len(msgs), len(vocab)))
    for r, d in enumerate(docs):
        for k, v in d.items():
            if k in vocab: X[r, vocab[k]] = (1 + np.log(v)) * np.log(len(docs) / df[k])
    n = np.linalg.norm(X, axis=1, keepdims=True); n[n == 0] = 1
    return X / n


def centroid_predict(Xtr, ytr, Xte, classes):
    C = np.stack([Xtr[ytr == k].mean(0) for k in classes])
    C /= np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-12)
    return np.array(classes)[np.argmax(Xte @ C.T, axis=1)]


def balanced_acc(y, p, classes):
    return float(np.mean([np.mean(p[y == k] == k) for k in classes if (y == k).any()]))


def loso(X, y, sess, folds, classes):
    ys, ps = [], []
    for f in folds:
        te, tr = sess == f, np.isin(sess, [g for g in folds if g != f])
        if not (te.any() and all((y[tr] == k).any() for k in classes)): continue
        ys.append(y[te]); ps.append(centroid_predict(X[tr], y[tr], X[te], classes))
    return balanced_acc(np.concatenate(ys), np.concatenate(ps), classes)


def pair_test(msgs, X, pair, folds, label, n_perm=10000, skip_openers=0):
    idx = [i for i, m in enumerate(msgs) if m["agent"] in pair and m["session"] in folds and m["rank"] > skip_openers]
    Xs, y, sess = X[idx], np.array([msgs[i]["agent"] for i in idx]), np.array([msgs[i]["session"] for i in idx])
    obs = loso(Xs, y, sess, folds, list(pair))
    null = []
    for _ in range(n_perm):
        yp = y.copy()
        for f in folds:                              # shuffle which message belongs to which agent, inside a session
            m = sess == f; yp[m] = rng.permutation(y[m])
        null.append(loso(Xs, yp, sess, folds, list(pair)))
    null = np.array(null)
    return dict(test=label, n_messages=len(idx), balanced_accuracy=round(obs, 3), null_mean=round(float(null.mean()), 3),
                null_95th=round(float(np.quantile(null, .95)), 3), p_one_sided=round(float((np.sum(null >= obs) + 1) / (n_perm + 1)), 4))


def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def main():
    msgs = load(); X = tfidf(msgs)
    res = {"n_messages_sessions_1_to_5": len(msgs), "vocab": int(X.shape[1])}
    T = []
    for skip in (0, 3):
        sfx = " (first 3 messages of each agent per session excluded)" if skip else ""
        T.append(pair_test(msgs, X, ("A", "B"), (1, 2, 3), "A vs B, sessions 1-3 (both gpt-5.6-luna)" + sfx, skip_openers=skip))
        T.append(pair_test(msgs, X, ("B", "C"), (1, 2, 3), "B vs C, sessions 1-3 (luna vs haiku): positive control" + sfx, skip_openers=skip))
    T.append(pair_test(msgs, X, ("B", "C"), (4, 5), "B vs C, sessions 4-5 (both gpt-5.6-luna after the swap)"))
    T.append(pair_test(msgs, X, ("A", "B"), (4, 5), "A vs B, sessions 4-5 (haiku vs luna)"))
    res["pairs"] = T
    # model vs memory: train A/B/C on sessions 1-3, label sessions 4-5 messages
    ses = np.array([m["session"] for m in msgs]); ag = np.array([m["agent"] for m in msgs])
    tr, te = ses <= 3, ses >= 4
    pred = centroid_predict(X[tr], ag[tr], X[te], ["A", "B", "C"])
    mm = {}
    for a, fam_after in (("A", "haiku (was luna)"), ("C", "luna (was haiku)"), ("B", "luna (unchanged)")):
        p = pred[ag[te] == a]; n = len(p)
        mm[a] = dict(model_in_4_5=fam_after, n=n, predicted=dict(Counter(p.tolist())))
    # A: memory-follows predicts A; model-follows predicts C (haiku style). C: memory predicts C; model predicts A or B (luna style).
    a_mem = mm["A"]["predicted"].get("A", 0); a_mod = mm["A"]["predicted"].get("C", 0)
    c_mem = mm["C"]["predicted"].get("C", 0); c_mod = mm["C"]["predicted"].get("A", 0) + mm["C"]["predicted"].get("B", 0)
    mm["summary"] = dict(
        A_labelled_as_A_memory=[a_mem, mm["A"]["n"], wilson(a_mem, mm["A"]["n"])], A_labelled_as_C_model=[a_mod, mm["A"]["n"], wilson(a_mod, mm["A"]["n"])],
        C_labelled_as_C_memory=[c_mem, mm["C"]["n"], wilson(c_mem, mm["C"]["n"])], C_labelled_as_A_or_B_model=[c_mod, mm["C"]["n"], wilson(c_mod, mm["C"]["n"])])
    res["model_vs_memory"] = mm
    # does a 2-class model classifier (haiku vs luna) trained on 1-3 transfer to 4-5?
    fam_tr = np.where(ag[tr] == "C", "haiku", "luna")
    fam_te = np.where(ag[te] == "A", "haiku", "luna")
    pf = centroid_predict(X[tr], fam_tr, X[te], ["haiku", "luna"])
    res["model_classifier_on_4_5"] = dict(balanced_accuracy=round(balanced_acc(fam_te, pf, ["haiku", "luna"]), 3), n=int(te.sum()))
    # descriptive: lengths
    res["mean_chars"] = {f"s{s}": {a: round(float(np.mean([len(m['text']) for m in msgs if m['session'] == s and m['agent'] == a]))) for a in "ABC"} for s in range(1, 6)}
    Path(ROOT / "results" / "analysis_style.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


main()
