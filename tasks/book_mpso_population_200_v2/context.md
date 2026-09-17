# Chapter-grounded population allocation: 200 peaks

Blackwell, Branke and Li, "Particle Swarms for Dynamic Optimization Problems"
(2008), describe MPSO's tension between local convergence inside a subswarm and
maintaining several search groups. Personal and shared memories support local
convergence; exclusion and swarm birth/removal sustain search across space. The
chapter identifies adapting particle numbers within a subswarm as future work.
That rationale is a hypothesis to test, not evidence that adaptation must help.

Question: can an evolved population rule improve reconstructed chapter 5+1 MPSO
when 200 peaks compete for a fixed counted objective-evaluation budget?

The preceding ten-peak population study evaluated six valid native descendants.
None improved the reconstructed target-five mean of 1.744569. Fixed target three
scored 1.806340, target seven 1.871657, and the closest descendant (constant target
six) 1.776112. Larger groups shifted queries toward ordinary PSO while average
subswarm counts changed little. Accepted rules did not use the available global
workload or previous-target fields. These are historical ten-peak development
findings, not performance estimates for this new 200-peak condition. The earlier
temporary-conversion search likewise found no better schedule; retain the
published change response throughout this experiment.

Only choose_neutral_count(observation) evolves. The public interface and deterministic resizing adapter are unchanged. The VERSIONED engine repairs convergence: the smallest enclosing ball of neutral positions must fit the current convergence radius; the historical pairwise-diameter approximation is no longer used. This is a source-fidelity repair, never an evolutionary gain. Each newborn/reinitialized swarm
starts with five neutrals plus one permanent quantum particle. The target is an
integer from two through eight; counted change detection and completed memory
refresh precede the call. At most one neutral is added or removed toward the
target before movement. All current neutrals take the chapter quantum-response
movement on that detected update and ordinary PSO otherwise. The permanent
quantum role always samples. Radius, retained velocities, personal memories,
coefficients, exclusion order and swarm birth/removal remain fixed; the corrected enclosing-ball convergence convention is shared by every control and candidate. This changes population within groups, without particle transfers
or conservation of a global particle total.

The four development seed pairs registered in the preceding 200-peak study use five dimensions, 200 conical peaks,
severity one, changes every 5000 queries, correlation zero, nexcess one and
exactly 500000 queries each. All four remain fixed throughout selection. Every
movement, initialization, detector check and memory refresh shares that budget.
Independent environment randomness pairs landscape histories across programs.

Newly measured fixed targets three and five supply the contemporary paired
controls. Both start at five and resize by at most one per detection. Target
five is the reconstructed chapter 5+1 and native seed; source-identical seed
evaluation reuses its four current control cases. No ten-peak record is reused
as a 200-peak result. Candidate fitness is 1/(1+mean offline error), without
complexity or adaptation bonuses. Constant rules are legitimate candidates.

Available public workload fields include swarm_count and total_particle_count;
previous_requested_target records the preceding target of this same subswarm.
These may help express a rule but their use is optional. Other public observations
describe counted deterioration/improvement, neutral spread and motion. Hidden
peak counts/locations, optimum, benchmark error, seeds and future changes are
unavailable to the policy. The known benchmark scale still supplies its radius.

Additional ordinary trajectories may help local search; fewer particles may
permit more subswarm updates under the same budget. Changed convergence and
birth/removal timing, memory quality, random closed-loop effects and constant
size tuning are competing explanations. A conditional expression alone isolates
none of them. Subswarm count is not a count of distinct peaks covered.

This is a resumable 50-descendant campaign, including the seed in final native selection. Session pauses are interim and cannot trigger winner freezing or fresh testing. All seven constant targets 2..8 will be measured before final selection; evolutionary feedback stays consistently against targets three and five. At campaign completion, a distinct native program improving on the seed can trigger a later frozen comparison on 50 NEW paired histories against the corrected 5+1 and independently development-selected constant. Fresh outcomes remain outside mutation, novelty and meta-memory. Constants are legitimate and no complexity or variability bonus applies. This small MPSO extension does not reproduce all chapter conditions, compare SPSO, establish global optimality, or identify a causal benefit of a particular Shinka mechanism.
