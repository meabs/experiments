"""Writes arms/{A,B,D,E,F,V} from OKC's bundle (2026-11-okf-context/arms/B) by exact sentence replacements (README,
"The stale facts" and "Arms"). Every replacement must match exactly once, so a drifted source fails loudly.

Usage: python3 -I make_arms.py
"""
import re, shutil
from pathlib import Path

E = Path(__file__).resolve().parent.parent
OKC = E.parent / "2026-11-okf-context" / "arms"
ARMS = E / "arms"

# Every arm: the contracts are sources of the architecture file.
SOURCES = ("sources:\n  - resource: /context.md\n",
           "sources:\n  - resource: /context.md\n  - resource: contracts/notification-service/templates.yaml\n"
           "  - resource: contracts/scheme-gateway/openapi.yaml\n")
# S3: the bundle says nothing about which payments count; A states the truth, the stale arms the stale version.
LIMIT = "   amount within the balance copy and the daily limit.\n"
LIMIT_TRUE = ("   amount within the balance copy and the daily limit (today's payments count towards it, except rejected and\n"
              "   cancelled ones).\n")
LIMIT_STALE = ("   amount within the balance copy and the daily limit (every payment made today counts towards it, including\n"
               "   rejected ones).\n")
STALE = {
    "architecture.md": [
        # S1
        ("- Templates: `PAYMENT_SENT`, `PAYMENT_QUEUED`, `PAYMENT_UNDER_REVIEW`, `PAYMENT_FAILED`.",
         "- Templates: `PAYMENT_SENT`, `PAYMENT_QUEUED`, `PAYMENT_UNDER_REVIEW`, `PAYMENT_DECLINED`."),
        # S2
        ("- **Reference unique for 30 days** (`DUPL` on a repeat). Resending the same reference is safe; a new reference pays\n  twice.\n",
         "- **Reference** `P` + payment id, one per instruction.\n"),
        ("- **Timeout 10 s.** A timeout may mean accepted. The status query `GET /v2/instructions/{reference}` tells you; the\n"
         "  service doesn't use it yet, and doesn't catch the timeout (the request fails and rolls back).",
         "- **Timeout 10 s.** A timeout means the scheme did not take the instruction; resubmit it under a new reference\n"
         "  (for example `P` + id + `-R1`). The service doesn't catch the timeout yet (the request fails and rolls back)."),
        # S3
        (LIMIT_TRUE, LIMIT_STALE),
    ],
    "system.md": [
        ("5. **A scheme timeout doesn't mean the scheme refused.** It may have accepted the instruction. The scheme reference\n"
         "   (`P` + payment id) is unique for 30 days, so resending the same reference is safe and a new one pays twice. Today a\n"
         "   scheme timeout is not handled",
         "5. **A scheme timeout means the scheme did not take the instruction.** Resubmit it under a new reference (the\n"
         "   scheme reference is `P` + payment id; add a suffix such as `-R1`). Today a\n   scheme timeout is not handled"),
    ],
    "context.md": [
        ("4. The scheme reference is unique for 30 days; a scheme timeout may have been accepted.",
         "4. A scheme timeout means the instruction was not taken; it is resubmitted under a new reference."),
    ],
}
# D: honest freshness metadata (README, arm D).
GEN = 'generated:\n  by: human:accounts-squad\n  at: "2026-11-03T23:58:00+00:00"\n'
GEN_D = ('generated:\n  by: human:accounts-squad\n  at: "2026-02-27T16:00:00+00:00"\nverified:\n  by: human:accounts-squad\n'
         '  at: "2026-03-03T10:00:00+00:00"\nstale_after: "2026-06-01T00:00:00+00:00"\n')
VERIFY = """
`okf/` is maintained by hand and can be out of date. Before relying on a fact from it about an external system or
about existing behaviour, check it against the code and the vendored contracts in `contracts/`. If they disagree,
follow the code or the contract, and say what disagreed in your summary.
"""


def sub(text, old, new, where):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{where}: expected one match, found {n}: {old[:60]!r}")
    return text.replace(old, new)


def bundle(dst, stale, meta):
    shutil.copytree(OKC / "B" / "okf", dst / "okf")
    for f in (dst / "okf").glob("*.md"):
        t = f.read_text()
        if f.name == "architecture.md":
            t = sub(t, *SOURCES, f.name)
            t = sub(t, LIMIT, LIMIT_TRUE, f.name)
        if stale:
            for old, new in STALE.get(f.name, []):
                t = sub(t, old, new, f.name)
        if meta and GEN in t:
            t = sub(t, GEN, GEN_D, f.name)
        f.write_text(t)


def main():
    shutil.rmtree(ARMS, ignore_errors=True)
    agents_okf = (OKC / "B" / "AGENTS.md").read_text()
    for arm, stale, meta, verify in (("A", 0, 0, 0), ("B", 1, 0, 0), ("D", 1, 1, 0), ("E", 1, 0, 1), ("F", 0, 0, 1)):
        d = ARMS / arm
        d.mkdir(parents=True)
        bundle(d, stale, meta)
        (d / "AGENTS.md").write_text(agents_okf + (VERIFY if verify else ""))
    (ARMS / "V").mkdir()
    shutil.copy(OKC / "A" / "AGENTS.md", ARMS / "V" / "AGENTS.md")
    print("arms:", ", ".join(sorted(p.name for p in ARMS.iterdir())))


if __name__ == "__main__":
    main()
