import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        if (observation.time() < 50.0
                || observation.triangleBenefit() < 0.4) {
            turn.originalTurn();
            return;
        }
        int target = targetDegree(observation);
        int self = observation.actor();
        int population = observation.population();
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
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
        int missing0 = missingPartnerCount(
                neighbors0,
                self,
                target,
                population,
                memory);
        int missing1 = missingPartnerCount(
                neighbors1,
                self,
                target,
                population,
                memory);
        int addLayer;
        if (missing0 > missing1) {
            addLayer = 0;
        } else if (missing1 > missing0) {
            addLayer = 1;
        } else {
            addLayer =
                    neighbors0.length <= neighbors1.length ? 0 : 1;
        }
        int partner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                self, target, population, memory);
        if (partner < 0) {
            addLayer = 1 - addLayer;
            partner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    self, target, population, memory);
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
            dropOneUnwanted(
                    turn, self, target, population);
        } else {
            memory.set(partner, 1.0);
            turn.drop(dropPartner, dropLayer);
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        if (observation.time() < 50.0
                || observation.triangleBenefit() < 0.4) {
            return offer.originalAcceptance();
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
        int population = observation.population();
        int bestCohortCount = population;
        double bestPopulationUtility = 0.0;
        double costSum =
                observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
        for (int cohortCount = population;
                cohortCount >= 1;
                cohortCount--) {
            int smallSize = population / cohortCount;
            int largeCount = population % cohortCount;
            int largeSize = smallSize + 1;
            double smallDegree = smallSize - 1.0;
            double largeDegree = largeSize - 1.0;
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
                    (cohortCount - largeCount)
                            * smallSize * smallUtility
                    + largeCount
                            * largeSize * largeUtility;
            if (populationUtility
                    > bestPopulationUtility) {
                bestPopulationUtility =
                        populationUtility;
                bestCohortCount = cohortCount;
            }
        }
        return bestCohortCount;
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
    private int missingPartnerCount(
            int[] neighbors,
            int self,
            int target,
            int population,
            Memory memory) {
        int count = 0;
        for (int partner = 0;
                partner < population;
                partner++) {
            if (partner != self
                    && memory.get(partner) == 0.0
                    && sameCohort(
                            self, partner, target, population)
                    && !contains(neighbors, partner)) {
                count++;
            }
        }
        return count;
    }
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int self,
            int target,
            int population,
            Memory memory) {
        int selected = -1;
        int eligible = 0;
        for (int partner = 0;
                partner < population;
                partner++) {
            if (partner != self
                    && memory.get(partner) == 0.0
                    && sameCohort(
                            self, partner, target, population)
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
    private boolean contains(
            int[] values,
            int target) {
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
        if (first == second) {
            return false;
        }
        int cohortCount = target;
        if (cohortCount < 1) {
            cohortCount = 1;
        }
        if (cohortCount > population) {
            cohortCount = population;
        }
        return cohortOf(
                first, population, cohortCount)
                == cohortOf(
                        second, population, cohortCount);
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