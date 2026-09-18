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
        int cohortCount = bestCohortCount(observation);
        int cohort = cohortOf(self, population, cohortCount);
        int smallSize = population / cohortCount;
        int largeCount = population % cohortCount;
        int first = cohort * smallSize
                + (cohort < largeCount ? cohort : largeCount);
        int limit = first + smallSize
                + (cohort < largeCount ? 1 : 0);
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int dropLayer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int dropPartner = unwantedNeighbor(
                dropLayer == 0 ? neighbors0 : neighbors1,
                first,
                limit);
        if (dropPartner < 0) {
            dropLayer = 1 - dropLayer;
            dropPartner = unwantedNeighbor(
                    dropLayer == 0 ? neighbors0 : neighbors1,
                    first,
                    limit);
        }
        int addLayer =
                neighbors0.length <= neighbors1.length ? 0 : 1;
        int addPartner = missingPartner(
                turn,
                addLayer == 0 ? neighbors0 : neighbors1,
                self,
                first,
                limit,
                memory);
        if (addPartner < 0) {
            addLayer = 1 - addLayer;
            addPartner = missingPartner(
                    turn,
                    addLayer == 0 ? neighbors0 : neighbors1,
                    self,
                    first,
                    limit,
                    memory);
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
                addPartner,
                addLayer,
                dropPartner,
                dropLayer)) {
            dropOneUnwanted(turn, first, limit);
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
        int self = observation.actor();
        int proposer = offer.proposer();
        int population = observation.population();
        if (proposer < 0
                || proposer >= population
                || proposer == self) {
            return Decision.no();
        }
        int cohortCount = bestCohortCount(observation);
        return cohortOf(self, population, cohortCount)
                == cohortOf(proposer, population, cohortCount)
                ? Decision.yes()
                : Decision.no();
    }
    private boolean constructionPhase(Observation observation) {
        double time = observation.time();
        return time >= 50.0
                && time < 95.0
                && observation.triangleBenefit() >= 0.4;
    }
    private int bestCohortCount(Observation observation) {
        int population = observation.population();
        int bestCount = population;
        double bestPopulationUtility = 0.0;
        double costSum =
                observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
        double quadratic = triangle - costSum;
        double linear = 2.0 + overlap - triangle;
        // Strict improvement favors more cohorts on exact ties.
        for (int count = population; count >= 1; count--) {
            int smallSize = population / count;
            int largeCount = population % count;
            int largeSize = smallSize + 1;
            double smallDegree = smallSize - 1.0;
            double largeDegree = largeSize - 1.0;
            double smallUtility =
                    quadratic * smallDegree * smallDegree
                    + linear * smallDegree;
            double largeUtility =
                    quadratic * largeDegree * largeDegree
                    + linear * largeDegree;
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
    private int missingPartner(
            Turn turn,
            int[] neighbors,
            int self,
            int first,
            int limit,
            Memory memory) {
        int selected = -1;
        int eligible = 0;
        // Ascending IDs preserve reservoir-sampling order.
        for (int partner = first; partner < limit; partner++) {
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
            int first,
            int limit) {
        for (int neighbor : neighbors) {
            if (neighbor < first || neighbor >= limit) {
                return neighbor;
            }
        }
        return -1;
    }
    private void dropOneUnwanted(
            Turn turn,
            int first,
            int limit) {
        // Refresh after the accepted rewire.
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer =
                neighbors0.length >= neighbors1.length ? 0 : 1;
        int partner = unwantedNeighbor(
                layer == 0 ? neighbors0 : neighbors1,
                first,
                limit);
        if (partner < 0) {
            layer = 1 - layer;
            partner = unwantedNeighbor(
                    layer == 0 ? neighbors0 : neighbors1,
                    first,
                    limit);
        }
        // The newly added within-cohort edge cannot be selected.
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