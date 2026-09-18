import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        if (usesOriginal(observation, memory)) {
            turn.originalTurn();
            return;
        }
        int self = observation.actor();
        int population = observation.population();
        int cohortCount = optimalCohortCount(observation);
        int[] bounds = cohortBounds(self, population, cohortCount);
        int first = bounds[0];
        int limit = bounds[1];
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        // Cells 0..39 remember rejected partners. Cell 63 records
        // permanent completion of the late construction phase.
        if (observation.time() >= 93.0
                && !hasEligibleMissing(
                        neighbors0, neighbors1,
                        self, first, limit, memory)) {
            memory.set(63, 1.0);
            turn.originalTurn();
            return;
        }
        int dropLayer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int dropPartner = unwantedNeighbor(
                dropLayer == 0 ? neighbors0 : neighbors1,
                first, limit);
        if (dropPartner < 0) {
            dropLayer = 1 - dropLayer;
            dropPartner = unwantedNeighbor(
                    dropLayer == 0 ? neighbors0 : neighbors1,
                    first, limit);
        }
        int addLayer =
                neighbors0.length <= neighbors1.length ? 0 : 1;
        int partner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                self, first, limit, memory);
        if (partner < 0) {
            addLayer = 1 - addLayer;
            partner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    self, first, limit, memory);
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
        if (turn.rewire(
                partner, addLayer, dropPartner, dropLayer)) {
            dropOneUnwanted(turn, first, limit);
        } else {
            memory.set(partner, 1.0);
            turn.drop(dropPartner, dropLayer);
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        if (usesOriginal(observation, memory)) {
            return offer.originalAcceptance();
        }
        if (!Double.isFinite(offer.gain())) {
            return Decision.no();
        }
        int self = observation.actor();
        int cohortCount = optimalCohortCount(observation);
        int[] bounds = cohortBounds(
                self, observation.population(), cohortCount);
        int proposer = offer.proposer();
        return proposer != self
                && proposer >= bounds[0]
                && proposer < bounds[1]
                ? Decision.yes()
                : Decision.no();
    }
    private boolean usesOriginal(
            Observation observation, Memory memory) {
        return observation.time() < 50.0
                || observation.triangleBenefit() < 0.4
                || observation.time() >= 95.0
                || (observation.time() >= 93.0
                    && memory.get(63) > 0.0);
    }
    private boolean hasEligibleMissing(
            int[] neighbors0,
            int[] neighbors1,
            int self,
            int first,
            int limit,
            Memory memory) {
        for (int partner = first; partner < limit; partner++) {
            if (partner == self || memory.get(partner) != 0.0) {
                continue;
            }
            if (!contains(neighbors0, partner)
                    || !contains(neighbors1, partner)) {
                return true;
            }
        }
        return false;
    }
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int self,
            int first,
            int limit,
            Memory memory) {
        int selected = -1;
        int eligible = 0;
        for (int partner = first; partner < limit; partner++) {
            if (partner == self
                    || memory.get(partner) != 0.0
                    || contains(neighbors, partner)) {
                continue;
            }
            eligible++;
            if (eligible == 1
                    || turn.randomUnit() < 1.0 / eligible) {
                selected = partner;
            }
        }
        return selected;
    }
    private void dropOneUnwanted(
            Turn turn, int first, int limit) {
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int partner = unwantedNeighbor(
                layer == 0 ? neighbors0 : neighbors1,
                first, limit);
        if (partner < 0) {
            layer = 1 - layer;
            partner = unwantedNeighbor(
                    layer == 0 ? neighbors0 : neighbors1,
                    first, limit);
        }
        if (partner >= 0) {
            turn.drop(partner, layer);
        }
    }
    private int unwantedNeighbor(
            int[] neighbors, int first, int limit) {
        for (int neighbor : neighbors) {
            if (neighbor < first || neighbor >= limit) {
                return neighbor;
            }
        }
        return -1;
    }
    private boolean contains(int[] values, int target) {
        for (int value : values) {
            if (value == target) {
                return true;
            }
        }
        return false;
    }
    private int optimalCohortCount(Observation observation) {
        int population = observation.population();
        int bestCount = population;
        double bestPopulationUtility = 0.0;
        double costSum =
                observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
        for (int cohortCount = population - 1;
                cohortCount >= 1;
                cohortCount--) {
            int smallSize = population / cohortCount;
            int largeCount = population % cohortCount;
            int smallCount = cohortCount - largeCount;
            double smallDegree = smallSize - 1.0;
            double largeDegree = smallSize;
            double smallUtility =
                    (triangle - costSum)
                            * smallDegree * smallDegree
                    + (2.0 + overlap - triangle)
                            * smallDegree;
            double largeUtility =
                    (triangle - costSum)
                            * largeDegree * largeDegree
                    + (2.0 + overlap - triangle)
                            * largeDegree;
            double populationUtility =
                    smallCount * smallSize * smallUtility
                    + largeCount * (smallSize + 1)
                            * largeUtility;
            if (populationUtility > bestPopulationUtility) {
                bestPopulationUtility = populationUtility;
                bestCount = cohortCount;
            }
        }
        return bestCount;
    }
    private int[] cohortBounds(
            int actor, int population, int cohortCount) {
        if (cohortCount >= population) {
            return new int[] {actor, actor + 1};
        }
        int smallSize = population / cohortCount;
        int largeCount = population % cohortCount;
        int largeRegion = largeCount * (smallSize + 1);
        if (actor < largeRegion) {
            int size = smallSize + 1;
            int first = (actor / size) * size;
            return new int[] {first, first + size};
        }
        int first = largeRegion
                + ((actor - largeRegion) / smallSize) * smallSize;
        return new int[] {first, first + smallSize};
    }
    // EVOLVE-BLOCK-END
}