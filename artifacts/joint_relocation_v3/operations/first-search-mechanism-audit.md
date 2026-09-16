# First v3 search runtime audit

Observed at 2026-09-16T03:51:04.374760+00:00; search remains active. This audit adds no objective evaluations, embeddings, or model requests.

All 29 frozen source/profile/model-artifact hashes match. The running service reports the frozen source and model manifest. Six real local embedding requests completed without a research request error. All seven saved database vectors (six originals and one native island copy) are finite, 768-dimensional, approximately unit norm, and match service input source hashes. The copy is not another evaluation or embedding call.

Actual returned logical responses: 5 mutation, 5 novelty, and 7 meta. All report `headless/codex@gpt-6-astra`. The first native meta update completed at 03:50:48 UTC; its three requests yielded five program summaries, one consolidation response, and one recommendation response. No degraded-feature event or novelty fallback was observed in this snapshot. These are early mechanism observations, not evidence of optimizer improvement or scientific originality.

The native client's `reasoning_efforts=disabled` sentinel is not forwarded as provider effort. Pinned Shinka builds the Headless effort option only from the route query; live Headless and Codex arguments contain no effort override. The effective provider effort remains unverified and must not be labeled disabled or Ultra. Native dollar-cost fields are bookkeeping estimates, not proof of paid API billing.

Detailed receipts, exact hash comparisons, service events, vectors' properties, live argv, and source trace are in `first-search-mechanism-audit.json`. The initial observation is preserved in `first-search-mechanism-audit-initial.json`. Later generations, retries, migrations and subsequent meta updates require their own accumulated evidence.
