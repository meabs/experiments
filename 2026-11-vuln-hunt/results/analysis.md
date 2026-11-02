# vuln-hunt: analysis

70 runs. Runs without a FINDINGS.json: 5.

## Planted vulnerabilities found, by tier

Mean share of each tier's vulnerabilities found per run (easy 3, medium 6, hard 9, very hard 5; 23 in all); **higher is better**. Runs: 10 per row.

| Arm | Easy | Medium | Hard | Very hard | Hard + very hard (of 14) | All (of 23) |
| --- | --- | --- | --- | --- | --- | --- |
| A. Codex | 63% | 35% | 51% | 50% | 7.1 | 11.1 |
| A2. Codex + checklist | 70% | 50% | 53% | 60% | 7.8 | 12.9 |
| B. Strands specialist | 77% | 47% | 39% | 46% | 5.8 | 10.9 |
| C. Strands team (Graph) | 83% | 55% | 76% | 82% | 10.9 | 16.7 |
| D. Strands swarm | 47% | 23% | 40% | 16% | 4.4 | 7.2 |
| B. Strands specialist, Qwen | 70% | 52% | 42% | 28% | 5.2 | 10.4 |
| C. Strands team, Qwen | 60% | 47% | 32% | 34% | 4.6 | 9.2 |

## Each vulnerability: share of runs that found it

Out of 10 runs per arm; **higher is better**.

| ID | OWASP | Tier | A | A2 | B | C | D | B Q | C Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V01 | A01 | medium | 90% | 100% | 90% | 100% | 60% | 90% | 40% |
| V02 | A01 | very hard | 50% | 40% | 0% | 70% | 0% | 0% | 30% |
| V03 | A01 | hard | 20% | 60% | 70% | 100% | 60% | 0% | 0% |
| V04 | A02 | easy | 0% | 30% | 30% | 50% | 0% | 40% | 60% |
| V05 | A02 | medium | 0% | 10% | 60% | 0% | 10% | 90% | 60% |
| V06 | A03 | medium | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| V07 | A03 | hard | 0% | 20% | 0% | 40% | 0% | 0% | 0% |
| V08 | A04 | easy | 90% | 80% | 100% | 100% | 70% | 70% | 60% |
| V09 | A04 | hard | 100% | 100% | 60% | 100% | 60% | 90% | 60% |
| V10 | A04 | very hard | 10% | 50% | 50% | 100% | 10% | 100% | 60% |
| V11 | A05 | easy | 100% | 100% | 100% | 100% | 70% | 100% | 60% |
| V12 | A05 | hard | 100% | 50% | 20% | 100% | 90% | 100% | 60% |
| V13 | A05 | medium | 90% | 100% | 90% | 100% | 70% | 30% | 60% |
| V14 | A06 | very hard | 10% | 10% | 0% | 40% | 0% | 0% | 0% |
| V15 | A06 | hard | 0% | 0% | 0% | 40% | 0% | 10% | 20% |
| V16 | A07 | medium | 0% | 10% | 0% | 30% | 0% | 40% | 60% |
| V17 | A07 | hard | 90% | 100% | 80% | 100% | 50% | 100% | 60% |
| V18 | A08 | hard | 100% | 90% | 50% | 100% | 70% | 80% | 60% |
| V19 | A08 | very hard | 80% | 100% | 80% | 100% | 20% | 0% | 20% |
| V20 | A09 | medium | 30% | 80% | 40% | 100% | 0% | 60% | 60% |
| V21 | A09 | hard | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| V22 | A10 | hard | 50% | 60% | 70% | 100% | 30% | 0% | 30% |
| V23 | A10 | very hard | 100% | 100% | 100% | 100% | 50% | 40% | 60% |

## By OWASP Top 10:2025 category

Mean share of the category's planted vulnerabilities found per run; **higher is better**.

| Category | A | A2 | B | C | D | B Q | C Q |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A01 Broken Access Control | 53% | 67% | 53% | 90% | 40% | 30% | 23% |
| A02 Security Misconfiguration | 0% | 20% | 45% | 25% | 5% | 65% | 60% |
| A03 Software Supply Chain Failures | 0% | 10% | 0% | 20% | 0% | 0% | 0% |
| A04 Cryptographic Failures | 67% | 77% | 70% | 100% | 47% | 87% | 60% |
| A05 Injection | 97% | 83% | 70% | 100% | 77% | 77% | 60% |
| A06 Insecure Design | 5% | 5% | 0% | 40% | 0% | 5% | 10% |
| A07 Authentication Failures | 45% | 55% | 40% | 65% | 25% | 70% | 60% |
| A08 Software or Data Integrity Failures | 90% | 95% | 65% | 100% | 45% | 40% | 40% |
| A09 Security Logging & Alerting Failures | 15% | 40% | 20% | 50% | 0% | 30% | 30% |
| A10 Mishandling of Exceptional Conditions | 75% | 80% | 85% | 100% | 40% | 20% | 45% |

## Findings and false alarms

Per run (mean). Matched: findings that identify a planted vulnerability. Duplicates: extra findings for a vulnerability already matched. Decoys flagged and wrong findings are false alarms (**lower is better**); real issues outside the key are listed separately. Precision: matched / (findings - outside the key); **higher is better**.

| Arm | Findings | Matched | Duplicates | Real, outside the key | Decoys flagged | Wrong | Precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Codex | 11.1 | 11.1 | 0.0 | 0.0 | 0 in all | 0 in all | 100% |
| A2. Codex + checklist | 13.1 | 12.7 | 0.0 | 0.4 | 0 in all | 0 in all | 100% |
| B. Strands specialist | 11.0 | 10.9 | 0.0 | 0.1 | 0 in all | 0 in all | 100% |
| C. Strands team (Graph) | 18.2 | 16.7 | 0.0 | 1.5 | 0 in all | 0 in all | 100% |
| D. Strands swarm | 7.2 | 7.2 | 0.0 | 0.0 | 0 in all | 0 in all | 100% |
| B. Strands specialist, Qwen | 11.3 | 10.4 | 0.0 | 0.4 | 2 in all | 3 in all | 97% |
| C. Strands team, Qwen | 10.3 | 9.2 | 0.0 | 0.4 | 1 in all | 6 in all | 93% |

## Cost and time

Per run (mean); cost at the model's list price (the same for Codex and OpenRouter's gpt-5.6-luna); **lower is better**. Qwen's price rises above 32k-token prompts; this uses the base price, so Qwen's cost is an underestimate.

| Arm | Cost | Median time | Tokens (input + output) | Total cost |
| --- | --- | --- | --- | --- |
| A. Codex | $0.016 | 44 s | 224k | $0.16 |
| A2. Codex + checklist | $0.024 | 74 s | 426k | $0.24 |
| B. Strands specialist | $0.015 | 72 s | 153k | $0.15 |
| C. Strands team (Graph) | $0.064 | 180 s | 474k | $0.64 |
| D. Strands swarm | $0.027 | 157 s | 485k | $0.27 |
| B. Strands specialist, Qwen | $0.008 | 304 s | 592k | $0.08 |
| C. Strands team, Qwen | $0.055 | 1222 s | 4525k | $0.55 |

Total: $2.09.

**D. Strands swarm:** statuses {'Status.COMPLETED': 10}; agents run per run (– = run failed): [3, 4, 3, 3, 3, 3, 3, 4, 4, 3]; runs in which each agent ran: {'access_auth': 4, 'injection': 10, 'recon': 10, 'verifier': 9}.

**C. Strands team:** statuses {'Status.COMPLETED': 10}; agents run per run (– = run failed): [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]; runs in which each agent ran: {'access_auth': 10, 'crypto_config_deps': 10, 'injection': 10, 'logic_integrity_errors': 10, 'recon': 10, 'verifier': 10}.

**C. Strands team, Qwen:** statuses {'Status.COMPLETED': 6, 'None': 4}; agents run per run (– = run failed): [6, 6, '–', 6, 6, 6, '–', 6, '–', '–']; runs in which each agent ran: {'access_auth': 6, 'crypto_config_deps': 6, 'injection': 6, 'logic_integrity_errors': 6, 'recon': 6, 'verifier': 6}.

## Hypotheses (Luna)

H1, H2, H4: mean difference in the per-vulnerability detection rate over the 14 hard and very-hard vulnerabilities (percentage points), exact one-sided sign-flip test, bootstrap 95% interval. H3: difference in mean precision, one-sided permutation test. Holm over H1-H4.

| Hypothesis | Difference | 95% interval | p | Holm p |
| --- | --- | --- | --- | --- |
| H1: B > A | -9.3 | -27.1 to +7.9 | 0.8457 | 1.0000 |
| H2: C > B | +36.4 | +25.0 to +47.9 | 0.0002 | 0.0010 |
| H3: precision B > A | +0.0 | – | 1.0000 | 1.0000 |
| H4: A2 > A | +5.0 | -7.1 to +15.7 | 0.2461 | 0.7383 |

Descriptive, A2 - B (same instructions and model, Codex against Strands): +14.3 points (95% interval +5.0 to +23.6).
Descriptive, D - C (swarm against Graph team): -46.4 points (95% interval -58.6 to -33.6).
