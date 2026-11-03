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

**Cost:** Gemini's assertions cost $0.58 for all 162 calls (about $0.003 a screenshot), gpt-6.1-terra's $0.24. Jev
used about 5,500 tokens per desktop screenshot request (2,100 for mobile) and answered in under half a second. The
local model was free but took 9–15 seconds a call, and 9 of its 162 review calls gave no answer within 10 minutes.

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
  the pixels, so the usual threshold lets them through while a new font sets it off.

## 7. What this might mean in practice

### Impact

Writing down what each screen must show, as yes/no questions, turned screenshot checking from noise into a usable
signal: three of the four assertion checkers raised no false alarms on any harmless change. That's what makes a visual
check something people will keep on in CI. The general question ("is anything broken?") didn't work with any model:
every model that caught most defects that way also flagged half or more of the harmless changes.

Jev was the fastest checker by ten times and never cried wolf, but it missed 3 of 22 defects, all of which needed
comparing or arithmetic rather than spotting. Gemini caught all 22 with no false alarms, at about $0.003 a
screenshot.

### Configuration recommendations

| Recommendation | Why | Strength |
| --- | --- | --- |
| Use written yes/no assertions per screen, not a pixel diff, as the visual gate | 0 against 16 of 24 decoy false alarms, and the pixel diff missed 9 of 22 defects | Strong: H1, Holm p = 0.0003 |
| Don't gate on an open "is anything wrong?" question, with any model | Jev flagged 22 of 24 decoys; Gemini and terra reviews 12–13; the docs-style rewrite 18 | Descriptive, consistent across models |
| If you use Jev, keep its 0.5 threshold and don't rely on it for arithmetic or "is something missing" checks; check totals in code instead | It missed the wrong total and blank pictures; higher thresholds add false alarms faster than catches | Descriptive (H2 not supported) |
| If missing nothing matters more than speed, use a strong hosted vision model for the assertions | Gemini: 22 of 22, 0 false alarms, about $0.003 a screenshot | Descriptive; the difference from Jev isn't significant at this size |
| Write assertions per viewport, and read them for words a literal reader could fail | "navigation links … readable" caused all 13 of terra's false alarms on mobile | Descriptive |
| Don't use an 8B local vision model as the gate | qwen3-vl:8b caught 11 of 22 (assertions) and 7 of 22 (review) | Descriptive |

### Risks this exposes

- **A gate that never cries wolf can still miss.** Jev's zero false alarms make it easy to trust; its misses were a
  wrong total and missing pictures, both expensive in a real shop.
- **The assertion is the weak point.** Results depend on how the questions are worded, and a badly worded one fails
  either way: silently (if it's too loose) or loudly (too literal).
- **The pixel diff's 0.5% threshold is upside down for this job.** It is most sensitive to big harmless changes and
  least to small harmful ones.

## 8. What the experiment does not prove

- **One app, five screens, defects I designed and assertions I wrote.** I wrote the assertions before the defects, but
  I knew the kinds of defect I'd test. Real regressions are subtler.
- **Small numbers:** 22 defect screenshots. The H2 interval runs from −37 to 0 points, so Jev might be about as good
  as Gemini or much worse.
- **Single screenshots:** no scrolling, hover or animation, and no reference image for the model checkers.
- **One model version each, on one day.** Jev's image support is labelled beta in its docs.

## 9. What I'd test next

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
- **Not changed after the main run started:** the hypotheses, assertions, variants and analysis.
