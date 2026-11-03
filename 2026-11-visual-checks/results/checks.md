# Hand checks

3 November 2026, after the main run. Each item: what I looked at and what I found.

- **Every defect is visible on its screenshot** (pilot, before the main run): I looked at all 22. Kept.
- **Jev's misses are real.** `D04-cart-total-wrong__cart-desktop`: lines US$28.00 + US$42.50 + US$129.00 = US$199.50,
  total shown US$219.50; Jev's `total` answer 0.93 (yes) in all 3 calls. `D07-broken-image__category-*`: Canvas
  Backpack and Wireless Headphones show empty white squares where the photo should be; Jev's `images` answer 0.84
  (desktop) and 0.92 (mobile). Not a scoring error.
- **gpt-6.1-terra's 13 assertion false alarms** are all the `header` assertion on mobile screenshots (10 decoys, 3
  clean), answered "no". The mobile header shows the logo, cart icon and a menu button; the navigation links are behind
  the button. The answer is a literal reading of an assertion I worded for desktop. Counted as false alarms, as fixed
  before the run.
- **Jev's two wrong-reason flags** (`D03-price-cut__category-*`): flagged on `no_overlap` (and `no_template` once),
  not on `cards`, the assertion covering the cut-off price. Counted as caught, not as right reason (17 of 19).
- **Threshold sweep** (Jev assertions, exploratory): flag if any answer is under t. t = 0.5 and 0.6: 19/22 defects,
  0/24 decoys; 0.7: 20/22, 4/24; 0.8: 22/22, 16/24; 0.9: 22/22, 24/24.
- **qwen3-vl:8b review:** 9 of 162 calls gave no answer within 600 s, recorded as unusable (not flagged), as amended.
- **Costs** from OpenRouter's reported usage: Gemini assertions $0.578 / review $0.651; gpt-6.1-terra assertions
  $0.239 / review $0.258 (162 calls each).
