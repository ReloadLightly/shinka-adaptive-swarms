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
        int target = targetDegree(observation);
        int[] bounds = cohortBounds(
                self, observation.population(), target);
        int first = bounds[0];
        int limit = bounds[1];
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int[] unwanted = rankedUnwanted(
                neighbors0, neighbors1, observation, first, limit);
        int dropPartner = unwanted[0];
        int dropLayer = unwanted[1];
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
            dropOneUnwanted(turn, observation, first, limit);
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
        int target = targetDegree(observation);
        int[] bounds = cohortBounds(
                self, observation.population(), target);
        int proposer = offer.proposer();
        return proposer != self
                && proposer >= bounds[0]
                && proposer < bounds[1]
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
            Turn turn,
            Observation observation,
            int first,
            int limit) {
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int[] unwanted = rankedUnwanted(
                neighbors0, neighbors1, observation, first, limit);
        if (unwanted[0] >= 0) {
            turn.drop(unwanted[0], unwanted[1]);
        }
    }
    private int[] rankedUnwanted(
            int[] neighbors0,
            int[] neighbors1,
            Observation observation,
            int first,
            int limit) {
        int bestPartner = -1;
        int bestLayer = 0;
        double bestRelief = 0.0;
        for (int layer = 0; layer < 2; layer++) {
            int[] neighbors = layer == 0 ? neighbors0 : neighbors1;
            int[] otherNeighbors =
                    layer == 0 ? neighbors1 : neighbors0;
            double cost =
                    layer == 0 ? observation.cost0() : observation.cost1();
            double degreeRelief =
                    cost * (2.0 * neighbors.length - 1.0) - 1.0;
            for (int neighbor : neighbors) {
                if (neighbor >= first && neighbor < limit) {
                    continue;
                }
                double relief = degreeRelief;
                if (contains(otherNeighbors, neighbor)) {
                    relief -= observation.spilloverBenefit();
                }
                if (bestPartner < 0 || relief > bestRelief) {
                    bestPartner = neighbor;
                    bestLayer = layer;
                    bestRelief = relief;
                }
            }
        }
        return new int[] {bestPartner, bestLayer};
    }
    private boolean contains(int[] values, int target) {
        for (int value : values) {
            if (value == target) {
                return true;
            }
        }
        return false;
    }
    private int targetDegree(Observation observation) {
        int bestDegree = 0;
        double bestUtility = 0.0;
        double costSum =
                observation.cost0() + observation.cost1();
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
    private int[] cohortBounds(
            int actor, int population, int target) {
        if (target <= 0) {
            return new int[] {actor, actor + 1};
        }
        int preferredSize = target + 1;
        int cohortCount =
                (population + preferredSize / 2) / preferredSize;
        if (cohortCount < 1) {
            cohortCount = 1;
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