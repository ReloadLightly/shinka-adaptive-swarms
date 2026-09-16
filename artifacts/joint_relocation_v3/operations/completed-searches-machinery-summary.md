# Completed V3 native machinery audit

Audited 2026-09-16T07:39:58.305051+00:00 from saved native databases, events, receipts, prompts and local embedding-service records. The auditor made **zero candidate, objective or model calls**. Full evidence: [completed-searches-machinery-audit.json](completed-searches-machinery-audit.json), SHA-256 `30b009dfa73f520e1c70d3ce135d43421e402d9f58ac4b202997a38480f04f77`.

Search indices below are the registered zero-based indices. Each search completed 30 evaluated generation slots (seed plus 29 valid descendants), 480 saved search cases and 31 database rows including one seed island copy. Across searches: 90 evaluated slots, 87 descendants, 1,440 search cases; island copies are not additional evaluations. Validation/final outcomes are outside this audit.

Each request cell is **native wrappers / requested logical responses / usable responses**. A batched wrapper may request five logical responses.

| Search | Mutation | Novelty | Meta | Closed shortfalls / unclosed wrappers |
|---|---:|---:|---:|---:|
| 0 | 30 / 30 / 30 | 30 / 30 / 30 | 18 / 42 / 42 | 0 / 0 |
| 1 | 30 / 30 / 30 | 30 / 30 / 30 | 18 / 42 / 42 | 0 / 0 |
| 2 | 31 / 31 / 31 | 31 / 31 / 31 | 18 / 42 / 42 | 0 / 0 |
| **Total** | **91 / 91 / 91** | **91 / 91 / 91** | **54 / 126 / 126** | **0 / 0** |

**236 wrappers requested 308 logical responses and returned 308 usable responses.** Saved start events and receipts have complete one-to-one coverage; no recorded feature-degradation events, novelty fallbacks, unresolved receipts or response shortfalls occurred. These are native-wrapper observations, not a count of hidden provider retries or HTTP transport requests.

Actual native sampling and prompt delivery were verified rather than inferred from configured settings. Each sampled parent/archive/top ID is retained in the JSON, with exact source and full feedback matches against saved database rows.

| Search | Sampling attempts / prompts | Parent / archive / top references | Full source-and-feedback references checked | Frozen context matches |
|---|---:|---:|---:|---:|
| 0 | 30 / 30 | 30 / 28 / 26 | 84 / 84 | 30 / 30 |
| 1 | 30 / 30 | 30 / 28 / 26 | 84 / 84 | 30 / 30 |
| 2 | 31 / 31 | 31 / 29 / 27 | 87 / 87 | 31 / 31 |
| **Total** | **91 / 91** | **91 / 85 / 79** | **255 / 255** | **91 / 91** |

Native patch types below count original evaluated database rows, not all proposal attempts. The rejected crossover attempts in searches 1 and 2 explain why crossover prompt counts exceed evaluated crossover counts.

| Search | Initial seed | Diff | Full rewrite | Crossover |
|---|---:|---:|---:|---:|
| 0 | 1 | 20 | 5 | 4 |
| 1 | 1 | 15 | 9 | 5 |
| 2 | 1 | 14 | 10 | 5 |
| **Total** | **3** | **49** | **24** | **14** |

Each search completed six meta updates at 5, 10, 15, 20, 25 and 30 evaluated programs. Each update requested five individual summaries, one global summary and one recommendation response: 42 logical meta responses per search. The 18 saved meta artifacts contain 90 numbered recommendation entries. The final update can complete after the final mutation; saved recommendations do not imply later use.

| Search | Completed meta updates | Mutation prompts with exact prior recommendation text | Crossover prompts without recommendation section | Other prompts before first completed meta update |
|---|---:|---:|---:|---:|
| 0 | 6 | 21 | 4 | 5 |
| 1 | 6 | 22 | 6 | 2 |
| 2 | 6 | 20 | 6 | 5 |
| **Total** | **18** | **63** | **16** | **12** |

All 63 matches are exact saved recommendation text, with prior completion supported by ordered native events. Crossover uses the installed native prompt format that omits meta injection; three of search 1's six crossover prompts also precede its first meta completion. No unexplained post-update diff/full injection gap was found. This audit counts matched prompts, not 63 distinct recommendation ideas.

| Search | Accepted / rejected / fallback novelty decisions | Rejected generation slots | Rejected maximum cosine similarity |
|---|---:|---|---|
| 0 | 29 / 1 / 0 | 13 | 0.988567412 |
| 1 | 29 / 1 / 0 | 29 | 0.986661851 |
| 2 | 29 / 2 / 0 | 19; 23 | 1.000000000; 0.977684259 |
| **Total** | **87 / 4 / 0** | **Four retries within existing slots** | |

The first two rejections identified cosmetic/equivalent reformulations. Search 2 generation 19 proposed identical code; generation 23 was judged an equivalent loss-clamping reformulation. Each was resampled inside its original generation slot. Accepted decisions nevertheless do **not** establish semantic novelty: search 1 generations 27 and 28 implement the same count threshold and fixed radius on the registered domain despite distinct source hashes and accepted novelty decisions. This is a novelty-quality limitation, not a provider fallback. Their hashes are `f4047cf27d7484f890ab84e4c35d2caa2a2b52d14f351083fa883591b812ff43` and `9406700ee6e2cd7fa88df9ab592813fd5f14e56bdef8b8098d5c053f809a74de`.

The database migration histories record 12 actual transfers: one in each direction between islands 0 and 1 at generations 10 and 20 of each search. Exact native IDs, rather than only native log messages, establish these transfers.

| Search | Migration generation | Island 0 → 1 native ID | Island 1 → 0 native ID |
|---|---:|---|---|
| 0 | 10 | `8cb76a7e-c3ee-447d-b1e0-791ad344a520` | `6864375b-097b-4fbc-a961-400a7aa3a57e` |
| 0 | 20 | `9eb2a79c-bbe4-4b42-8ad4-162b82f004e0` | `c4b14f28-cc6e-418b-81f5-a97421db227c` |
| 1 | 10 | `6d4882d1-bc0f-40fb-9b22-c58175fc9f6d` | `a30bb48e-7737-44fe-8339-f32d8e0d6177` |
| 1 | 20 | `8125e5a5-f0a4-4056-9367-3e000f470654` | `76b563aa-f916-4793-87da-37661f5ff881` |
| 2 | 10 | `62702cca-bb38-4351-9c61-c4937478f0ab` | `38542c73-831f-47e9-ad43-6b70ba0f107f` |
| 2 | 20 | `44023814-85c8-48a2-8177-6df514403f31` | `b016b694-1a25-45d4-86ed-89dcbd5db3e1` |

Local embeddings are separate CPU inference, not subscription LLM requests. Native searches logged 31, 31 and 32 embedding starts/completions respectively: three initial seeds plus 91 proposals, all dimension 768, without native embedding degradation. Service time buckets independently show:

| Service observation period | Request starts | Input texts | Completion events / texts | Errors |
|---|---:|---:|---:|---|
| Development before frozen calibration | 6 | 46 | 6 / 46 | 0 |
| After freeze, before first search | 0 | 0 | 0 / 0 | 1 intentional unknown-model HTTP rejection |
| Search period | 94 | 94 | 94 / 94 | 0 |

The service used the pinned Jina code model ONNX int8 artifact with CPUExecutionProvider, two threads, disjoint 512-token windows and 768-dimensional normalized embeddings. No remote embedding fallback was recorded. SHA-256 text identity links 91 of 94 search-period inputs to saved program sources; three rejected/overwritten inputs remain unlinked. Development links cover 42 of 46 texts against declared calibration sources, with four unlinked. These are observed hash links, not reconstructed missing content. Completion events lack request IDs/input hashes, so individual concurrent requests are not paired to completions and no hidden requests are invented. The expected readiness rejection and freeze boundary are recorded separately in [embedding-http-checks.json](embedding-http-checks.json) and [embedding-freeze.json](embedding-freeze.json).

All searches requested `gpt-6-astra`; all usable native receipts report `headless/codex@gpt-6-astra`. Mutation client settings record temperature 0 and a 16,384-token cap; novelty/meta record temperature 0.75 and a 4,096-token cap. Native configuration serializes `reasoning_efforts="disabled"`, while the manifest records no effort override sent and the Codex profile/default applying. Effective provider effort remains **unverified**; these observations do not establish internal Ultra effort or provider enforcement of every client setting. Subscription routing is the recorded route; no paid fallback/degraded route was observed.

Native cost estimates sum to 18.879200 (mutation), 5.384990 (novelty) and 25.954568 (meta), total **50.218758** in the saved native cost field. These are accounting estimates, **not billing statements or paid API charges**.

A [clock-discontinuity record](clock-discontinuity-20260916.json) documents about 47.5 minutes of wall-clock advance beyond monotonic elapsed time during search 2. Host suspension or clock correction is consistent with the evidence; the cause was not directly observed. The original supervisor/controller survived and continued without restart or repeated saved evaluations. Wall-clock durations should not be treated as uninterrupted compute times.

The native phrase “passes all validation tests” in search feedback means search-evaluator correctness, not the protected V3 validation suite; see [native-feedback-wording-note.json](native-feedback-wording-note.json). All claims above concern observed machinery and saved execution. They do not establish optimizer superiority, generalization, or semantic diversity.
