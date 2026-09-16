# Retained v2 search-feedback label deviation

The frozen search evaluator's auxiliary `mean_relocation_fraction` averages the
fraction supplied to the simulator, and its text calls this “relocated fraction.”
In v2 that value is an interior encoding, not the fraction of particles selected.
The actual allocated fraction is `executed_count / swarm_size`.

For five particles, counts 0–5 encode as 0, 0.1, 0.3, 0.5, 0.7 and 0.9, while
the actual allocated fractions are 0, 0.2, 0.4, 0.6, 0.8 and 1.0. Each positive
count therefore differs by 0.1; zero agrees. Across a response mixture, the mean
difference is 0.1 times the proportion of responses choosing a positive count.
The saved seed case 000 independently confirms 254 responses choosing exactly
three particles: auxiliary encoding mean 0.5, actual allocation fraction 0.6.

The simulator executed the requested integer counts. Saved measured errors,
objective-query accounting, score calculation and exact requested/executed count
distributions remain correct. The actual first mutation prompt included the
misleading label, the correct exact count distributions and the adapter formula.
The label may nevertheless have influenced proposal interpretation; its effect on
evolutionary search behavior is unknown. Correct numerical execution does not
establish that the wording had no search effect.

The run and frozen source were preserved unchanged. No completed evaluations are
repeated and historical prompt/feedback records are not rewritten. Validation and
final behavior summaries calculate fractions from selected particle indices.
These allocation fractions describe simulator-selected particles; partial final
responses retain separate objectively evaluated relocation counts and flags.
The final scientific report must retain this deviation and use actual allocation
fractions in its behavior summaries.

Evidence: `search-feedback-label-note.json`, the frozen evaluator and adapter,
the actual first Headless mutation prompt, and the original saved seed case.
