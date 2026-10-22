# Does Graph RAG answer multi-hop questions better? (knowledge retrieval)

**Draft design, written 2026-10-22. Not built, not run.** Nothing below is fixed until it is committed as final, after the development split has been used for tuning (see "Phases"). After that, changes go in the amendment log at the bottom.

This experiment is about **knowledge retrieval**, not coding. A system answers employees' questions from a company's internal documents: the wiki, service catalogue, decision records, API contract pages, team pages, meeting notes and incident reviews. The corpus describes services and APIs but contains no code, and no coding agent is involved.

## Question

Many teams want a knowledge graph, but few can show when it gives better answers than conventional retrieval. With the same documents and the same answer model:

- Does retrieving through a knowledge graph answer questions that need three or more linked facts better than vector retrieval?
- Does it beat vector retrieval with query decomposition, the stronger conventional rival?
- Is the graph no better on simple questions?
- When does it help, and what does it cost?

## Approach

### Why the usual comparison is unfair, and how this one avoids it

1. **The graph comes from the documents, not from the answer key.** The enterprise is generated from a ground-truth graph, but the graph arms never see it. They build their own graph by extracting it from the same documents the vector arms index.
2. **The questions do not use the graph's words.** Questions are generated from the ground truth, then paraphrased into the language staff would use. They are checked so that relation names (such as "depends on" in schema form) are not echoed.
3. **The vector baseline is not a straw man.** Plain top-k retrieval is weak at multi-hop by design. The main rival for the graph is vector retrieval with iterative query decomposition.
4. **The answer model and context budget are the same for every arm.** All arms get the same prompt, output format, answer model and context budget (8,000 tokens).

### The artificial enterprise

A seeded generator builds the ground-truth graph first, then has an LLM render it as documents. Answers and evidence paths come from the graph, so every score is computed without an LLM judge.

- **Entities:** about 150 services, 300 API contracts with versions, 40 teams, 120 people, 80 decision records with chains of decisions that replace earlier ones, environments and incidents.
- **Relations:** owns, depends on (by version), exposes, consumes, deprecates, supersedes, on call for, migrated to. Every relation has a valid-from and a valid-to date.
- **Documents:** about 1,500 per enterprise:
  - service pages, API contract pages written for readers, decision records, team pages, changelogs, meeting notes and incident reviews;
  - each fact is stated in one to three documents, some only in passing in prose;
  - the generator records which documents state each fact, so citations can be checked exactly.
- **Difficulty built in, the same for every arm:**
  - aliases and renamed services;
  - near-duplicate names;
  - stale pages contradicted by later decisions;
  - distractor documents that mention an entity but not the relation asked about.
- **Two document styles,** rendered from the same graph:
  - *structured:* mostly tables, specs and catalogue entries;
  - *narrative:* relations mostly stated in prose, notes and minutes.

  Graph extraction should do well on the first and struggle on the second. This factor answers *when* the graph helps.
- **Three enterprises** (different seeds), so the result does not rest on one corpus. Each is rendered in both styles: six corpora.
- **Fictional names throughout,** so the answer model cannot draw on what it already knows.

### Questions

All questions are generated from the ground truth with their answer and full evidence path, then paraphrased.

| Type | Example | Hops |
| --- | --- | --- |
| Lookup | Which team owns the ledger service? | 1 |
| Chain | Who should I contact about the refund limits in version 2 of the Payments API? | 2–4 |
| Set | Which teams need to know if we retire the old login service? | 3–5 |
| Temporal | What was the agreed token-expiry rule when Checkout 3.2 was released, and has it changed since? | 2–4 |
| Current vs stale | An old wiki page and a later decision disagree; what is true now? | 2–3 |
| Unanswerable | No such path exists; the right answer is to say so | — |

- **Per enterprise:** 40 questions at each of 1, 2, 3 and 4–5 hops, plus 30 unanswerable: 190 per enterprise, 570 in all, each asked of both styles.
- **Splits:** 30% development (tuning), 70% held-out test.
- **Validation, before any arm runs:**
  - every answer is unique, recomputed from the graph;
  - **closed book:** with no retrieval, accuracy is near zero;
  - **oracle:** given the gold evidence, the answer model reaches about 90%. Questions that fail it are ambiguous, and are dropped;
  - 50 questions are checked by hand.

### Arms

| Arm | Retrieval |
| --- | --- |
| A Vector | Chunk, embed, take the top passages up to the budget |
| B Vector + decomposition | The model breaks the question into sub-questions, step by step, using earlier answers; up to 5 steps; same total budget |
| C Graph | Schema-guided extraction into a property graph. At query time, the question is mapped to entities and turned into a graph query (with one retry); the subgraph and its source passages form the context |
| C′ Off-the-shelf Graph RAG | One widely used package (LightRAG, or GraphRAG's local search), with the same models. This is what most readers mean by "Graph RAG" |
| D Hybrid | Vector seeds, linked to graph entities, expanded up to k hops, reranked into the same budget |
| Control 0 | No retrieval: checks that the questions need the corpus |
| Control O | Gold evidence given: the ceiling, which separates retrieval failures from reasoning failures |

- **Equal tuning.** Each arm tries the same number of settings (4) on the development split of one enterprise per style. The winners are fixed before the test split is touched.
- **Extraction is not tuned.** Its settings are fixed in advance. Tuning them would mean rebuilding the graph for every setting.

### Models and infrastructure (lean configuration)

| Part | Choice | Where it runs |
| --- | --- | --- |
| Corpus writer and question paraphrasing | Gemini 3.7 Flash, a different family from both answer models | OpenRouter |
| Graph extraction (C, D, C′) | Claude Haiku 5.5 | OpenRouter |
| Answer model, primary (all arms, tuning and test) | Claude Haiku 5.5 | OpenRouter |
| Answer model, robustness check (test split only, same retrieved context) | Qwen 32B, open weights (exact version and quantisation recorded at step 0) | Local GPU |
| Embeddings | Qwen3-Embedding-8B, open weights | Local GPU |
| Graph store | Neo4j Community | Local |
| Harness | Python, run entirely on the larger machine (1 TB disk, 32 GB RAM, 32 GB GPU) | Local |

- **Pinned providers.** Each OpenRouter model is pinned to one provider, with fallbacks off, so every arm uses the same weights and latency is not mixed across providers.
- **Why a second answer model.** A stronger or weaker answer model could make up for, or expose, weak retrieval. If the graph's advantage appears with only one model, the result is about that model, not about Graph RAG. The graph and retrieved context are the same for both answer models; only the final answer call changes.

## Measures

All are scored against the ground truth, without an LLM judge:

- **Answer accuracy.** Answers are structured, as JSON with entity IDs and citations.
  - Exact match for single answers.
  - Exact-set match, with F1 reported alongside, for set answers.
  - Correct abstention for unanswerable questions.
  - Use of the current fact, and citation of the superseding document, for current-vs-stale questions.
- **Complete evidence-path recall.** The share of questions where the retrieved context contains every fact on the gold path, and recall for each hop. This is measured at retrieval, apart from the answer.
- **Incorrect citations.** Cited documents that do not state the fact they are cited for, from the fact-to-document map.
- **Latency.** Median and 95th percentile, split into embedding, retrieval and generation.
- **Cost.** Tokens and dollars per question, including decomposition and query-generation calls, plus the one-off build cost (embedding, extraction). Also the break-even number of questions at which the graph's build cost pays for itself.
- **Diagnostic: extracted-graph quality.** Precision and recall of the extracted edges against the ground truth, by document style. This explains why the graph arms win or lose.

## Hypotheses (to be fixed before the test split)

The unit is the question, paired across arms. Intervals come from bootstrapping over question templates within enterprises, because questions about the same entities are not independent.

| # | Hypothesis |
| --- | --- |
| H1 | On questions of 3 or more hops, C beats A |
| H2 | On questions of 3 or more hops, C beats B *(the claim that matters)* |
| H3 | C's advantage over A is larger at 3 or more hops than at 1 hop |
| H4 | On 1-hop questions, C is within 5 points of A (equivalence test) |
| H5 | On questions of 3 or more hops, D beats B |

- H1 to H5 are Holm-adjusted together, for the primary answer model.
- **Secondary:** the same comparisons with the Qwen answer model; all results by question type and by document style; C′ against C; cost and latency.

**Predictions, written before any build:**

- Decomposition (B) closes most of the gap on chain questions.
- The graph wins clearly on set, temporal and current-vs-stale questions, and on structured documents.
- On narrative documents, the graph loses ground, because extraction misses relations and confuses aliases.
- Hybrid (D) is the most robust, and the most expensive to build.

## Size and cost

| Item | Tokens | Cost |
| --- | --- | --- |
| Corpus writing: 6 corpora, about 9,000 documents | ~14M in, 5.5M out | $28 |
| Graph extraction (C, D) | ~30M in, 7M out | $5 |
| C′'s own extraction | ~20M in, 5M out | $4 |
| Questions: tuning and test, Haiku | ~99M in, 6.5M out | $13–18 |
| Questions: test split, local Qwen 32B | ~47M in | $0, GPU time |
| Embeddings: local Qwen3-Embedding-8B, 2 chunk sizes | ~17M | $0, ~1 hour |
| OpenRouter credit fee (about 5%) | | $2–3 |
| **Total** | | **≈ $52–58**, plus a 30% margin for reruns |

OpenRouter prices were read from its public models API on 2026-10-22. Token counts are estimates. The largest uncertainty is decomposition: if it averages 5 steps rather than 3, the question cost rises by about a quarter.

**Local GPU time** (estimates, measured at step 0):

- embeddings, about 35–90 minutes;
- Qwen 32B answering the test split (about 5,600 questions, mostly input), several hours, run overnight.

## Phases

0. **Set-up and throughput test on the larger machine.**
   - Record the GPU, the Qwen version and quantisation, and the embedding and answer speeds.
   - Pin the OpenRouter providers.
1. **Generator and corpora.**
   - Build the ground-truth graphs and render the six corpora.
   - Generate and paraphrase the questions.
   - Run the validation: closed book, oracle, hand check.
2. **Build the arms, and tune them on the development split.**
3. **Commit the design as final:** settings, hypotheses and analysis script.
4. **Run the test split, then analyse.**

Phase 1 is most of the work.

## Known limits

- **A synthetic enterprise.** It is built to be realistic, with aliases, stale pages and prose, but real knowledge bases are messier in ways a generator will not foresee.
- **Fixed pipelines only.** An agent that searches several times with tools may close the gap differently. That is a later experiment.
- **Implementation choices matter.** The graph arm is one implementation, with C′ as a widely used second. A better-engineered graph pipeline could do better.
- **Two answer models,** one closed and one open; others may differ.
- **The writer's model shapes the corpus.** It is from a different family from both answer models, to reduce familiarity effects.

## Amendment log

- 2026-10-22: draft written at the user's request: knowledge retrieval, not coding; lean configuration; local open-weight embeddings, plus a local Qwen 32B as the second answer model, on the user's larger machine.
