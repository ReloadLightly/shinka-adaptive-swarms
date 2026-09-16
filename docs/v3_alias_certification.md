# V3 constant-alias certification amendment

This is a narrow implementation amendment prepared after development search 0
completed and before any protected validation, source-review freeze, selection,
or final evaluation. It is **not** described as implementation committed before
search outcomes. The original registration, registered scientific sources,
native searches and their checkpoints remain unchanged.

The protocol requires explicit final aliases when identical execution can be
established. The registered controller already consumes `proven_constant`
metadata, but its automatic recognizer accepts only direct literal returns and
the fixed swarm-size expression. Static review found three search-0 shortlist
sources that always return count four at respective radii 1.21875, 1.1875 and
1.25. They use `min`, `int`, or local assignments that the original recognizer
does not accept. These three radii differ from one another and from the fixed
grid, so all three remain distinct validation candidates. Their constant
behavior can nevertheless establish aliases among later component or sampler
controls. Equal measured scores or traces are never an equivalence proof.

`scripts/certify_joint_constants.py` addresses this gap without changing the
registered recognizer, simulator, adapter, controller, ranking, source set,
selection, controls, budgets, seeds, or inferential rules. It parses source text
without importing or invoking a candidate. The allowed subset is a module
containing only docstrings and one ordinary `choose_relocation` definition,
safe builtin annotations, finite numeric constants, the fixed integer
`observation["swarm_size"]`, local names and simple/tuple assignments, unary
numeric signs, and the unshadowed `int` and multi-argument `min` builtins over
known constants. A final direct dictionary must satisfy the exact output
contract. Imports, decorators, defaults, executable annotations, other state,
unknown expressions, external access, mutation, branches, loops and persistent
effects are rejected by the prover. Unsupported programs retain their original
metadata and are executed normally. Every certificate is restricted to the
registered five-particle domain; both registered case suites are checked.

After all three native searches finish, the order is:

```bash
.venv/bin/python scripts/run_joint_study.py freeze-shortlists \
  --run results/joint_relocation_v3/study_20260916
.venv/bin/python scripts/certify_joint_constants.py \
  --run results/joint_relocation_v3/study_20260916
# Review the exact sources, then use the existing `review` and `validate`
# controller stages. Source review binds the certified shortlist hash.
```

The exact certifier must be committed before actual certification. It takes the
existing study-controller lock and refuses certification after any source
review, validation, selection, final-suite, final-stage, or analysis artifact
exists. No protected outcome informs proof recognition or alias decisions.

The operation preserves the original shortlist byte for byte as
`shortlists.pre-alias-certification.json`. An exclusively created
`constant_alias_certification.json` records both shortlist hashes, the exact
source hashes and proof results, certifier source hash and repository revision,
domain, time, and the fact that the amendment follows development outcomes.
Only `proven_constant` and explicit proof-provenance metadata are added to the
active shortlist; search ranks, source bytes, occurrences and the program set
stay fixed. This expressly supersedes the original shortlist **metadata hash
before the source-review freeze**, rather than changing selection after it.
The certificate is persisted before the atomic metadata replacement. A retry
can finish that same recorded publication, but cannot change its contents.
The normal frozen stage signature then includes the certified shortlist hash.

Native searches retain every original execution, even when a later proof shows
behavioral equivalence. Validation still evaluates the source-distinct union,
with only established execution aliases. Final methods use the registered
identity rules. A constant winner and an identical component substitution can
share a checkpoint. A joint sampler aliases a constant only when the full
frozen pair distribution in the relevant regime is a single pair. The baseline
fallback for a validation case with no responses can prevent that equivalence;
the certification does not remove or reinterpret this fallback.

Alias telemetry always describes the representative execution. A component
alias may share a winner or fixed-control checkpoint that has no
`component_substitution` or `original_candidate_action` fields. Those fields
are not fabricated: the nominal component intervention remains in frozen
method metadata and the explicit alias record. Existing figure and audit
readers do not require component-call telemetry from an aliased execution.
Action summaries use the existing `nominal_action_pairs` helper, including its
labeled nominal radius projection for proven zero-count aliases. Measured
observations, previous-radius fields, traces and objective accounting remain
unchanged. An alias is never reported as an additional evaluated method case.

Focused checks cover the exact three observed source hashes, unsafe and unknown
syntax, preserved registration/source/ranking records, protected-stage refusal,
interrupted publication, and existing program/component/sampler identity and
telemetry paths. They use fabricated metadata and static parsing only; they do
not invoke candidate policies, simulations, objectives, or model calls.
