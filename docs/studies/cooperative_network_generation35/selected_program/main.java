import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        if (usesOriginal(observation)) {
            turn.originalTurn();
            return;
        }
        int self = observation.actor();
        int population = observation.population();
        int cohortCount = optimalCohortCount(observation);
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int dropLayer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int dropPartner = unwantedNeighbor(
                dropLayer == 0 ? neighbors0 : neighbors1,
                self, cohortCount);
        if (dropPartner < 0) {
            dropLayer = 1 - dropLayer;
            dropPartner = unwantedNeighbor(
                    dropLayer == 0 ? neighbors0 : neighbors1,
                    self, cohortCount);
        }
        int addLayer =
                neighbors0.length <= neighbors1.length ? 0 : 1;
        int partner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                addLayer == 0 ? neighbors1 : neighbors0,
                self,
                population,
                cohortCount,
                memory);
        if (partner < 0) {
            addLayer = 1 - addLayer;
            partner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    addLayer == 0 ? neighbors1 : neighbors0,
                    self,
                    population,
                    cohortCount,
                    memory);
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
            dropPairedOrUnwanted(
                    turn,
                    dropPartner,
                    dropLayer,
                    self,
                    cohortCount);
        } else {
            memory.set(partner, 1.0);
            turn.drop(dropPartner, dropLayer);
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        if (usesOriginal(observation)) {
            return offer.originalAcceptance();
        }
        if (!Double.isFinite(offer.gain())) {
            return Decision.no();
        }
        int self = observation.actor();
        int proposer = offer.proposer();
        int cohortCount = optimalCohortCount(observation);
        return proposer != self
                && sameCohort(self, proposer, cohortCount)
                ? Decision.yes()
                : Decision.no();
    }
    private boolean usesOriginal(Observation observation) {
        return observation.time() < 50.0
                || observation.time() >= 93.0
                || observation.triangleBenefit() < 0.4;
    }
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int[] otherNeighbors,
            int self,
            int population,
            int cohortCount,
            Memory memory) {
        int selected = -1;
        int eligible = 0;
        // First complete relationships already present on the other layer.
        for (int partner = 0; partner < population; partner++) {
            if (partner == self
                    || !sameCohort(self, partner, cohortCount)
                    || memory.get(partner) != 0.0
                    || contains(neighbors, partner)
                    || !contains(otherNeighbors, partner)) {
                continue;
            }
            eligible++;
            if (eligible == 1
                    || turn.randomUnit() < 1.0 / eligible) {
                selected = partner;
            }
        }
        if (selected >= 0) {
            return selected;
        }
        // Otherwise start a new within-cohort relationship.
        eligible = 0;
        for (int partner = 0; partner < population; partner++) {
            if (partner == self
                    || !sameCohort(self, partner, cohortCount)
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
    private void dropPairedOrUnwanted(
            Turn turn,
            int removedPartner,
            int removedLayer,
            int self,
            int cohortCount) {
        int oppositeLayer = 1 - removedLayer;
        int[] oppositeNeighbors = turn.neighbors(oppositeLayer);
        if (!sameCohort(self, removedPartner, cohortCount)
                && contains(oppositeNeighbors, removedPartner)) {
            turn.drop(removedPartner, oppositeLayer);
            return;
        }
        dropOneUnwanted(turn, self, cohortCount);
    }
    private void dropOneUnwanted(
            Turn turn, int self, int cohortCount) {
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int partner = unwantedNeighbor(
                layer == 0 ? neighbors0 : neighbors1,
                self,
                cohortCount);
        if (partner < 0) {
            layer = 1 - layer;
            partner = unwantedNeighbor(
                    layer == 0 ? neighbors0 : neighbors1,
                    self,
                    cohortCount);
        }
        if (partner >= 0) {
            turn.drop(partner, layer);
        }
    }
    private int unwantedNeighbor(
            int[] neighbors, int self, int cohortCount) {
        for (int neighbor : neighbors) {
            if (!sameCohort(self, neighbor, cohortCount)) {
                return neighbor;
            }
        }
        return -1;
    }
    private boolean sameCohort(
            int actor, int other, int cohortCount) {
        return actor % cohortCount == other % cohortCount;
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
    // EVOLVE-BLOCK-END
}