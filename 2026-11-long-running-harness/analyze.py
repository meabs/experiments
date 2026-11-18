#!/usr/bin/env python3
"""Summarise runs/*/result.json per condition: means with bootstrap 95% intervals, plus differences
between neighbouring conditions (each adds one component). Stdlib only.

Usage: python3 analyze.py [--model TAG]
"""
import argparse
import json
import random
from pathlib import Path

ORDER = ['bare', 'notes', 'featurelist', 'full']
RUNS = Path(__file__).parent / 'runs'


def boot(xs, f=lambda v: sum(v) / len(v), n=4000, seed=1):
    rng = random.Random(seed)
    if len(xs) < 2:
        return None
    b = sorted(f([rng.choice(xs) for _ in xs]) for _ in range(n))
    return b[int(.025 * n)], b[int(.975 * n)]


def boot_diff(a, b, n=4000, seed=2):
    rng = random.Random(seed)
    if len(a) < 2 or len(b) < 2:
        return None
    d = sorted(sum(rng.choice(b) for _ in b) / len(b) - sum(rng.choice(a) for _ in a) / len(a) for _ in range(n))
    return d[int(.025 * n)], d[int(.975 * n)]


def fisher(a, n1, b, n2):
    """Two-sided Fisher exact p for a/n1 vs b/n2 (hypergeometric, stdlib)."""
    from math import comb
    k, n = a + b, n1 + n2
    def pr(x):
        return comb(n1, x) * comb(n2, k - x) / comb(n, k)
    p0 = pr(a)
    return min(1.0, sum(pr(x) for x in range(max(0, k - n2), min(n1, k) + 1) if pr(x) <= p0 * (1 + 1e-9)))


def fmt(v, ci, pct=False):
    s = '%.1f%%' % (100 * v) if pct else '%.2f' % v
    if ci:
        s += ' (%s to %s)' % (('%.1f%%' % (100 * ci[0]), '%.1f%%' % (100 * ci[1])) if pct else
                              ('%.2f' % ci[0], '%.2f' % ci[1]))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model')
    a = ap.parse_args()
    rs = [json.loads(p.read_text()) for p in sorted(RUNS.glob('*/result.json'))]
    rs = [r for r in rs if (not a.model or r['model'] == a.model) and not r['error']]
    by = {c: [r for r in rs if r['condition'] == c] for c in ORDER}
    print('| condition | n | features passed /12 | all 12 | declared done | premature victory | '
          'broken sessions | list edits | false claims | cost/run |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for c in ORDER:
        g = by[c]
        if not g:
            continue
        sc = [r['final_passed'] for r in g]
        n = len(g)
        print('| %s | %d | %s | %d/%d | %d/%d | %d/%d | %.2f | %.2f | %.2f | $%.3f |' % (
            c, n, fmt(sum(sc) / n, boot(sc)), sum(1 for s in sc if s == 12), n,
            sum(r['done_declared'] for r in g), n, sum(r['premature_victory'] for r in g), n,
            sum(r['broken_sessions'] for r in g) / n, sum(r['fl_violations'] for r in g) / n,
            sum(r['false_claims'] for r in g) / n, sum(r['cost'] for r in g) / n))
    print('\nDifference in mean features passed, each condition minus the one before:')
    for p, q in zip(ORDER, ORDER[1:]):
        if by[p] and by[q]:
            x, y = [r['final_passed'] for r in by[p]], [r['final_passed'] for r in by[q]]
            d = sum(y) / len(y) - sum(x) / len(x)
            print('  %-11s - %-11s %+.2f  95%% interval %s' % (q, p, d, boot_diff(x, y)))
    if by['bare'] and by['full']:
        x, y = [r['final_passed'] for r in by['bare']], [r['final_passed'] for r in by['full']]
        print('  %-11s - %-11s %+.2f  95%% interval %s' % ('full', 'bare', sum(y) / len(y) - sum(x) / len(x),
                                                             boot_diff(x, y)))
    print('\nBinary outcomes, neighbouring conditions (exact test, two-sided, unadjusted, exploratory):')
    for p, q in list(zip(ORDER, ORDER[1:])) + [('bare', 'full')]:
        if by[p] and by[q]:
            for label, f in (('reached 12/12', lambda r: r['final_passed'] == 12),
                             ('premature victory', lambda r: r['premature_victory'])):
                a_, b_ = sum(map(f, by[p])), sum(map(f, by[q]))
                print('  %-11s vs %-11s %-18s %d/%d vs %d/%d  p=%.3f' % (
                    q, p, label, b_, len(by[q]), a_, len(by[p]), fisher(a_, len(by[p]), b_, len(by[q]))))
    print('\nTotal cost of these runs: $%.3f' % sum(r['cost'] for r in rs))


if __name__ == '__main__':
    main()
