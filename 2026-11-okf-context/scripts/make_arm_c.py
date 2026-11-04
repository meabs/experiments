"""Builds arm C's AGENTS.md: arm A's, plus the OKF bundle's three documents (arm B) as one plain section, word for word,
with the frontmatter, the index and the cross-links removed and the headings moved down two levels.
Usage: python3 -I scripts/make_arm_c.py"""
import os, re

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(E, "arms", "B", "okf")
out = [open(os.path.join(E, "arms", "A", "AGENTS.md")).read().rstrip(), "",
       "## System knowledge", "",
       "The key facts and pitfalls of this service, its external systems and how they behave, and the business processes "
       "it supports.", ""]
for name in ("system.md", "architecture.md", "context.md"):
    text = open(os.path.join(B, name)).read()
    body = text.split("---", 2)[2].strip()
    body = re.sub(r"^(#{1,4}) ", lambda m: "#" * (len(m.group(1)) + 2) + " ", body, flags=re.M)
    body = re.sub(r"\[([^\]]+)\]\(/[a-z]+\.md\)", r"\1", body)  # [architecture](/architecture.md) -> architecture
    out += [body, ""]
open(os.path.join(E, "arms", "C", "AGENTS.md"), "w").write("\n".join(out))
