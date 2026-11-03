# visual-checks: analysis

54 screenshots, 9 checkers.

## Results by checker

Defects caught: defect screenshots flagged (higher is better). False alarms: decoy or clean screenshots flagged (lower is better). Right reason: flagged defects where a flagged assertion covers the defect. Consistent: same verdict in every call. Wilson 95% in brackets.

| Checker | Defects caught | False alarms, decoys | False alarms, clean | Right reason | Consistent | Unusable calls | Median s per call | Median tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `jev-assert` | 19 / 22 (67%–95%) | 0 / 24 (0%–14%) | 0 / 8 (0%–32%) | 17 / 19 | 54 / 54 | 0 | 0.4 | 5,525 |
| `jev-open` | 22 / 22 (85%–100%) | 22 / 24 (74%–98%) | 7 / 8 (53%–98%) | – | 51 / 54 | 0 | 0.4 | 5,298 |
| `pixel` | 13 / 22 (39%–77%) | 16 / 24 (47%–82%) | 0 / 8 (0%–32%) | – | 54 / 54 | 0 | 0.0 | 0 |
| `vlm-assert-google_gemini-4-argon` | 22 / 22 (85%–100%) | 0 / 24 (0%–14%) | 0 / 8 (0%–32%) | 22 / 22 | 54 / 54 | 0 | 4.9 | 1,418 |
| `vlm-assert-ollama_qwen3-vl-8b` | 11 / 22 (31%–69%) | 0 / 24 (0%–14%) | 0 / 8 (0%–32%) | 10 / 11 | 52 / 54 | 0 | 9.0 | 2,299 |
| `vlm-assert-openai_gpt-6.1-terra` | 22 / 22 (85%–100%) | 10 / 24 (24%–61%) | 3 / 8 (14%–69%) | 22 / 22 | 54 / 54 | 0 | 4.1 | 2,482 |
| `vlm-review-google_gemini-4-argon` | 21 / 22 (78%–99%) | 12 / 24 (31%–69%) | 5 / 8 (31%–86%) | – | 48 / 54 | 0 | 5.8 | 1,394 |
| `vlm-review-ollama_qwen3-vl-8b` | 7 / 22 (16%–53%) | 0 / 24 (0%–14%) | 1 / 8 (2%–47%) | – | 48 / 54 | 9 | 15.2 | 2,259 |
| `vlm-review-openai_gpt-6.1-terra` | 21 / 22 (78%–99%) | 13 / 24 (35%–72%) | 4 / 8 (22%–78%) | – | 50 / 54 | 0 | 4.8 | 2,413 |

## Defects caught, by defect type

Screenshots of each defect flagged (higher is better).

| Defect | `jev-assert` | `jev-open` | `pixel` | `vlm-assert-google_gemini-4-argon` | `vlm-assert-ollama_qwen3-vl-8b` | `vlm-assert-openai_gpt-6.1-terra` | `vlm-review-google_gemini-4-argon` | `vlm-review-ollama_qwen3-vl-8b` | `vlm-review-openai_gpt-6.1-terra` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D01-pay-covered | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 0 / 1 | 1 / 1 |
| D02-no-add-to-cart | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 1 / 2 | 2 / 2 |
| D03-price-cut | 4 / 4 | 4 / 4 | 0 / 4 | 4 / 4 | 0 / 4 | 4 / 4 | 4 / 4 | 1 / 4 | 4 / 4 |
| D04-cart-total-wrong | 0 / 1 | 1 / 1 | 0 / 1 | 1 / 1 | 0 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| D05-text-overlap | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 2 / 2 |
| D06-low-contrast | 1 / 1 | 1 / 1 | 0 / 1 | 1 / 1 | 0 / 1 | 1 / 1 | 1 / 1 | 0 / 1 | 1 / 1 |
| D07-broken-image | 0 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 2 / 2 |
| D08-mobile-overflow | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 |
| D09-modal-stuck | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 1 / 2 | 2 / 2 |
| D10-template-text | 1 / 1 | 1 / 1 | 0 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| D11-missing-names | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 1 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 2 / 2 |
| D12-wrong-currency | 2 / 2 | 2 / 2 | 0 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 1 / 2 | 0 / 2 | 1 / 2 |

## Decoys flagged, by decoy type

Screenshots of each harmless change flagged (lower is better).

| Decoy | `jev-assert` | `jev-open` | `pixel` | `vlm-assert-google_gemini-4-argon` | `vlm-assert-ollama_qwen3-vl-8b` | `vlm-assert-openai_gpt-6.1-terra` | `vlm-review-google_gemini-4-argon` | `vlm-review-ollama_qwen3-vl-8b` | `vlm-review-openai_gpt-6.1-terra` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01-brand-colour | 0 / 4 | 4 / 4 | 3 / 4 | 0 / 4 | 0 / 4 | 2 / 4 | 2 / 4 | 0 / 4 | 1 / 4 |
| C02-font | 0 / 3 | 3 / 3 | 3 / 3 | 0 / 3 | 0 / 3 | 1 / 3 | 1 / 3 | 0 / 3 | 1 / 3 |
| C03-hero-picture | 0 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 0 / 2 | 1 / 2 | 0 / 2 | 0 / 2 | 0 / 2 |
| C04-footer-order | 0 / 4 | 3 / 4 | 0 / 4 | 0 / 4 | 0 / 4 | 2 / 4 | 2 / 4 | 0 / 4 | 3 / 4 |
| C05-spacing | 0 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 0 / 2 | 0 / 2 | 2 / 2 | 0 / 2 | 2 / 2 |
| C06-rounded | 0 / 3 | 3 / 3 | 0 / 3 | 0 / 3 | 0 / 3 | 1 / 3 | 1 / 3 | 0 / 3 | 2 / 3 |
| C07-promo-strip | 0 / 4 | 3 / 4 | 4 / 4 | 0 / 4 | 0 / 4 | 2 / 4 | 2 / 4 | 0 / 4 | 2 / 4 |
| C08-product-order | 0 / 2 | 2 / 2 | 2 / 2 | 0 / 2 | 0 / 2 | 1 / 2 | 2 / 2 | 0 / 2 | 2 / 2 |

## Hypotheses

Best vision model (most defects caught, then fewest decoy alarms): `vlm-assert-google_gemini-4-argon`.

| # | Statement | Difference | Value | p | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | Jev assertions raise fewer decoy false alarms than the pixel diff | pixel − Jev, decoys | +0.67 | 0.0001 | 0.0003 |
| H3 | Written assertions catch more defects than the open question | assertions − open, defects | -0.14 | 1.0000 | 1.0000 |
| H4 | Jev and the best vision model (`vlm-assert-google_gemini-4-argon`) differ in false alarms | Jev − best, decoys and clean | +0.00 | 1.0000 | 1.0000 |
| H2 | Jev assertions catch as many defects as the best vision model's assertions (within 10 points) | Jev − best, defects | -0.14 | 95% interval -0.37 to +0.00 | holds if lower end > −0.10: no |
