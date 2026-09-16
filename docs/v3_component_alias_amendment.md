# V3 component-alias controller amendment

This amendment is prepared after development search outcomes and before
protected source review, validation, selection, or final evaluation. It extends
the earlier [constant proof amendment](v3_alias_certification.md), which leaves
jointly adaptive policies unproved. It is not described as implementation
committed before development outcomes.

The protocol requires explicit aliases when identical final execution can be
established. Some reviewed programs have a fixed radius output and a conditional
count. Replacing count therefore creates a constant action pair, even though
the original program is not constant. The earlier controller could recognize
this only for programs whose *entire* action was already proved constant.

The correction adds `joint_alias_amendment.py` and changes only the V3
controller's amendment verification, component execution identity and nominal
action interpretation. `build_policy`, `ComponentPolicy`, candidate source,
ranking, selection, numerical simulation, accounting, budgets, control
distributions and statistical analysis stay unchanged. A component that needs
execution still calls the original program on the reached observation,
validates its action, and then replaces the specified output. An established
alias shares the representative checkpoint and is not an additional execution.

Partial proofs are explicit reviewed facts bound to complete source SHA-256
values. The registry contains only the approved search-1 generations 26/27/28
(radius 1.25) and search-2 generations 21/14/23 (radius 1.5). All retain
conditional count 3/4. No rule infers purity or totality merely from a literal
radius in arbitrary source. The full `proven_constant` field remains unset for
these programs. The separate `proven_constant_outputs` record includes exact
source and registry hashes, domain and reasoning. The identity mechanism can
use a proved retained count or radius, but the current registry asserts only
the six reviewed radius facts.

The domain requires dimension five, five particles per swarm, severity one or
three, and the unmodified simulator's valid public scalar observations. Default
radius is exactly 0.5 or 1.5. A finite simulator distance is a square root of a
finite nonnegative binary64 sum, so it is at most the square root of the maximum
finite binary64 number. The normalized distances used in the reviewed sources
are therefore finite. Count computations use positive guarded denominators and
produce Python integer three or four. Search-2 generation 21 mutates only a
fresh local response dictionary; its early return precedes division when
diameter is small, and its remaining division has a positive denominator and
a ratio bounded by one. No source consumes RNG, changes observations, retains
state, or accesses external resources. The original call's validity and lack
of effects are part of the proof, not discarded because one output is replaced.

The original `registration.json` and every original `runner_snapshot` byte are
retained. After root review and a commit containing the exact amendment code,
install the amendment before shortlist certification:

```bash
.venv/bin/python scripts/install_joint_alias_amendment.py \
  --run results/joint_relocation_v3/study_20260916
.venv/bin/python scripts/run_joint_study.py freeze-shortlists \
  --run results/joint_relocation_v3/study_20260916
.venv/bin/python scripts/certify_joint_constants.py \
  --run results/joint_relocation_v3/study_20260916
# Then review the exact sources and use the existing protected stage commands.
```

The installer holds the normal study lock. It refuses an existing source
review, validation, selection, final-suite, final-stage, analysis, or constant
certification artifact. It accepts changes only to the original controller and
the newly added support module. Every scientific/tool/document source in its
receipt must match the bytes stored at the recorded Git commit. No numerical
case or candidate invocation occurs during installation or certification.

`controller_amendment.json` records the original registration hash, original and
new execution fingerprints, full committed revision, proof registry hash,
installation time, clean stage guards and source snapshot paths. New snapshots
live exclusively in `controller_amendment_snapshot/`. A pending write-once
receipt permits interrupted installation to finish only with the same inputs.
Completed receipts and snapshots cannot be overwritten by different contents.
Later read-only verification checks the immutable chain, current scientific
hashes, copied snapshots and chronology. It does not need the original run
paths or historical Git objects: the exact Git-byte comparison is performed and
recorded at installation, and all referenced snapshot paths are study-relative.

The certifier cites this controller-amendment record and attaches only exact
registry facts. Source review then binds the resulting shortlist hash. The
normal selection freeze carries these facts into component method metadata.
Stage signatures include the amended scientific fingerprint and frozen source
metadata. All final control and alias definitions precede fresh final seeds.

For a reviewed fixed-radius policy, count replacement yields
`(selected_fixed_count, certified_radius)`. It can alias another final winner
with that constant pair, a matching fixed control, or a genuinely point-mass
joint sampler. A zero-count component follows the existing zero-count constant
equivalence rule. Replacing radius leaves an adaptive count and is not
misclassified as constant. The original adaptive winner retains its source
identity; no observed score, sampled trace, or branch frequency establishes an
alias. Source-distinct validation candidates remain source-distinct.

Representative telemetry remains unchanged. A component alias may share a
checkpoint lacking `original_candidate_action` or `component_substitution`
fields; those fields are not fabricated. The component definition remains in
method metadata, and alias records explain reuse. Nominal-action reporting
uses the certified post-substitution pair, with explicit existing projections
for unused zero-count radii. Figures, paired analysis and query accounting use
the saved representative measurements.

Focused checks use exact source bytes and fabricated metadata only. They cover
adaptive identities, correct component aliases, zero counts, invalid facts and
domains, registry/source drift, installation chronology and interruption,
preserved original records, and verification after relocating an archived
study. They do not invoke candidates, objectives or models.
