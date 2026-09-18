import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        int cohortCount = constructionCohorts(observation);
        if (cohortCount == 0) {
            turn.originalTurn();
            return;
        }
        int self = observation.actor();
        int population = observation.population();
        int cohort = cohortOf(self, population, cohortCount);
        int smallSize = population / cohortCount;
        int largeCount = population % cohortCount;
        int start = cohort * smallSize
                + (cohort < largeCount ? cohort : largeCount);
        int end = start + smallSize
                + (cohort < largeCount ? 1 : 0);
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int dropLayer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int dropPartner = unwantedNeighbor(
                dropLayer == 0 ? neighbors0 : neighbors1,
                start, end);
        if (dropPartner < 0) {
            dropLayer = 1 - dropLayer;
            dropPartner = unwantedNeighbor(
                    dropLayer == 0 ? neighbors0 : neighbors1,
                    start, end);
        }
        int addLayer =
                neighbors0.length <= neighbors1.length ? 0 : 1;
        int partner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                self, start, end, memory);
        if (partner < 0) {
            addLayer = 1 - addLayer;
            partner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    self, start, end, memory);
        }
        if (partner < 0) {
            if (dropPartner >= 0) {
                turn.drop(dropPartner, dropLayer);
            } else {
                turn.noOp();
            }
            return;
        }
        if (dropPartner < 0) {
            if (!turn.add(partner, addLayer)) {
                memory.set(partner, 1.0);
            }
            return;
        }
        if (turn.rewire(partner, addLayer, dropPartner, dropLayer)) {
            dropOneUnwanted(turn, start, end);
        } else {
            memory.set(partner, 1.0);
            turn.drop(dropPartner, dropLayer);
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        int cohortCount = constructionCohorts(observation);
        if (cohortCount == 0) {
            return offer.originalAcceptance();
        }
        int population = observation.population();
        return cohortOf(observation.actor(), population, cohortCount)
                == cohortOf(offer.proposer(), population, cohortCount)
                ? Decision.yes()
                : Decision.no();
    }
    private int constructionCohorts(Observation observation) {
        double triangle = observation.triangleBenefit();
        // Strong incentives: construct one population-wide cohort
        // throughout formation and recovery, on both layers.
        if (triangle >= 1.2
                && triangle >= 2.0 * observation.cost0()
                && triangle >= 2.0 * observation.cost1()) {
            return 1;
        }
        // Otherwise preserve the parent's construction/release window.
        if (observation.time() < 50.0
                || observation.time() >= 95.0
                || triangle < 0.4) {
            return 0;
        }
        int preferredSize = targetDegree(observation) + 1;
        int cohortCount =
                (observation.population() + preferredSize / 2)
                / preferredSize;
        return cohortCount < 1 ? 1 : cohortCount;
    }
    private int targetDegree(Observation observation) {
        int bestDegree = 0;
        double bestUtility = 0.0;
        double costSum = observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
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
    private int cohortOf(
            int actor,
            int population,
            int cohortCount) {
        int smallSize = population / cohortCount;
        int largeCount = population % cohortCount;
        int largeRegion = largeCount * (smallSize + 1);
        if (actor < largeRegion) {
            return actor / (smallSize + 1);
        }
        return largeCount + (actor - largeRegion) / smallSize;
    }
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int self,
            int start,
            int end,
            Memory memory) {
        int selected = -1;
        int eligible = 0;
        // Contiguous cohort bounds avoid scanning unrelated actors.
        for (int partner = start; partner < end; partner++) {
            if (partner != self
                    && memory.get(partner) == 0.0
                    && !contains(neighbors, partner)) {
                eligible++;
                if (eligible == 1
                        || turn.randomUnit() < 1.0 / eligible) {
                    selected = partner;
                }
            }
        }
        return selected;
    }
    private int unwantedNeighbor(
            int[] neighbors,
            int start,
            int end) {
        for (int neighbor : neighbors) {
            if (neighbor < start || neighbor >= end) {
                return neighbor;
            }
        }
        return -1;
    }
    private void dropOneUnwanted(
            Turn turn,
            int start,
            int end) {
        // Refresh after the accepted rewire. The new within-cohort
        // edge cannot qualify for this additional deletion.
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer = neighbors0.length >= neighbors1.length ? 0 : 1;
        int partner = unwantedNeighbor(
                layer == 0 ? neighbors0 : neighbors1,
                start, end);
        if (partner < 0) {
            layer = 1 - layer;
            partner = unwantedNeighbor(
                    layer == 0 ? neighbors0 : neighbors1,
                    start, end);
        }
        if (partner >= 0) {
            turn.drop(partner, layer);
        }
    }
    private boolean contains(int[] values, int target) {
        for (int value : values) {
            if (value == target) {
                return true;
            }
        }
        return false;
    }
    // EVOLVE-BLOCK-END
}