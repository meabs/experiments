"""Analysis for visual-checks (the design's measures and hypotheses), written before the main run's results were read.

  python3 -I analyse.py [results dir]      default results/  ->  results/analysis.md, results/summary.json

A checker's verdict on a screenshot is the majority of its calls (3; the pixel diff runs once). Flagged means:
  pixel: more than 0.5% of pixels changed; jev-assert: any assertion's noul below 0.5; jev-open: noul 0.5 or more;
  vlm-assert: any assertion answered "no"; vlm-review: at least one defect listed. A call that returns no usable
  answer counts as not flagged and is reported.
Right reason (assertion checkers): a flagged defect screenshot where some flagged assertion is one of the defect's
`covered_by` assertions (fixed in variants.json before the main run).
Tests: paired sign-flip permutation tests over screenshots (10,000, seed 1); H2 non-inferiority by bootstrap over
defect types (10,000, seed 1); Holm over H1, H3, H4. Wilson 95% intervals for every rate.
"""
import glob, json, math, os, random, sys

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(E, 'results')
V = {v['id']: v for v in json.load(open(os.path.join(E, 'variants', 'variants.json')))}


def flagged(c, d):
    if c == 'pixel':
        return d['changed'] > 0.005, []
    if c in ('jev-assert', 'jev-open', 'jev-open-criteria'):
        a = d.get('answers') or {}
        if c in ('jev-open', 'jev-open-criteria'):
            return (a.get('defect') or 0) >= 0.5, []
        bad = [k for k, v in a.items() if v is not None and v < 0.5]
        return bool(bad), bad
    p = d.get('parsed')
    if not isinstance(p, dict):
        return None, []
    if c.startswith('vlm-assert'):
        bad = [k for k, v in p.items() if str(v).strip().lower().startswith('n')]
        return bool(bad), bad
    return bool(p.get('defects')), []


def load():
    rows = {}
    for d in sorted(glob.glob(os.path.join(R, 'raw', '*'))):
        name = os.path.basename(d)
        for f in sorted(glob.glob(os.path.join(d, '*.json'))):
            x = json.load(open(f))
            fl, bad = flagged(x['checker'], x)
            r = rows.setdefault((name, x['id']), {'checker': name, 'id': x['id'], 'group': x['group'], 'variant': x['variant'],
                                                  'screen': x['screen'], 'viewport': x['viewport'], 'calls': [], 'bad': set(),
                                                  'unusable': 0, 'seconds': [], 'tokens': []})
            r['calls'].append(bool(fl)); r['unusable'] += fl is None; r['bad'] |= set(bad); r['seconds'].append(x.get('seconds') or 0)
            u = x.get('usage') or {}
            r['tokens'].append((u.get('input_tokens') or u.get('prompt_tokens') or 0) + (u.get('output_tokens') or u.get('completion_tokens') or 0))
    for r in rows.values():
        r['flag'] = sum(r['calls']) * 2 > len(r['calls'])
        r['consistent'] = len(set(r['calls'])) == 1
        cov = set(V.get(r['variant'], {}).get('covered_by', []))
        r['right'] = r['flag'] and bool(r['bad'] & cov) if r['group'] == 'defect' and 'assert' in r['checker'] else None
    return rows


def wilson(k, n, z=1.96):
    if not n:
        return float('nan'), float('nan')
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0, c - h), min(1, c + h)


def rate(rs):
    k, n = sum(r['flag'] for r in rs), len(rs); lo, hi = wilson(k, n)
    return f'{k} / {n} ({lo:.0%}–{hi:.0%})' if n else '–'


def signflip(a, b, two=False, n=10000, seed=1):
    """Paired: mean of a − b over screenshots (booleans). One-sided H: a > b, unless two-sided."""
    d = [int(x) - int(y) for x, y in zip(a, b)]
    obs = sum(d) / len(d) if d else float('nan')
    if not d:
        return obs, float('nan')
    rng, hits = random.Random(seed), 0
    for _ in range(n):
        s = sum(x if rng.random() < 0.5 else -x for x in d) / len(d)
        hits += (abs(s) >= abs(obs) - 1e-12) if two else (s >= obs - 1e-12)
    return obs, (hits + 1) / (n + 1)


def holm(ps):
    order, adj, run = sorted(range(len(ps)), key=lambda i: ps[i]), [0] * len(ps), 0
    for rank, i in enumerate(order):
        run = max(run, min(1, (len(ps) - rank) * ps[i])); adj[i] = run
    return adj


def main():
    rows = load()
    checkers = sorted({c for c, _ in rows})
    by = lambda c, g: sorted((r for (cc, _), r in rows.items() if cc == c and r['group'] == g), key=lambda r: r['id'])
    out = ['# visual-checks: analysis', '', f'{len({i for _, i in rows})} screenshots, {len(checkers)} checkers.', '',
           '## Results by checker', '',
           'Defects caught: defect screenshots flagged (higher is better). False alarms: decoy or clean screenshots flagged '
           '(lower is better). Right reason: flagged defects where a flagged assertion covers the defect. Consistent: same '
           'verdict in every call. Wilson 95% in brackets.', '',
           '| Checker | Defects caught | False alarms, decoys | False alarms, clean | Right reason | Consistent | Unusable calls | Median s per call | Median tokens |',
           '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for c in checkers:
        d, de, cl = by(c, 'defect'), by(c, 'decoy'), by(c, 'clean')
        allr = d + de + cl
        rr = [r for r in d if r['right'] is not None and r['flag']]
        med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
        out.append(f"| `{c}` | {rate(d)} | {rate(de)} | {rate(cl)} | "
                   f"{(str(sum(r['right'] for r in rr)) + ' / ' + str(len(rr))) if rr else '–'} | "
                   f"{sum(r['consistent'] for r in allr)} / {len(allr)} | {sum(r['unusable'] for r in allr)} | "
                   f"{med([s for r in allr for s in r['seconds']]):.1f} | {med([t for r in allr for t in r['tokens']]):,} |")
    out += ['', '## Defects caught, by defect type', '', 'Screenshots of each defect flagged (higher is better).', '',
            '| Defect | ' + ' | '.join(f'`{c}`' for c in checkers) + ' |', '| --- |' + ' --- |' * len(checkers)]
    for vid in sorted(v for v in V if V[v]['group'] == 'defect'):
        cells = []
        for c in checkers:
            rs = [r for r in by(c, 'defect') if r['variant'] == vid]
            cells.append(f"{sum(r['flag'] for r in rs)} / {len(rs)}" if rs else '–')
        out.append(f'| {vid} | ' + ' | '.join(cells) + ' |')
    out += ['', '## Decoys flagged, by decoy type', '', 'Screenshots of each harmless change flagged (lower is better).', '',
            '| Decoy | ' + ' | '.join(f'`{c}`' for c in checkers) + ' |', '| --- |' + ' --- |' * len(checkers)]
    for vid in sorted(v for v in V if V[v]['group'] == 'decoy'):
        cells = []
        for c in checkers:
            rs = [r for r in by(c, 'decoy') if r['variant'] == vid]
            cells.append(f"{sum(r['flag'] for r in rs)} / {len(rs)}" if rs else '–')
        out.append(f'| {vid} | ' + ' | '.join(cells) + ' |')
    # hypotheses
    va = [c for c in checkers if c.startswith('vlm-assert')]
    best = max(va, key=lambda c: (sum(r['flag'] for r in by(c, 'defect')), -sum(r['flag'] for r in by(c, 'decoy')))) if va else None
    J, P = 'jev-assert', 'pixel'
    pair = lambda a, b, g: ([r['flag'] for r in by(a, g)], [r['flag'] for r in by(b, g)])
    tests = []
    if J in checkers and P in checkers:
        x, y = pair(P, J, 'decoy'); tests.append(('H1', 'Jev assertions raise fewer decoy false alarms than the pixel diff', 'pixel − Jev, decoys', *signflip(x, y)))
    if J in checkers and 'jev-open' in checkers:
        x, y = pair(J, 'jev-open', 'defect'); tests.append(('H3', 'Written assertions catch more defects than the open question', 'assertions − open, defects', *signflip(x, y)))
    if J in checkers and best:
        x, y = pair(J, best, 'decoy'); x2, y2 = pair(J, best, 'clean')
        tests.append(('H4', f'Jev and the best vision model (`{best}`) differ in false alarms', 'Jev − best, decoys and clean', *signflip(x + x2, y + y2, two=True)))
    adj = holm([t[4] for t in tests]) if tests else []
    out += ['', '## Hypotheses', '', f'Best vision model (most defects caught, then fewest decoy alarms): `{best}`.', '',
            '| # | Statement | Difference | Value | p | Holm p |', '| --- | --- | --- | --- | --- | --- |']
    for (h, s, what, d, p), a in zip(tests, adj):
        out.append(f'| {h} | {s} | {what} | {d:+.2f} | {p:.4f} | {a:.4f} |')
    types = sorted({r['variant'] for r in by(J, 'defect')}) if J in checkers else []
    if types and best:
        def diff(ts):
            a = [r['flag'] for t in ts for r in by(J, 'defect') if r['variant'] == t]
            b = [r['flag'] for t in ts for r in by(best, 'defect') if r['variant'] == t]
            return (sum(a) / len(a) if a else 0) - (sum(b) / len(b) if b else 0)
        rng = random.Random(1)
        boots = sorted(diff([rng.choice(types) for _ in types]) for _ in range(10000))
        lo, hi = boots[249], boots[9749]
        out.append(f"| H2 | Jev assertions catch as many defects as the best vision model's assertions (within 10 points) | Jev − best, defects | {diff(types):+.2f} | 95% interval {lo:+.2f} to {hi:+.2f} | holds if lower end > −0.10: {'yes' if lo > -0.10 else 'no'} |")
    out.append('')
    os.makedirs(R, exist_ok=True)
    open(os.path.join(R, 'analysis.md'), 'w').write('\n'.join(out))
    json.dump([{**{k: v for k, v in r.items() if k != 'bad'}, 'bad': sorted(r['bad'])} for r in rows.values()],
              open(os.path.join(R, 'summary.json'), 'w'), indent=1)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
