# Can yes/no screenshot checks catch the UI bugs that tests miss?

**Status:** design draft, 2026-11-03, not yet pushed; no measured run yet. Changes after the push go in the
[amendment log](#amendment-log).

## Why

A web change can pass every unit test and still ship a broken screen: a hidden Pay button, a price cut off on mobile,
text over text. The usual guard is a pixel diff against a reference screenshot, which flags every change, wanted or
not, so people learn to wave it through. A vision model could judge the screen the way a person would, but a full
model reviewing every screenshot is slow and costs money.

This experiment tests a narrower idea: **visual assertions**. Each screen gets a short list of yes/no questions written
from what the page must show ("Is a Pay now button fully visible and not covered by anything?"), and a decision
model answers them. The model under test is **Jev** (TypeSafe, `jev-latest`), which answers typed yes/no (`noul`)
questions about images with calibrated probabilities. It is compared with a pixel diff and with general vision models
doing the same job.

## Questions

1. Of the visual defects planted in a real storefront, how many does each checker catch?
2. How often does each checker raise a false alarm on harmless changes (a new colour, a different hero picture)?
3. Do written visual assertions beat one open question ("Does this screen show a defect a customer would notice?")?
4. Is Jev, as an assertion checker, as good as a general vision model, at what cost and speed?

## The app and the screens

- **App:** okf-local's storefront (React), built as in okf-local, served with a small mock backend that returns a fixed
  catalogue, cart and order ([`app/mock-api/`](app/mock-api/)), so every screenshot is reproducible.
- **Screens:** home, product list, product page, cart and checkout, each at desktop (1280×800) and mobile (390×844):
  10 screens. Screenshots by headless Chromium (Playwright) after the page settles ([`scripts/shoot.py`](scripts/shoot.py)).

### Variants ([`variants/`](variants/), one change each, applied as a CSS or JSX patch)

| Group | Examples | Count |
| --- | --- | --- |
| Defects (12 types) | Pay button hidden behind a banner; Add to cart missing; price cut off; cart total doesn't match the lines; overlapping text; unreadable contrast; broken product image; mobile layout overflows sideways; a modal stuck open over the page; a placeholder string ("{{price}}") shown; empty product list; wrong currency symbol | each on the 1–3 screens it affects: about 26 screenshots |
| Decoys (8 types) | new brand colour; different font; different hero picture; footer links reordered; slightly more spacing; rounded buttons; a new promo banner that covers nothing; product order changed | about 20 screenshots |
| Clean | the 10 untouched screens | 10 |

Defects and decoys are fixed and committed before any checker sees them. The pilot confirms that every defect is
visible to a person on the screenshot (I look at each) and that unit tests still pass with it.

## Checkers

| Checker | What it does |
| --- | --- |
| Pixel diff | compares with the clean screenshot of the same screen; flags if more than 0.5% of pixels changed (the common default) |
| Jev, assertions | each screen's assertions as `noul` questions in one request; flags the screenshot if any answer is on the wrong side of 0.5 |
| Jev, open question | one `noul`: "Does this screenshot show a visual defect a customer would notice?" |
| Vision model, assertions | the same assertions, asked of a general vision model ("answer yes or no to each") |
| Vision model, review | the model is asked to review the screenshot and list defects; flags if it lists any |

Vision models: two hosted through OpenRouter, chosen at the pilot from current vision models and named in the
amendment log, and one local model through Ollama (download needs the user's OK).

**The assertions** ([`assertions/`](assertions/)) are written from a requirements list for each page (what the page
must show), committed before the defects are designed. That keeps them from being tuned to the planted defects. I write
both, so the risk isn't zero; the report says so, and lists which defects no assertion covers.

Each checker sees each screenshot 3 times (separate calls), to measure consistency. The pixel diff is deterministic
and runs once.

## Measures

- **Defects caught** (higher is better): defect screenshots flagged, of all defect screenshots; also per defect type.
- **False alarms** (lower is better): decoy and clean screenshots flagged, reported separately.
- **Right reason** (assertion checkers): the flagged assertion is one that covers the planted defect.
- **Consistency:** share of screenshots with the same verdict in all 3 calls.
- **Cost and time** per screen.

## Hypotheses and analysis (fixed before the runs)

| # | Statement | How it is judged |
| --- | --- | --- |
| H1 | Jev assertions raise fewer false alarms on decoys than the pixel diff | One-sided paired permutation test (pairs: the same screenshot) |
| H2 | Jev assertions catch as many defects as the best vision model's assertions (no worse by more than 10 points) | Non-inferiority: the lower end of the bootstrap 95% interval of the difference above −10 points |
| H3 | Written assertions catch more defects than Jev's open question | One-sided paired permutation test |
| H4 | Jev and the best vision model differ in false alarms | Two-sided paired permutation test |

H1, H3 and H4 are Holm-adjusted together at α = 0.05; "no measurable difference" where a test isn't significant.
A screenshot's verdict for a checker is its majority over the 3 calls. Bootstrap intervals resample defect and decoy
types (not screenshots), 10,000 resamples, seed 1. Script: [`scripts/analyse.py`](scripts/analyse.py), written and
dry-run on the pilot before the main run.

## Size and cost

About 56 screenshots × 5 checker set-ups × up to 3 models × 3 calls: roughly 1,500 calls. Jev uses about 1,300 input
tokens per image plus the questions (measured 2026-11-03). OpenRouter calls cost cents each; the local model is free
but slower.

## Pilot (before the main run)

- Build the storefront with the mock backend and shoot the 10 clean screens; check each renders fully.
- Apply every variant; I check each defect is plainly visible and each decoy harmless, and that the unit tests pass.
- Run Jev and one vision model on the clean screens and 6 variants. **If every checker catches every defect with no
  false alarms** (a ceiling), harder defects are added before the main run, as in earlier experiments.

## What it does not show

- One app, ten screens, defects I designed. Real regressions are subtler and more varied.
- Single screenshots: no interaction (hover, scroll, animation) and no comparison with a reference for the model
  checkers.
- One wording of each assertion; better-written assertions might do better.

## Before it can run

- OK to download one local vision model.
- Jev credits: about 1,500 calls × ~1,500 tokens ≈ 2.3 M input tokens.

## Amendment log

(empty)
