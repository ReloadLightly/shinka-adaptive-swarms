# Saved native search audit

Audited 2026-09-16T00:24:27.766398+00:00; source `results/evolution/20260915T101024.562418Z-search`. Original results were read only; zero candidates were executed.

The search completed its original 20-slot target on 15 September 2026 at 12:41:51 UTC. No unfinished evaluations remain to resume.

- SQLite integrity: `ok`; 21 rows represent 20 evaluated programs (two seed island copies and 19 descendants). All parents resolve.
- All 80 saved cases parse and contain exactly 50,000 counted objective evaluations: 4,000,000 in total. All category counts sum to their budgets.
- Generations 3–19 have complete four-case checkpoints with matching program hashes and no active case. Generations 0–2 retain complete legacy cases and metrics.
- Every saved generation source matches its native database program. All programs share identical initial and subsequent landscape hashes for each paired case.
- All 16 best-reference artifact hashes match. Saved worker stderr files are empty; final logs contain `run_complete`.
- Native generation-event and attempt tables are empty; completion is established from program rows, metrics, case artifacts and persistent progress events.

The best program is generation 12 (`e671664f-bcd3-4e00-b681-7b532d7daa22`), with mean offline error **1.9703446** versus **2.7750773** for the corrected baseline seed (29.00% lower on this search suite). Its direct parent lineage is 0 → 4 → 9 → 10 → 12.

| Search case | Severity | Corrected seed | Best generation 12 | Parent generation 10 |
|---|---:|---:|---:|---:|
| case_000 | 1 | 5.694844 | 2.466150 | 2.410080 |
| case_001 | 1 | 2.050179 | 1.308247 | 2.001169 |
| case_002 | 3 | 1.049280 | 1.145215 | 1.030198 |
| case_003 | 3 | 2.306006 | 2.961766 | 2.682702 |

The best improves both severity-1 cases and worsens both severity-3 cases against the seed. The compact-swarm floor improves one case against its direct parent and worsens three. These selected search outcomes do not establish independent generalization or a causal mechanism.

The program combines deterioration-sensitive radius and partial relocation with dispersion-based anchor preservation. Its new floor broadens recovery for compact swarms even when fitness loss is small. Memory reevaluation and existing velocities are retained.

Static inspection of all 20 programs found no imports, filesystem/network calls, introspection, evaluator access or held-out inputs. The best reads only `relative_fitness_drop`, `default_radius` and `swarm_diameter`. This audit does not claim Python sandbox isolation.

The frozen program has a floating-point boundary worth preserving and reporting: blending sometimes returns `fraction=0.6000000000000001`, so `ceil(5*fraction)=4`. This occurred in **29 of 204** best-policy responses. Actual relocation counts were 145 responses with four particles, 50 with three and nine with two. Do not silently replace this behavior with an intended three-particle response or attribute performance to this rounding without a separate test.

All 19 mutation records name `headless/codex@gpt-6-astra`. Saved inner effort was not sent; the Codex profile/default applied. Supervising Astra/Ultra and internal effort remain separate.
