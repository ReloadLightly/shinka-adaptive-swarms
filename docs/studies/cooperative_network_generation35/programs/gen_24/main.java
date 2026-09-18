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
        int[] unwanted = balancedUnwanted(
                neighbors0, neighbors1, first, limit);
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
            dropPairedOrUnwanted(
                    turn, dropPartner, dropLayer, first, limit);
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
    private void dropPairedOrUnwanted(
            Turn turn,
            int removedPartner,
            int removedLayer,
            int first,
            int limit) {
        int otherLayer = 1 - removedLayer;
        int[] otherNeighbors = turn.neighbors(otherLayer);
        // The displaced partner is external to this actor's cohort.
        // Its remaining edge cannot be the newly added internal edge.
        if (contains(otherNeighbors, removedPartner)) {
            turn.drop(removedPartner, otherLayer);
            return;
        }
        int[] sameNeighbors = turn.neighbors(removedLayer);
        int[] neighbors0 =
                removedLayer == 0 ? sameNeighbors : otherNeighbors;
        int[] neighbors1 =
                removedLayer == 1 ? sameNeighbors : otherNeighbors;
        int[] unwanted = balancedUnwanted(
                neighbors0, neighbors1, first, limit);
        if (unwanted[0] >= 0) {
            turn.drop(unwanted[0], unwanted[1]);
        }
    }
    private int[] balancedUnwanted(
            int[] neighbors0,
            int[] neighbors1,
            int first,
            int limit) {
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
        return new int[] {partner, layer};
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