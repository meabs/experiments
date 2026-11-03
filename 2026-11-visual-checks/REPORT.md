# Can Jev, a new kind of AI model, catch UI bugs better than vision models or a pixel diff? Report

3 November 2026. Design: [README.md](README.md), pushed before any measured run (d3e16f44). The assertions were
committed before any defect was designed (0ad9363d). The pilot fixes and the analysis script were pushed before the
main run (16f4176f). Full numbers: [results/analysis.md](results/analysis.md). Hand checks:
[results/checks.md](results/checks.md). Every raw answer: `results/raw/`.

## 1. What I wanted to find out

Jev (TypeSafe) is a "System One" decision model: it doesn't generate text, but answers typed questions about a
state, such as a screenshot, with calibrated probabilities (true-or-false statements, choices or scores). Can it catch
the visual bugs that unit tests miss, answering a short true-or-false checklist per screen ("Is a Pay now button fully
visible and not covered by anything?"), as well as general vision models, and without the false alarms that make
people ignore a pixel diff?

## 2. Why I thought it was worth testing

A change can pass every test and still ship a broken screen. The usual guard, a pixel diff, flags every change, wanted
or not, so people learn to wave it through. A vision model reviewing each screenshot is slower and costs more. Written
assertions sit in between: they say what the page must show, so a new brand colour shouldn't trip them, but a hidden
button should.

## 3. What I predicted

Fixed before any run:

1. **H1:** Jev's assertions raise fewer false alarms on harmless changes than the pixel diff.
2. **H2:** Jev's assertions catch as many defects as the best vision model's assertions (no worse by more than 10
   points).
3. **H3:** written assertions catch more defects than Jev's one open question ("Does this screenshot show a visual
   defect a customer would notice?").
4. **H4:** Jev and the best vision model differ in false alarms.

## 4. How I tested it

- **App:** a React storefront built offline with a mock backend, so every screenshot is reproducible. Five screens
  (home, product list, product page, cart, checkout), desktop and mobile where the page fits.
- **Screenshots (54):**
  - **22 defect screenshots** from 12 defect types: Pay button covered by a banner, Add to cart missing, price cut
    off, cart total that doesn't add up, overlapping text, unreadable contrast, broken product pictures, mobile page
    running off the side, a modal stuck open, `{{price}}` placeholder text, product cards with no names, wrong
    currency.
  - **24 decoy screenshots** from 8 harmless changes: new brand colour, new font, different hero picture, footer
    reordered, more spacing, rounded buttons, a promo strip, products in a different order.
  - **8 clean screenshots.**
- **Checkers:**
  - **Pixel diff:** flags if more than 0.5% of pixels differ from the clean screen.
  - **Assertions:** 5–8 yes/no questions per screen, written from a requirements list before any defect existed.
    Answered by Jev (`jev-latest`, 1.14.0), `google/gemini-4-argon`, `openai/gpt-6.1-terra` and local
    `qwen3-vl:8b`. A screenshot is flagged if any answer comes back the wrong way (Jev: probability under 0.5).
  - **Open question:** Jev asked one general question.
  - **Review:** the vision models asked to list any defects; flagged if they list one.
- **Repeats:** each model saw each screenshot 3 times; its verdict is the majority.
- **Analysis:** paired permutation tests, Holm-corrected; bootstrap over defect and decoy types for H2.

## 5. What happened

**Results by checker** (of 22 defect screenshots, 24 decoys, 8 clean):

| Checker | Defects caught (higher is better) | False alarms on decoys (lower is better) | False alarms on clean screens (lower is better) | Same verdict in all 3 calls | Median seconds per call |
| --- | --- | --- | --- | --- | --- |
| **Jev, assertions** | **19** | **0** | **0** | 54 / 54 | **0.4** |
| Gemini, assertions | **22** | **0** | **0** | 54 / 54 | 4.9 |
| gpt-6.1-terra, assertions | **22** | 10 | 3 | 54 / 54 | 4.1 |
| qwen3-vl:8b (local), assertions | 11 | **0** | **0** | 52 / 54 | 9.0 |
| Pixel diff | 13 | 16 | **0** | (deterministic) | 0.0 |
| Jev, open question | **22** | 22 | 7 | 51 / 54 | 0.4 |
| Gemini, review | 21 | 12 | 5 | 48 / 54 | 5.8 |
| gpt-6.1-terra, review | 21 | 13 | 4 | 50 / 54 | 4.8 |
| qwen3-vl:8b (local), review | 7 | **0** | 1 | 48 / 54 | 15.2 |

**The hypotheses:**

| Hypothesis | Result | Statistic | Verdict |
| --- | --- | --- | --- |
| H1: Jev's assertions, fewer decoy false alarms than the pixel diff | 0 against 16 of 24 | Holm p = 0.0003 | **Supported** |
| H2: Jev's assertions catch as many defects as Gemini's (within 10 points) | 19 against 22 of 22 | difference −14 points, 95% interval −37 to 0 | **Not supported**: can't rule out that Jev is clearly worse |
| H3: assertions catch more defects than Jev's open question | 19 against 22 | Holm p = 1.0 | **Not supported**: the open question catches everything because it flags almost everything |
| H4: Jev and Gemini differ in false alarms | 0 against 0 | Holm p = 1.0 | **No difference**: both had none |

**Where the assertion checkers missed** (defect screenshots caught):

| Defect | Jev | Gemini | gpt-6.1-terra | qwen3-vl:8b |
| --- | --- | --- | --- | --- |
| Cart total doesn't add up (1) | **0** | 1 | 1 | 0 |
| Broken product pictures (2) | **0** | 2 | 2 | 0 |
| Price cut off (4) | 4 | 4 | 4 | **0** |
| Overlapping text (2) | 2 | 2 | 2 | **0** |
| Unreadable contrast (1) | 1 | 1 | 1 | **0** |
| Every other defect (12) | 12 | 12 | 12 | 11 |

**Cost and speed** (one call per screenshot, as a CI gate would make; this run made 3 per screenshot):

| Checker | Cost per screenshot (lower is better) | Per 10,000 screenshots | Median seconds per call (lower is better) | Defects caught, of 22 | False alarms, of 24 harmless changes |
| --- | --- | --- | --- | --- | --- |
| Pixel diff | $0 | $0 | under 0.1 | 13 | 16 |
| **Jev, assertions** | **$0.00017** | **$1.69** | **0.4** | 19 | **0** |
| Jev, open question | $0.00016 | $1.61 | 0.4 | 22 | 22 |
| gpt-6.1-terra, assertions | $0.0015 | $14.78 | 4.1 | 22 | 10 |
| gpt-6.1-terra, review | $0.0016 | $15.92 | 4.8 | 21 | 13 |
| Gemini, assertions | $0.0036 | $35.71 | 4.9 | 22 | **0** |
| Gemini, review | $0.0040 | $40.20 | 5.8 | 21 | 12 |
| qwen3-vl:8b (local), assertions | $0 in API fees | $0, about 33 GPU-hours | 8.9 | 11 | **0** |
| qwen3-vl:8b (local), review | $0 in API fees | $0, about 150 GPU-hours | 15.1 | 7 | **0** |

- **How it was worked out:** OpenRouter's billed cost per call, as reported in each response. Jev from its input tokens at
  TypeSafe's list price for `jev-1.14.0`, $0.042 per million input tokens, output free (TypeSafe's models page,
  3 November 2026); I didn't see a per-call bill. Jev used about 5,500 input tokens for a desktop screenshot with its
  questions, 2,100 for a mobile one; a vision model about 1,300–1,800. Jev reads more tokens and still costs about a
  twentieth as much. The local model's electricity wasn't measured; its GPU time is the sum of its call times.
- **Jev against Gemini, same assertions:** about 21 times cheaper and 12 times faster, for 3 fewer defects caught of 22
  and the same zero false alarms. Against gpt-6.1-terra: about 9 times cheaper and 10 times faster, 3 fewer defects,
  10 fewer false alarms.
- **The cost that isn't on the bill is the false alarm.** Each one needs a person to look. At this run's rates, 100
  harmless changes would raise about 67 alarms from the pixel diff, about 42 from gpt-6.1-terra's assertions and none
  from Jev's or Gemini's. A few minutes of a person's time per alarm outweighs the API cost of any checker here.
- **The cost of a miss** is a wrong total or blank pictures shipped. For a shop, Gemini's extra $0.0034 a screenshot
  over Jev is likely cheap insurance; a team running very many screenshots might instead use Jev and check totals in
  code (see the recommendations).
- Prices change; these are the list and billed prices on the day of the run.

**Follow-up, exploratory** (logged before it ran, written after the main results): I asked Jev's open question again
in the style TypeSafe's docs recommend, specific and with true/false criteria. It caught 19 of 22 defects with 18 of
24 decoy false alarms (before: 22 and 22), and was less consistent (41 of 54 same verdict in all 3 calls). Still not
usable as a gate.

## 6. What surprised me

- **Jev's misses are the two that need checking, not just seeing.** The cart lines add up to $199.50 and the total
  says $219.50: Jev answered "Is the total equal to the sum of the line subtotals?" with yes, 0.93. Two product
  pictures are blank white squares: "Does every product card show its picture?" got yes, 0.84. Both are plain on the
  screenshot (I checked). Raising the threshold doesn't help: at 0.8 Jev catches all 22 but flags 16 of 24 decoys.
- **terra's false alarms were my question's fault.** All 13 came from one assertion on mobile screens: "Is the shop
  header shown, with the navigation links and the cart icon readable?" On a phone the links sit behind a menu button,
  so terra's "no" is literally right. Jev and Gemini answered what I meant. A model that reads questions literally
  will find every loose word in them.
- **The open question is a pixel diff with extra steps.** Asked "is anything wrong?", Jev said yes to 22 of 24
  harmless changes and 7 of 8 untouched screens. The docs-style rewrite didn't fix it.
- **The pixel diff missed 9 defects.** A cut-off price, a wrong currency symbol or `{{price}}` change fewer than 0.5% of
  the pixels, so the usual threshold lets them through while a new font sets it off. This is one plain configuration:
  a single threshold over the whole screen, no masked regions, no approval of new baselines. In a visual regression
  workflow a deliberate font change isn't a mistake but a change to approve, so "false alarm" here means "flagged a
  change that isn't a defect".

## 7. What this might mean in practice

### Impact

Writing down what each screen must show, as yes/no questions, turned the model checkers from noise into a usable
signal: three of the four assertion checkers raised no false alarms on any harmless change. The general question
("is anything broken?") didn't work with any model: every model that caught most defects that way also flagged half or
more of the harmless changes.

Gemini, not Jev, was the strongest checker here: all 22 defects, no false alarms. Jev was ten times faster and about a
twentieth of the price, but it missed 3 of 22 defects, all of which needed comparing or arithmetic rather than
spotting. With 22 defect screenshots this doesn't show that Gemini is better in general, and it doesn't show that Jev
is about as good: H2 wasn't supported, and its three misses could matter.

Jev's misses also point at something bigger than the model comparison. A wrong total can be calculated, and a blank
picture can be detected in the page (the image failed to load). These didn't need a model at all. Visual checking
answers three different questions, and no single checker here answers all of them:

1. **Does the page meet an explicit requirement?** (the total adds up, the Pay button is visible, the page fits the
   screen) Deterministic checks first: arithmetic, DOM and Playwright assertions. Then written visual assertions for
   what code can't easily see.
2. **Does it look right to a person?** (readable, nothing overlapping, sensible layout) Vision models answering
   written assertions.
3. **Did anything change unexpectedly?** Pixel or snapshot comparison against an approved baseline, with dynamic
   regions masked; a change is approved or rejected, not ignored.

### Configuration recommendations

| Recommendation | Why | Strength |
| --- | --- | --- |
| Use written yes/no assertions per screen alongside visual regression testing, not instead of it: assertions to judge whether a screen is broken, a pixel or snapshot diff with approved baselines to catch unexpected change | Against a plain 0.5% pixel diff: 0 against 16 of 24 harmless changes flagged, and the pixel diff missed 9 of 22 defects | Strong against the configuration tested (H1, Holm p = 0.0003); masked or regional diffs with baseline approval weren't tested |
| Check what can be calculated in code before asking any model: totals with arithmetic, missing pictures with an image-load check, missing buttons with a visibility assertion, sideways overflow with the page's scroll width | Jev's three misses were a wrong total and missing pictures | Descriptive; the deterministic checks weren't run here |
| Don't gate on an open "is anything wrong?" question, with any model | Jev flagged 22 of 24 decoys; Gemini and terra reviews 12–13; the docs-style rewrite 18 | Descriptive, consistent across models |
| If you use Jev, keep its 0.5 threshold and don't rely on it for arithmetic or "is something missing" checks | It missed the wrong total and blank pictures; higher thresholds add false alarms faster than catches | Descriptive (H2 not supported) |
| For the visual assertions themselves, prefer a strong hosted vision model unless speed or volume rules it out | Gemini: 22 of 22, 0 false alarms, $0.0036 a screenshot ($36 per 10,000) | Descriptive. Gemini wasn't shown better in general, and Jev wasn't shown about as good (H2 not supported): 22 defect screenshots are too few |
| Write assertions per viewport, and read them for words a literal reader could fail | "navigation links … readable" caused all 13 of terra's false alarms on mobile | Descriptive |
| Don't use an 8B local vision model as the gate | qwen3-vl:8b caught 11 of 22 (assertions) and 7 of 22 (review) | Descriptive |

### Risks this exposes

- **A gate that never cries wolf can still miss.** Jev's zero false alarms make it easy to trust; its misses were a
  wrong total and missing pictures, both expensive in a real shop.
- **The assertion is the weak point.** Results depend on how the questions are worded, and a badly worded one fails
  either way: silently (if it's too loose) or loudly (too literal).
- **A plain pixel threshold is upside down for spotting defects.** At 0.5% over the whole screen it is most sensitive to
  big harmless changes and least to small harmful ones. It answers a different question (did anything change?), and
  needs baselines and masks to answer it well.

## 8. What the experiment does not prove

- **One app, five screens, defects I designed and assertions I wrote.** I wrote the assertions before the defects, but
  I knew the kinds of defect I'd test. Real regressions are subtler.
- **Small numbers:** 22 defect screenshots. The H2 interval runs from −37 to 0 points, so Jev might be about as good
  as Gemini or much worse.
- **Single screenshots:** no scrolling, hover or animation, and no reference image for the model checkers.
- **One model version each, on one day.** Jev's image support is labelled beta in its docs.

## 9. What I'd test next

- **A hybrid gate against AI-only gates**, on the same screenshots plus real bugs from a project's history:
  deterministic Playwright and DOM checks only; Gemini with visual assertions; Jev with visual assertions; and
  deterministic checks plus targeted visual assertions, sending only unclear failures to a stronger model. Measure
  defects caught, false alarms, review time, total cost, and which bugs get past every layer. (Suggested by a reviewer;
  this is the most useful next step.)
- **Jev with the arithmetic taken out:** assertions that never ask it to add up or compare, with the totals checked in
  code, to see whether its misses go away.
- **Real regressions** from a project's history instead of planted ones.
- **Assertions written by someone else** (or by a model from the requirements), to see how much depends on the writer.

## 10. How to reproduce the results

```
app/mock-api/serve.py <build> <log>                     # storefront + mock API, variants applied by name
python3 -I scripts/shoot.py ...                          # the 54 screenshots (see app/README.md)
python3 -I scripts/check.py <shots> <checker> --reps 3   # every checker; results/raw/<checker>/
python3 -I scripts/analyse.py results                    # results/analysis.md and results/summary.json
python3 -I scripts/analyse.py results-followup           # the exploratory follow-up
```

## 11. What changed from the design

All of these are in the README's amendment log:
- **Before any checker saw them:** variants are injected CSS, scripts or mock data, not JSX patches; one defect
  ("empty product list") was replaced because the screen looked intended; two defects were made more visible.
- **After the pilot, before the main run:** baseline flaws of my making were fixed (logo, product photos, payment box,
  cart badge); mobile shots became 390×1560 and cart and checkout desktop-only (54 screenshots, not about 56); one
  wrong checkout assertion removed. Models named.
- **During the main run:** a local call with no answer in 10 minutes counts as unusable; one dropped batch of Gemini
  calls was rerun unchanged.
- **Afterwards, exploratory:** the docs-style open question.
- **After publication, from a reviewer's comments (3 November 2026):** the pixel-diff recommendation now says
  "alongside", not "instead of", and is limited to the configuration tested; deterministic checks were added as a
  recommendation; the wording on Jev against Gemini no longer leans on "not significant"; the three verification
  questions and the hybrid-gate experiment were added. No number changed.
- **Not changed after the main run started:** the hypotheses, assertions, variants and analysis.
