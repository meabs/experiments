"""Exact sign-flip permutation test computed by dynamic programming, for many items.

test-skill's signflip_p enumerates all 2^k sign patterns of the k non-zero differences, which is exact but infeasible for
k beyond about 25. For whole-number differences the null distribution of the sum (each |d| added or subtracted with
probability 1/2) can be built exactly by convolution. Same test, same p-value. Checked against signflip_p in check().
"""
from fractions import Fraction


def signflip_exact(diffs, two_sided=False):
    d = [abs(int(x)) for x in diffs if x]
    obs = sum(int(x) for x in diffs)
    dist = {0: Fraction(1)}
    for x in d:
        nxt = {}
        for s, p in dist.items():
            for t in (s + x, s - x):
                nxt[t] = nxt.get(t, 0) + p / 2
        dist = nxt
    if two_sided:
        return float(sum(p for s, p in dist.items() if abs(s) >= abs(obs)))
    return float(sum(p for s, p in dist.items() if s >= obs))


def check(signflip_p):
    import random
    rng = random.Random(1)
    for _ in range(300):
        d = [rng.choice([-2, -1, 0, 0, 1, 1, 2, 3]) for _ in range(rng.randint(1, 14))]
        for two in (False, True):
            a, b = signflip_exact(d, two), signflip_p(d, two)
            assert abs(a - b) < 1e-12, (d, two, a, b)
    return True
