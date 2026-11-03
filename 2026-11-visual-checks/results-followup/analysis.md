# visual-checks: analysis

54 screenshots, 1 checkers.

## Results by checker

Defects caught: defect screenshots flagged (higher is better). False alarms: decoy or clean screenshots flagged (lower is better). Right reason: flagged defects where a flagged assertion covers the defect. Consistent: same verdict in every call. Wilson 95% in brackets.

| Checker | Defects caught | False alarms, decoys | False alarms, clean | Right reason | Consistent | Unusable calls | Median s per call | Median tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `jev-open-criteria` | 19 / 22 (67%–95%) | 18 / 24 (55%–88%) | 5 / 8 (31%–86%) | – | 41 / 54 | 0 | 0.4 | 5,383 |

## Defects caught, by defect type

Screenshots of each defect flagged (higher is better).

| Defect | `jev-open-criteria` |
| --- | --- |
| D01-pay-covered | 1 / 1 |
| D02-no-add-to-cart | 1 / 2 |
| D03-price-cut | 4 / 4 |
| D04-cart-total-wrong | 1 / 1 |
| D05-text-overlap | 2 / 2 |
| D06-low-contrast | 1 / 1 |
| D07-broken-image | 2 / 2 |
| D08-mobile-overflow | 2 / 2 |
| D09-modal-stuck | 2 / 2 |
| D10-template-text | 1 / 1 |
| D11-missing-names | 1 / 2 |
| D12-wrong-currency | 1 / 2 |

## Decoys flagged, by decoy type

Screenshots of each harmless change flagged (lower is better).

| Decoy | `jev-open-criteria` |
| --- | --- |
| C01-brand-colour | 3 / 4 |
| C02-font | 2 / 3 |
| C03-hero-picture | 2 / 2 |
| C04-footer-order | 2 / 4 |
| C05-spacing | 2 / 2 |
| C06-rounded | 1 / 3 |
| C07-promo-strip | 4 / 4 |
| C08-product-order | 2 / 2 |

## Hypotheses

Best vision model (most defects caught, then fewest decoy alarms): `None`.

| # | Statement | Difference | Value | p | Holm p |
| --- | --- | --- | --- | --- | --- |
