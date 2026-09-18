import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        double time = observation.time();
        if (time < 50.0
                || time >= 95.0
                || observation.triangleBenefit() < 0.4) {
            turn.originalTurn();
            return;
        }
        int self = observation.actor();
        int population = observation.population();
        int cohortCount = bestCohortCount(observation);
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int addLayer =
                neighbors0.length <= neighbors1.length ? 0 : 1;
        int addPartner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                self,
                cohortCount,
                population,
                memory,
                observation.ownTurns());
        if (addPartner < 0) {
            addLayer = 1 - addLayer;
            addPartner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    self,
                    cohortCount,
                    population,
                    memory,
                    observation.ownTurns());
        }
        /*
         * The final construction window only fills remaining
         * cohort links. It does not remove links whose benefits
         * may not be recovered before the policy handoff.
         */
        if (time >= 90.0) {
            if (addPartner >= 0) {
                if (!turn.add(addPartner, addLayer)) {
                    deferPartner(
                            memory,
                            addPartner,
                            observation.ownTurns());
                }
            } else {
                turn.noOp();
            }
            return;
        }
        int dropLayer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int dropPartner = unwantedNeighbor(
                dropLayer == 0 ? neighbors0 : neighbors1,
                self,
                cohortCount,
                population);
        if (dropPartner < 0) {
            dropLayer = 1 - dropLayer;
            dropPartner = unwantedNeighbor(
                    dropLayer == 0 ? neighbors0 : neighbors1,
                    self,
                    cohortCount,
                    population);
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
                deferPartner(
                        memory,
                        addPartner,
                        observation.ownTurns());
            }
            return;
        }
        if (turn.rewire(
                addPartner,
                addLayer,
                dropPartner,
                dropLayer)) {
            dropOneUnwanted(
                    turn,
                    self,
                    cohortCount,
                    population);
        } else {
            deferPartner(
                    memory,
                    addPartner,
                    observation.ownTurns());
            turn.drop(dropPartner, dropLayer);
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        double time = observation.time();
        if (time < 50.0
                || time >= 95.0
                || observation.triangleBenefit() < 0.4) {
            return offer.originalAcceptance();
        }
        int cohortCount = bestCohortCount(observation);
        return sameCohort(
                observation.actor(),
                offer.proposer(),
                cohortCount,
                observation.population())
                ? Decision.yes()
                : Decision.no();
    }
    private void deferPartner(
            Memory memory,
            int partner,
            double ownTurns) {
        memory.set(partner, ownTurns + 3.0);
    }
    private void dropOneUnwanted(
            Turn turn,
            int self,
            int cohortCount,
            int population) {
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int partner = unwantedNeighbor(
                layer == 0 ? neighbors0 : neighbors1,
                self,
                cohortCount,
                population);
        if (partner < 0) {
            layer = 1 - layer;
            partner = unwantedNeighbor(
                    layer == 0 ? neighbors0 : neighbors1,
                    self,
                    cohortCount,
                    population);
        }
        if (partner >= 0) {
            turn.drop(partner, layer);
        }
    }
    private int bestCohortCount(Observation observation) {
        int population = observation.population();
        int bestCount = population;
        double bestPopulationUtility = 0.0;
        double costSum =
                observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
        /*
         * Counts are visited from many cohorts to few cohorts.
         * Strict replacement therefore favors smaller groups
         * whenever population utilities tie.
         */
        for (int count = population; count >= 1; count--) {
            int smallSize = population / count;
            int largeCount = population % count;
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
                    (count - largeCount)
                            * smallSize * smallUtility
                    + largeCount
                            * largeSize * largeUtility;
            if (populationUtility > bestPopulationUtility) {
                bestPopulationUtility = populationUtility;
                bestCount = count;
            }
        }
        return bestCount;
    }
    private int unwantedNeighbor(
            int[] neighbors,
            int self,
            int cohortCount,
            int population) {
        for (int neighbor : neighbors) {
            if (!sameCohort(
                    self,
                    neighbor,
                    cohortCount,
                    population)) {
                return neighbor;
            }
        }
        return -1;
    }
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int self,
            int cohortCount,
            int population,
            Memory memory,
            double ownTurns) {
        int selected = -1;
        int eligible = 0;
        for (int partner = 0;
                partner < population;
                partner++) {
            if (partner != self
                    && memory.get(partner) <= ownTurns
                    && sameCohort(
                            self,
                            partner,
                            cohortCount,
                            population)
                    && !contains(neighbors, partner)) {
                eligible++;
                if (eligible == 1
                        || turn.randomUnit()
                                < 1.0 / eligible) {
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
            int cohortCount,
            int population) {
        if (first == second) {
            return false;
        }
        int count = cohortCount;
        if (count < 1) {
            count = 1;
        }
        if (count > population) {
            count = population;
        }
        return cohortOf(first, population, count)
                == cohortOf(second, population, count);
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