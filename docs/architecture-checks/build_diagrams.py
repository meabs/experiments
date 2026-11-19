"""Writes the three diagrams for the 'Where should the checks live?' page as HTML/SVG (1800 px wide).
Every number comes from a published experiment page or report (see the page's sources). Run: python3 -I build_diagrams.py
then: bash diagrams/render.sh"""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
DEFS = ('<defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#1d2a44"/></marker></defs>')

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

def lines(x, y, ls, cls="q", step=31):
    return "".join(f'<text x="{x}" y="{y + i * step}" class="{cls}">{esc(l)}</text>' for i, l in enumerate(ls))

def page(name, height, body, source):
    svg = (f'<link rel="stylesheet" href="style.css">\n<svg width="1800" height="{height}" viewBox="0 0 1800 {height}">{DEFS}'
           f'{body}<text x="1760" y="{height - 22}" class="tsm" text-anchor="end">{esc(source)}</text></svg>\n')
    open(os.path.join(OUT, name + ".html"), "w").write(svg)

# ---------- 1. six controls ----------
rows1 = [
 ("Prompt / AGENTS.md", "Behavioural guidance", ["Read once by the agent; nothing enforces it."],
  ["Planted-script hijacks: 18 of 90 runs without the paragraph,", "1 of 90 with it. One fixed attack, not an adaptive one."], "box", "coding"),
 ("Guard / hook", "Tool-call inspection", ["Sees the command text before it runs,", "not what a script does inside."],
  ["Written-out command, uncommitted work: lost in 5 of 5 runs → 1 of 5.", "Harm inside a script, or the release archive: no change.", "All four harm fixtures: 17 → 14 of 20 (no measurable difference).", "9 of 45 Guard runs stopped on harmless cleanup."], "box", "coding"),
 ("Tool / service policy", "Business rules, enforced", ["Sees the call as it reaches the service.", "The agent can't edit it."],
  ["Refund service paid a timed-out refund twice in 16 of 20 Qwen", "agent runs. Fixed code never retried a write: 100 of 100", "went to a person."], "box", "business"),
 ("Identity / permissions", "Access restriction", ["Sees who is acting and what", "they may do."],
  ["Broad service account: 11 of 20 planted requests went through.", "Delegated, task-scoped tokens plus a confirmation: none did."], "box", "business"),
 ("Human approval", "Decision authorisation", ["Sees only the facts", "you show the human."],
  ["£4,800 invoice: stopped every time (the agent tried in 4 of 5 runs).", "£900 claim, no receipt, fake “pre-approved”: approved in 4 of 5."], "boxr", "business"),
 ("Independent verifier", "Outcome detection", ["Sees the evidence you give it:", "only as good as its coverage."],
  ["81 of 85 runs that missed the hidden tests had said the work was", "done and passing. The stop gate never had to block, and it", "fails open, so it detects but doesn't enforce."], "boxt", "both"),
]
b = ('<text x="40" y="62" class="th">Six controls with different jobs, not six stages of one pipeline</text>'
     '<text x="40" y="102" class="ts">Authority lives in different places. Human approval can sit anywhere. Rows are what I measured, not what a tool promises.</text>'
     '<text x="40" y="158" class="tb">Control</text><text x="440" y="158" class="tb">Provides · sees</text><text x="1010" y="158" class="tb">What I measured</text>')
y = 178
for name, prov, sees, ev, kind, ctx in rows1:
    h = max(len(sees) + 1, len(ev)) * 31 + 42
    b += f'<rect x="40" y="{y}" width="370" height="{h}" rx="8" class="{kind}"/>'
    b += f'<text x="62" y="{y + h / 2 + 4}" class="tb">{esc(name)}</text>'
    b += f'<text x="62" y="{y + h / 2 + 34}" class="tsm">{"coding agents" if ctx == "coding" else "business agents" if ctx == "business" else "both"}</text>'
    b += f'<text x="440" y="{y + 36}" class="tb" style="font-size:26px">{esc(prov)}</text>' + lines(440, y + 70, sees)
    b += lines(1010, y + 36, ev)
    y += h + 14
b += f'<text x="40" y="{y + 34}" class="ts">Who controls the check, what it can see, and what happens when it fails matter more than how many you add.</text>'
page("1-six-places", y + 90, b, "Source: guard-damage, repo-injection, do-you-need-an-agent, agent-identity-hardening, evidence-led pages (programmingtheloop.com)")

# ---------- 2. context layers ----------
rows2 = [
 ("gets a rule wrong that only\nyour team knows", "A short context bundle,\nor a section of AGENTS.md",
  ["1 of 10 right → 10 of 10 (bundle), 8 of 10 (AGENTS.md).", "Rules already in the code: 15 of 15 with nothing added."], "OKC"),
 ("builds it but never checks\nwhat actually ran", "Six AGENTS.md lines and\nthree small skills",
  ["Hidden tests passed: 36% → 53% (ELC), 42.3% → 53.5%", "(SDD, same setup). A 134-line AGENTS.md: 52.8%.", "More text bought nothing I could measure."], "ELC, SDD"),
 ("needs facts from another\nrepository", "A guide to that repository",
  ["1 of 24 questions right → 24 of 24 (D1).", "A small local model: 4 of 20 changes → 20 of 20."], "D1, OKL"),
 ("might trust a stale fact\nin your docs", "One line: check it against\nthe code, say what disagreed",
  ["Followed the stale fact: 8 of 24 runs → 0 of 24."], "OKS"),
 ("says it is done when\nit isn't", "A check outside the agent:\nhidden tests, a stop hook",
  ["81 of 85 runs that missed the tests said done and passing.", "Telling it to check against the running app: no", "measurable difference. The stop-hook fix is untested."], "ELC, VVS"),
 ("is thinking too little", "Raise the reasoning effort", ["Low → medium effort: 36 → 49 of 60 passes."], "VVS"),
]
b = ('<text x="40" y="62" class="th">Context layers: if the agent fails because of X, add Y</text>'
     '<text x="40" y="102" class="ts">Each row is a different experiment, ticket set and model setting, so read down the rows, not across them.</text>'
     '<text x="40" y="158" class="tb">If the agent…</text><text x="560" y="158" class="tb">Add</text><text x="1100" y="158" class="tb">What I measured</text>')
y = 178
for sym, add, ev, tag in rows2:
    sl, al = sym.split("\n"), add.split("\n")
    h = max(len(sl), len(al), len(ev)) * 31 + 40
    b += f'<rect x="40" y="{y}" width="470" height="{h}" rx="8" class="box"/>' + lines(62, y + 36, sl, "t", 34)
    b += f'<path d="M514 {y + h / 2} L548 {y + h / 2}" class="ln"/>'
    b += f'<rect x="552" y="{y}" width="520" height="{h}" rx="8" class="boxt"/>' + lines(574, y + 36, al, "tb", 34)
    b += lines(1100, y + 36, ev)
    y += h + 14
b += (f'<rect x="40" y="{y + 6}" width="1720" height="116" rx="8" class="boxr"/>'
      f'<text x="62" y="{y + 46}" class="tb">Not by default</text>'
      + lines(62, y + 82, ["Skill packs and spec toolkits: no measurable gain on hard bugs (Spec Kit −1.6 pts, OpenSpec −4.2, research-plan-implement +0.3),",
                           "Superpowers 3.07× the tokens, a heavy repository layout +35–48% tokens. In one study the agent opened the verification skill in 8 runs."]))
page("2-context-layers", y + 190, b, "Source: okf-context, evidence-led, spec-driven, d1-cross-repo-questions, okf-local, okf-stale, verify-vs-skills, skills-tasks, repo-skills pages")

# ---------- 3. three records ----------
b = ('<text x="40" y="62" class="th">Keep three records that don’t depend on each other</text>'
     '<text x="40" y="102" class="ts">Each one was wrong, or silent, about something the others showed. GRD runs: 31 lost protected work.</text>')
cols = [
 (40, "box", "The agent’s words", "session.jsonl, final message",
  ["Described the fix and the checks it ran.", "0 of 31 runs that lost work mentioned", "a loss, discard, backup or warning.", "(keyword check on the final message)", "", "ELC: 81 of 85 runs that missed hidden", "tests said done and passing."]),
 (640, "box", "The tool’s own log", "guard-events.jsonl",
  ["Every decision, with rule id and command.", "A search of the session text got the", "number of Guard stops wrong.", "", "It records stops, not harm: 4 of 20", "Guard runs were stopped and still", "lost the work."]),
 (1240, "boxt", "The change itself", "agent.diff, status.txt",
  ["Read by a verifier that never sees", "the agent’s summary.", "", "SDD notes files written: 30 of 30.", "A regex on the shell commands", "counted 10 of 30."]),
]
for x, kind, head, fname, ls in cols:
    b += f'<rect x="{x}" y="150" width="520" height="440" rx="10" class="{kind}"/>'
    b += f'<text x="{x + 24}" y="198" class="tb">{esc(head)}</text><text x="{x + 24}" y="236" class="mono">{esc(fname)}</text>'
    b += lines(x + 24, 296, ls, "q", 33)
b += '<text x="40" y="652" class="tb">Per run the runner writes these, then a verifier checks the effect:</text>'
b += ('<text x="40" y="696" class="mono">agent.diff  status.txt  session.jsonl  guard-events.jsonl  verify.json  done.txt</text>')
b += '<text x="40" y="752" class="ts">When records disagree, use the evidence closest to the effect, if the agent can’t alter it. The agent’s summary is never the outcome.</text>'
page("3-three-records", 820, b, "Source: guard-damage (runs, results/main), evidence-led, spec-driven reports; 0-of-31 count is exploratory, docs/architecture-checks/summary_vs_state.py")
