# Four-slot scientific review

**16 September 2026, 16:17 UTC; development data only.** The published 5+1
schedule remains the best native program after four valid descendants. None of
the four alternatives improved either contemporary reference in mean error.
This is useful negative feedback about the proposals actually tested, not a
proof that no other schedule can improve the optimizer.

Run: `book_mpso_schedule_v1/20260916T154109Z`, native search seed `640001`.
All five native programs used the same eight 500,000-query cases. The seed
reused the eight compatible standalone 5+1 cases. Together with both references,
the experiment has completed **48 new full executions / 24 million queries**
at this review, plus eight cached seed records. No numerical failures occurred.

## What the programs actually did

| Generation | Exact behavioral rule | Mean error | Difference from 5+1 | Better / worse cases | Neutral updates converted |
|---|---|---:|---:|---:|---:|
| 0: published seed | Five on current detection; zero otherwise | 1.744569 | 0 | 0 / 0 | 1.2074% |
| 1 | Five on detection; two on each of the next three updates | 1.902573 | +0.158004 | 3 / 5 | 2.6039% |
| 2 | Five on detection; two on the next update only if the preceding update made no shared-best improvement | 1.813739 | +0.069170 | 4 / 4 | 1.2454% |
| 3 | Three on detection; zero otherwise | 1.919122 | +0.174553 | 1 / 7 | 0.7064% |
| 4 | Three on detection; one on each of the next two updates | 1.970515 | +0.225946 | 2 / 6 | 1.1522% |

The external 5+0 reference scored **1.743485**, close to the 5+1 seed on this
eight-case suite. All conversion percentages give each case equal weight.
The permanent quantum particle continues to sample under every native rule.
Requested temporary conversions and completed movement evaluations remain
separately counted at the final budget boundary.

These are distinct decisions, not cosmetic rewrites. Generations 1 and 2 test
extended sampling after the initial response. Generation 3 reduces the first
burst. Generation 4 redistributes five temporary conversions across three
updates in an uninterrupted response sequence. Actual age-bin measurements
match these functions. Generation 2's extra count-two action occupies only
**0.0925%** of all updates, so its conditional expression mostly reproduces the
original behavior rather than providing a frequently used new recovery mode.

The losses are not uniform. Generation 1 improves case 001 by **−0.760375**
but loses case 004 by **+1.427936**; omitting the latter would reverse its mean
effect. It remains included. Generation 4's largest loss is case 006,
**+1.245104**, while case 002 improves by **−0.610774**. These are complete
closed-loop trajectory differences. They do not identify overshoot or a causal
value of a particular quantum move.

## Feedback was used, rather than inferred from flags

The actual generation-2 and generation-3 mutation prompts contain this measured
generation-1 feedback:

```text
case_004 severity=1.0,period=5000: error=3.331870,
delta5+0=+1.823548, delta5+1=+1.427936;
interval-end error=2.7394387174541066; incomplete responses=0.
```

The saved original line is in
`evolution/search_seed_640001/gen_2/attempts/novelty_1/resample_1/patch_1/headless_prompt.md`
and the corresponding generation-3 prompt. Feedback also supplies all case
differences, the single-regime summary, conversion age bins, ordinary/temporary/
permanent quantum shared-best contributions, and both recovery extremes. Its
per-case raw summaries are verbose; the record does not substitute configuration
claims for the actual supplied content.

## Decision within the original batch

**Continue the remaining four originally authorized slots.** The first four
proposals establish that these longer and weaker responses did not beat the
published schedule on the development suite. They have not resolved whether a
different detection-dependent intensity, a trigger using observed deterioration,
or reliance on the permanent sampler can improve it. Those are concrete schedule
uncertainties within the existing interface, not invitations to change radius,
landscape, objective or engine settings. Native proposal and meta-memory decisions
remain in control; this review inserts no handcrafted candidate or new prompt.

There is no evidence of a malfunction or repeated identical behavior, and the
time and response allowances retain margin. At the receipt snapshot, four novelty
responses and four mutation responses have returned; the next mutation and the
first five-program meta-summary batch are pending (**14 logical responses
requested** in total). No p-value gate, additional slots, new cases or evaluator
changes are introduced. If the seed remains best, it will be selected and the
duplicate fresh comparison will be omitted as declared.
