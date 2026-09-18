import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        if (!constructionPhase(observation)) {
            turn.originalTurn();
            return;
        }
        int self = observation.actor();
        int population = observation.population();
        int count = bestCohortCount(observation);
        int cohort = cohortOf(self, population, count);
        int smallSize = population / count;
        int largeCount = population % count;
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
        int addPartner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                self, start, end, memory);
        if (addPartner < 0) {
            addLayer = 1 - addLayer;
            addPartner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    self, start, end, memory);
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
                memory.set(addPartner, 1.0);
            }
            return;
        }
        if (turn.rewire(
                addPartner, addLayer, dropPartner, dropLayer)) {
            // The new edge is inside the cohort, so this can only
            // remove another old edge outside it.
            dropOneUnwanted(turn, start, end);
        } else {
            memory.set(addPartner, 1.0);
            turn.drop(dropPartner, dropLayer);
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        if (!constructionPhase(observation)) {
            return offer.originalAcceptance();
        }
        if (!Double.isFinite(offer.gain())) {
            return Decision.no();
        }
        int self = observation.actor();
        int proposer = offer.proposer();
        int population = observation.population();
        int count = bestCohortCount(observation);
        return proposer != self
                && cohortOf(self, population, count)
                        == cohortOf(proposer, population, count)
                ? Decision.yes()
                : Decision.no();
    }
    private boolean constructionPhase(Observation observation) {
        return observation.time() >= 50.0
                && observation.time() < 93.0
                && observation.triangleBenefit() >= 0.4;
    }
    private int bestCohortCount(Observation observation) {
        int population = observation.population();
        double costSum =
                observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
        // Singleton cohorts have zero ideal utility. Descending
        // enumeration retains more, smaller cohorts on exact ties.
        int bestCount = population;
        double bestTotal = 0.0;
        for (int count = population - 1; count >= 1; count--) {
            int smallSize = population / count;
            int largeCount = population % count;
            int smallCount = count - largeCount;
            // This is a structural proxy using only this actor's
            // parameters, not an observation of population utility.
            double total = (double) smallCount * smallSize
                    * cliqueUtility(
                            smallSize - 1,
                            costSum, triangle, overlap);
            if (largeCount > 0) {
                total += (double) largeCount * (smallSize + 1)
                        * cliqueUtility(
                                smallSize,
                                costSum, triangle, overlap);
            }
            if (total > bestTotal) {
                bestTotal = total;
                bestCount = count;
            }
        }
        return bestCount;
    }
    private double cliqueUtility(
            int degree,
            double costSum,
            double triangle,
            double overlap) {
        double k = degree;
        return (2.0 + overlap) * k
                - costSum * k * k
                + triangle * k * (k - 1.0);
    }
    private void dropOneUnwanted(
            Turn turn,
            int start,
            int end) {
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
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
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int self,
            int start,
            int end,
            Memory memory) {
        int selected = -1;
        int eligible = 0;
        for (int partner = start; partner < end; partner++) {
            if (partner == self
                    || memory.get(partner) != 0.0
                    || contains(neighbors, partner)) {
                continue;
            }
            // Uniform reservoir sampling over eligible cohort partners.
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
        return largeCount
                + (actor - largeRegion) / smallSize;
    }
    // EVOLVE-BLOCK-END
}