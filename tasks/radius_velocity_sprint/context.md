# Scientific context: bounded radius/velocity discovery

Blackwell, Branke and Li (2008), printed p.215, propose that retained velocities
can contribute to relocation overshoot and explain a preferred sampling radius.
This is a hypothesis; outcome interaction alone cannot identify overshoot. Our
fixed simulator resets only relocated particles when reset_velocity is true;
subsequent PSO and memory dynamics remain unchanged.

Phase A used the same eight development cases as this search, two for each
severity1/3 by period2500/5000 regime, 5D, ten peaks, 100000 counted queries.
Mean errors: count4/r1/retain 3.041839; count4/r1.5/retain 3.089088;
count4/r1/reset 3.329122; count4/r1.5/reset 3.332410; corrected count5/r1/retain
baseline 3.423599; exact V3 selected policy 3.152140. The seed is the best
fixed count-four policy, r1/retain, chosen on development data. V3 always used
radius1.5 and occasionally count3; it was +0.063052 worse than constant4/1.5
here (paired SD0.391413). This is reused development evidence, not confirmation.

The radius1.5-minus1 effect is +0.047249 retained, +0.003288 reset. The within-case
radius-by-velocity interaction mean is -0.043961, SD0.836208, range[-1.815428,
+0.930971]. Reset-minus-retain mean errors are +0.287283 (r1) and +0.243322 (r1.5).
All eight outcomes are retained; no significance gate controls continuation.
These observations do not support universal resetting or a single coherent
overshoot explanation. Individual cases and regimes differ materially.

The task evolves radius_scale and reset_velocity only; count4 and personal-best
memory reevaluation are fixed. Use the public scalar observations listed in the
task prompt. Constants and conditional functions are legitimate, with no reward
for complexity or a branch. Feedback compares every case with both the original
baseline and fixed seed, groups paired differences by regime and records actual
output-action occupancy. This does not expose hidden peak locations, optimum,
seeds or pilot data. Competing explanations include better constant radius,
conditional responses to observed loss/spread, altered query allocation and
stochastic closed-loop paths. Observational correlations do not identify a
mediator. This is a twelve-descendant probe, not exhaustive search. Any transfer
claim needs the separately frozen exploratory pilot; its outcomes are unavailable.
