import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        // Preserve source formation and low-triangle behavior. After the shock,
        // reorganize only where coordinated clique formation is plausible.
        if (observation.time() < 50.0
                || observation.triangleBenefit() < 0.4) {
            turn.originalTurn();
            return;
        }
        final int self = observation.actor();
        final int population = observation.population();
        final int target = targetDegree(observation);
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        // Prefer removing an out-of-cohort edge from the denser layer.
        int dropLayer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int dropPartner = unwantedNeighbor(
                dropLayer == 0 ? neighbors0 : neighbors1,
                self, target, population);
        if (dropPartner < 0) {
            dropLayer = 1 - dropLayer;
            dropPartner = unwantedNeighbor(
                    dropLayer == 0 ? neighbors0 : neighbors1,
                    self, target, population);
        }
        // Add missing cohort ties to the sparser layer first so that the two
        // layers converge toward the same clique and obtain overlap benefits.
        int addLayer =
                neighbors0.length <= neighbors1.length ? 0 : 1;
        int addPartner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                self, target, population, memory, observation.time());
        if (addPartner < 0) {
            addLayer = 1 - addLayer;
            addPartner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    self, target, population, memory, observation.time());
        }
        if (addPartner < 0) {
            if (dropPartner >= 0) {
                turn.drop(dropPartner, dropLayer);
            } else {
                turn.noOp();
            }
            return;
        }
        if (dropPartner < 0) {
            if (!turn.add(addPartner, addLayer)) {
                memory.set(
                        addPartner,
                        cooldownUntil(observation.time()));
            }
            return;
        }
        if (turn.rewire(
                addPartner, addLayer, dropPartner, dropLayer)) {
            // Source semantics permit one further old-edge deletion after an
            // accepted addition. Use it only for another out-of-cohort edge.
            dropOneUnwanted(
                    turn, self, target, population);
        } else {
            // A failed recipient decision is temporary evidence. Retry only
            // after the topology has had five rounds in which to change.
            memory.set(
                    addPartner,
                    cooldownUntil(observation.time()));
            turn.drop(dropPartner, dropLayer);
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        if (observation.time() < 50.0
                || observation.triangleBenefit() < 0.4) {
            return offer.originalAcceptance();
        }
        if (!Double.isFinite(offer.gain())) {
            return Decision.no();
        }
        int target = targetDegree(observation);
        return sameCohort(
                observation.actor(),
                offer.proposer(),
                target,
                observation.population())
                ? Decision.yes()
                : Decision.no();
    }
    private double cooldownUntil(double time) {
        return time + 5.0;
    }
    private void dropOneUnwanted(
            Turn turn,
            int self,
            int target,
            int population) {
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int partner = unwantedNeighbor(
                layer == 0 ? neighbors0 : neighbors1,
                self, target, population);
        if (partner < 0) {
            layer = 1 - layer;
            partner = unwantedNeighbor(
                    layer == 0 ? neighbors0 : neighbors1,
                    self, target, population);
        }
        if (partner >= 0) {
            turn.drop(partner, layer);
        }
    }
    private int targetDegree(Observation observation) {
        int bestDegree = 0;
        double bestUtility = 0.0;
        double costSum =
                observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
        // Exact utility of belonging to the same degree-k clique on both
        // layers: 2k - (c0+c1)k^2 + d*k*(k-1) + e*k.
        for (int degree = 1;
                degree < observation.population();
                degree++) {
            double k = degree;
            double utility =
                    (2.0 + overlap) * k
                    - costSum * k * k
                    + triangle * k * (k - 1.0);
            if (utility > bestUtility) {
                bestUtility = utility;
                bestDegree = degree;
            }
        }
        return bestDegree;
    }
    private int unwantedNeighbor(
            int[] neighbors,
            int self,
            int target,
            int population) {
        for (int neighbor : neighbors) {
            if (!sameCohort(
                    self, neighbor, target, population)) {
                return neighbor;
            }
        }
        return -1;
    }
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int self,
            int target,
            int population,
            Memory memory,
            double time) {
        int selected = -1;
        int eligible = 0;
        for (int partner = 0;
                partner < population;
                partner++) {
            if (partner == self
                    || memory.get(partner) > time
                    || !sameCohort(
                            self, partner, target, population)
                    || contains(neighbors, partner)) {
                continue;
            }
            // Reservoir sampling avoids deterministic first-partner bias while
            // remaining far below the permitted random-query budget.
            eligible++;
            if (eligible == 1
                    || turn.randomUnit() < 1.0 / eligible) {
                selected = partner;
            }
        }
        return selected;
    }
    private boolean contains(int[] values, int target) {
        for (int value : values) {
            if (value == target) {
                return true;
            }
        }
        return false;
    }
    private boolean sameCohort(
            int first,
            int second,
            int target,
            int population) {
        if (first == second || target <= 0) {
            return false;
        }
        int preferredSize = target + 1;
        int cohortCount =
                (population + preferredSize / 2)
                        / preferredSize;
        if (cohortCount < 1) {
            cohortCount = 1;
        }
        return cohortOf(first, population, cohortCount)
                == cohortOf(second, population, cohortCount);
    }
    private int cohortOf(
            int actor,
            int population,
            int cohortCount) {
        int smallSize = population / cohortCount;
        int largeCount = population % cohortCount;
        int largeRegion =
                largeCount * (smallSize + 1);
        if (actor < largeRegion) {
            return actor / (smallSize + 1);
        }
        return largeCount
                + (actor - largeRegion) / smallSize;
    }
    // EVOLVE-BLOCK-END
}