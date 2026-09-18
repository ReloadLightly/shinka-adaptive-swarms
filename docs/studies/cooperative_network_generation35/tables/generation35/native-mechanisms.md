# Native search mechanism audit

Observed 2026-09-18T10:54:51.917469+00:00; proposals 31–35.

This is saved-evidence analysis, not an atomic checkpoint. No simulations, inference or live-state writes.

| Proposal | Status | Parent | Island at sampling | Actual mutation route | Prompt |
|---|---|---:|---:|---|---|
| 31 | persisted_valid | 15 | 1 | headless/codex@gpt-5.6-sol?effort=xhigh | aab9b733-663b-48d2-8d3f-6885f152f239 |
| 32 | persisted_valid | 21 | 1 | headless/codex@gpt-6-astra?effort=xhigh | aab9b733-663b-48d2-8d3f-6885f152f239 |
| 33 | persisted_valid | 29 | 0 | headless/codex@gpt-5.6-sol?effort=xhigh | b1b2c70d-9030-41be-a518-0bfcfd72a73c |
| 34 | persisted_valid | 30 | 2 | headless/codex@gpt-5.6-sol?effort=xhigh | b1b2c70d-9030-41be-a518-0bfcfd72a73c |
| 35 | persisted_valid | 16 | 0 | headless/codex@gpt-6-astra?effort=xhigh | b1b2c70d-9030-41be-a518-0bfcfd72a73c |

## Triggered native events

```json
{
  "native_ucb_state_restored": 5,
  "native_ucb_selection": 5,
  "native_parent_sample": 5,
  "native_ucb_submitted": 5,
  "native_ucb_reward": 5
}
```

## Meta and prompt memory

Before continuation, pending generations: [22, 23, 24, 25, 26, 27, 28, 29, 30].
Current memory operation: None.
Completed meta updates: 3; processed programs: 30.
The normal interval counts evaluated programs in the retained buffer; proposal numbers are not the trigger.

Prompt creation and fitness attribution are distinct. See JSON prompt_rows and usage receipts for actual new prompts and their models.

## G31 versus G22

```json
{
  "scope": "Exact terminal population means only; no actor, adjacency or path equality claim",
  "generations": [
    31,
    22
  ],
  "case_counts": [
    288,
    288
  ],
  "same_case_ids": true,
  "exact_equal_count": 288,
  "different_case_ids": [],
  "all_288_exact_equal": true,
  "references": [
    "results/paper_trajectory_v2/search/gen_31/results/case_results.json",
    "results/paper_trajectory_v2/search/gen_22/results/case_results.json"
  ]
}
```

The accompanying JSON records source paths, hashes, event line numbers and sanitized provider accounting. Enabled mechanisms without corresponding events are not claimed to have triggered.
