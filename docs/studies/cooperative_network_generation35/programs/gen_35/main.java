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
        int target = targetDegree(observation);
        int[] bounds = cohortBounds(
                self, observation.population(), target);
        int first = bounds[0];
        int limit = bounds[1];
        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        // Cells 0..39 record rejected partners. Cell 63 records the
        // actor's permanent transition to terminal cleanup.
        // Only observations, neighbors and private memory have been
        // read here, so originalTurn remains an exclusive valid path.
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
        if (neighbors0.length == neighbors1.length) {
            int overlapAvailable0 = 0;
            int overlapAvailable1 = 0;
            for (int candidate = first; candidate < limit; candidate++) {
                if (candidate == self
                        || memory.get(candidate) != 0.0) {
                    continue;
                }
                boolean onLayer0 = contains(neighbors0, candidate);
                boolean onLayer1 = contains(neighbors1, candidate);
                if (!onLayer0 && onLayer1) {
                    overlapAvailable0++;
                } else if (onLayer0 && !onLayer1) {
                    overlapAvailable1++;
                }
            }
            if (overlapAvailable1 > overlapAvailable0) {
                addLayer = 1;
            }
        }
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
            // The new partner is inside the cohort, so this helper
            // cannot delete the edge just added.
            dropOneUnwanted(turn, first, limit);
        } else {
            memory.set(partner, 1.0);
            // Rejection leaves the nominated old edge intact.
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
    private boolean usesOriginal(
            Observation observation, Memory memory) {
        return observation.time() < 50.0
                || observation.triangleBenefit() < 0.4
                || observation.time() >= 97.0
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
    private int targetDegree(Observation observation) {
        int bestDegree = 0;
        double bestUtility = 0.0;
        double costSum =
                observation.cost0() + observation.cost1();
        double triangle = observation.triangleBenefit();
        double overlap = observation.spilloverBenefit();
        // Preserve the parents' clique-utility arithmetic and
        // strict comparison when choosing the preferred degree.
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
        // Equivalent to the parents' balanced cohort assignment,
        // calculated once per callback using public identities.
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