# Compact publication: contents and omissions

This is the separate **Burghardt–Maoz cooperative multiplex-network experiment**,
`paper_trajectory_v2`, published from [commit `42ccaaf`](https://github.com/ReloadLightly/shinka-cooperative-network/commit/42ccaaf4b4f9c361f671cf54b6d874bc4d442359).
It is not the adaptive multi-swarm PSO campaign. Nothing here reports new experiments.

| Included | Location |
|---|---|
| Existing paper-style README, G30 and G35 reviews, research synthesis | [Paper](README.md), [G30](generation30_review.md), [G35](generation35_review.md), [synthesis](research_synthesis.md) |
| Seed and every available generated source through proposal 35; failed/invalid evidence; late unaccepted G1 source | [Complete program index](PROGRAM_INDEX.md) |
| Final SQLite checkpoint and matching native state, unchanged provenance and hashes | [Checkpoint](checkpoint/README.md) |
| Saved scientific figures and original figure provenance | [Figures](figures/) |
| Existing numerical review and native-event summary; G30 progress table; per-program metrics | [G35 tables](tables/generation35/), [G30 progress](tables/generation30-progress.csv), [program index](PROGRAM_INDEX.md) |
| Java interface/engine adapters and original upstream Java; evaluator/runtime/native integration; shared helpers; frozen development panel/comparator and task | [Source](source/), [frozen task](source/frozen/task_prompt.md), [scientific contract](source/experiments/paper_trajectory_v2/scientific_contract.json) |
| Source-to-publication file mapping and SHA256 values | [Provenance](PROVENANCE.json) |

## Material retained only in the original archive

All links below are pinned to `42ccaaf4b4f9c361f671cf54b6d874bc4d442359`. This compact publication **does not contain every raw trajectory**.

- [Full simulation cache](https://github.com/ReloadLightly/shinka-cooperative-network/tree/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/cache/): compressed per-case trajectory and network/actor history data.
- [Per-generation result directories](https://github.com/ReloadLightly/shinka-cooperative-network/tree/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/): raw case records, logs, accepted-job receipts, full proposal prompts/responses and recovery files beyond the compact failure evidence included here. Only the programs and listed metrics/receipts were copied.
- [Reference-run evidence](https://github.com/ReloadLightly/shinka-cooperative-network/tree/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/reference-report/) and [reference index](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/reference-index.json), full [reference grid](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/experiments/paper_trajectory_v2/reference_cases.json) and [comparator pool](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/experiments/paper_trajectory_v2/reference_comparator_pool.json).
- [G35 actor-level CSV](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-35-review/actor-effects.csv), [compact trajectory observations](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-35-review/compact-observations.json.gz), [G30 full numerical review](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/report/generation-30-review/review.json), and intermediate analyses. The selected saved figures and G35 numerical review are included without regeneration.
- [Complete numerical usage journal](https://github.com/ReloadLightly/shinka-cooperative-network/blob/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/evaluation_usage.jsonl), [inference usage receipts](https://github.com/ReloadLightly/shinka-cooperative-network/tree/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/usage/), [recovery history](https://github.com/ReloadLightly/shinka-cooperative-network/tree/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/recoveries/) and redundant [older checkpoints](https://github.com/ReloadLightly/shinka-cooperative-network/tree/42ccaaf4b4f9c361f671cf54b6d874bc4d442359/results/paper_trajectory_v2/search/checkpoints/).
- Dependency binaries, model weights, environments, other campaigns and paper PDFs are not included. The [source notice](source/NOTICE), [upstream provenance](source/upstream/multiplex/PROVENANCE.json) and [pinned requirements](source/requirements-shinka.txt) identify relevant dependencies and source precedence.

Scientific reports have only publication-scope notices and link adjustments; source,
metrics, figures, SQLite and native-state files retain their saved bytes. Original
absolute paths inside JSON/code are provenance, not a claim of a portable runtime.
The new program index is an inventory of saved database rows and failure receipts,
not a new scientific analysis. No simulations, research calls, policy execution,
fresh confirmation or literature research were performed for this publication.
