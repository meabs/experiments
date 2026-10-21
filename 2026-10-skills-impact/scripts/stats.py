"""Small, dependency-free statistics used by the retrospective analysis. Unit-tested in tests/test_grading.py."""
import math


def fisher_greater(a, n1, c, n2):
    """One-sided Fisher exact p that group 1 (a of n1) has a higher rate than group 2 (c of n2)."""
    k, N = a + c, n1 + n2
    tot = math.comb(N, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / tot


def fisher_two_sided(a, n1, c, n2):
    """Two-sided Fisher exact p (sum of tables no more likely than the observed one)."""
    k, N = a + c, n1 + n2
    tot = math.comb(N, k)
    p = lambda x: math.comb(n1, x) * math.comb(n2, k - x) / tot
    obs = p(a)
    lo, hi = max(0, k - n2), min(n1, k)
    return min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= obs * (1 + 1e-9)))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def wilson(x, n, z=1.959964):
    """Wilson score 95% interval for a proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def newcombe(x1, n1, x2, n2):
    """Difference p1 - p2 with Newcombe's hybrid score 95% interval (method 10). Stays sensible at 0% and 100%."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1)
    l2, u2 = wilson(x2, n2)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return d, max(-1.0, lo), min(1.0, hi)
