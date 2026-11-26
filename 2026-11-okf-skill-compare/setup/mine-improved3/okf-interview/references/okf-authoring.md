# OKF authoring contract

Based on [OKF v0.3 SPEC.md](https://github.com/open-knowledge-format/open-knowledge-format/blob/527e81aff55992be21507e97004286789126f88c/SPEC.md). The bundled validator is copied unchanged from `skills/okf-generate/scripts/validate.py` at that revision, copyright 2026 Google LLC, Apache-2.0. The license is [OKF-LICENSE.txt](OKF-LICENSE.txt). It requires Python 3.9+ and PyYAML. No upstream skill installation or model API is needed. This reference summarizes the subset needed for interviews; consult the pinned specification for advanced fields or migrations.

## Structure and identity

- A bundle is a directory tree. Concepts are UTF-8 `.md` files with YAML frontmatter and a nonempty string `type`. `type` is the only universally required concept field. Type names are extensible; reuse existing local conventions.
- Use stable lowercase filenames. The concept ID is its bundle-relative path without `.md`.
- Reserve `index.md` for navigation and `log.md` for history; they are not concepts.
- Root `index.md`: frontmatter with `okf_version: "0.3"`, title and scope description. Add a license only if known. Preserve existing root metadata.
- Directory indexes: no frontmatter; link direct children with descriptions. `log.md`: no frontmatter; newest `## YYYY-MM-DD` entries first.
- A concept's frontmatter starts and ends with a line exactly `---`. Use a YAML mapping, no duplicate keys or custom tags. Body text is Markdown with GFM tables and footnotes.

## Minimal interview-derived concept

The following is a template, not a factual example. Replace placeholders with supported facts, omit fields you cannot justify, and never write the placeholder timestamps literally.

```yaml
---
type: Decision
title: <Specific decision and scope>
description: <One sentence explaining when this knowledge matters>
tags: [<relevant-tag>]
sources:
  - id: engineer-interview
    resource: "<Actual interview artifact URL, bundle path, or descriptive interview scope>"
    title: "<Interview topic and date>"
    # author: "human:<id>" only when the person supplied that identity
generated:
  by: "<actual agent product/model or other truthful actor>"
  at: "<actual current RFC3339 timestamp with offset>"
status: draft
---
```

Lead with the decision, its conditions, and its consequence. Cite an interview-derived claim as `...[^engineer-interview]`, with `[^engineer-interview]: Interview topic and date` at the end. Footnote labels match `sources[].id`; use a different source ID for repository evidence. Do not cite an interview as proof that a suspected technical cause is established.

## Provenance and links

Each `sources` entry requires `resource`. It can identify an accessible artifact or describe a source scope such as “Engineering interview about the billing integration on <date>; no recording retained.” Do not fabricate a URL, transcript path, or personal actor. A `source` document in the bundle can hold consented, curated interview evidence; it need not contain raw replies. Raw notes should normally remain outside the consumable bundle.

Use pinned commit URLs for repository evidence. `resource` on the concept itself is optional; set it only for a genuine canonical asset, not an invented API or issue URL.

Use relative Markdown links between concepts, such as `../decisions/replay.md`. For frontmatter paths, prefer bundle-root paths such as `/references/interview.md`. Paths without a leading `/` resolve from the containing document. Link only to existing files. Keep repository links external so a bundle stays portable. Source footnotes attribute claims, while ordinary links connect related knowledge.

## Trust, lifecycle, and extensions

`generated.by` records the real producer, in `<product>/<model-or-version>` or `<scheme>:<id>` form. `generated.at` is the actual last meaningful change time. Do not guess a model identifier you do not know; use a truthful actor such as `process:okf-interview-author` and explain it if necessary.

`verified` records actual confirmation of the finished content with `by` and `at`. No current event means unverified; a current non-human event means machine-confirmed; a current `human:<id>` event means human-reviewed. Structural validation is not content verification. A simulated engineer is never a human reviewer. Preserve old events; generation newer than verification makes the old review historical.

`status` is `draft`, `stable`, or `deprecated`. Omitted status means stable, so explicitly mark complete but unreviewed interview answers `draft`. This skill's admission rule is stricter than OKF's format requirements: incomplete answers and anything needing clarification stay in a separate review log outside the bundle, even though OKF itself permits incomplete drafts. Do not use `status: unknown` or `status: resolved`. Use `deprecated` and `superseded_by` for retirement/replacement when appropriate.

Set `stale_after` only for a real agreed review/expiry date. Preserve unknown keys. Additional metadata should use `x-<producer>-<name>`, for example `x-okf-interview-synthetic: true`; label synthetic content visibly in its body too. Do not add custom trust scores or risk scores as if they were standard fields.

## Actors, migration and retirement

Actors are `<producer>/<version>` for tools and `<scheme>:<id>` for everything else, with the schemes `human:`, `team:` and `process:`. Only `human:` earns the human-reviewed tier, because a team name does not say which person checked the content; never record `team:` as a review of this skill's output.

For migrating a v0.1 or v0.2 bundle, and for the full rules on `status: deprecated`, `superseded_by` and moving or renaming a concept (leave a short deprecated concept at the old path), use the upstream skill's references rather than copies kept here: [migration](https://github.com/open-knowledge-format/open-knowledge-format/blob/527e81aff55992be21507e97004286789126f88c/skills/okf-generate/references/migration.md) and [`okf-generate` rules 9 and 10](https://github.com/open-knowledge-format/open-knowledge-format/blob/527e81aff55992be21507e97004286789126f88c/skills/okf-generate/SKILL.md).
