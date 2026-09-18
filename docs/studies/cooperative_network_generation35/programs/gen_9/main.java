import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        double triangle = observation.triangleBenefit();
        if (triangle < 2.0 * observation.cost0()
                || triangle < 2.0 * observation.cost1()) {
            turn.originalTurn();
            return;
        }
        int self = observation.actor();
        int population = observation.population();
        int layer = observation.degree0() <= observation.degree1() ? 0 : 1;
        int[] neighbors = turn.neighbors(layer);
        if (neighbors.length >= population - 1) {
            turn.noOp();
            return;
        }
        int[] otherLayer = turn.neighbors(1 - layer);
        int trianglePartner = -1;
        // Prefer a locally visible triangle closure. If possible, choose one
        // that also creates overlap across the two layers.
        for (int neighbor : neighbors) {
            int[] distanceTwo = turn.neighborsOfNeighbor(neighbor, layer);
            for (int partner : distanceTwo) {
                if (partner == self || contains(neighbors, partner)) continue;
                if (contains(otherLayer, partner)) {
                    turn.add(partner, layer);
                    return;
                }
                if (trianglePartner < 0) trianglePartner = partner;
            }
        }
        if (trianglePartner >= 0) {
            turn.add(trianglePartner, layer);
            return;
        }
        // When no triangle can be closed, reuse an existing partner from the
        // other layer to obtain spillover while continuing balanced growth.
        for (int partner : otherLayer) {
            if (partner != self && !contains(neighbors, partner)) {
                turn.add(partner, layer);
                return;
            }
        }
        // A bounded random fallback creates new bridges and prevents local
        // closure from trapping formation inside disconnected components.
        for (int draw = 0; draw < 8 * population; draw++) {
            int partner = turn.randomActor();
            if (partner == self || contains(neighbors, partner)) continue;
            turn.add(partner, layer);
            return;
        }
        turn.noOp();
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        double triangle = observation.triangleBenefit();
        if (triangle >= 2.0 * observation.cost0()
                && triangle >= 2.0 * observation.cost1()) {
            if (!Double.isFinite(offer.gain())) return Decision.no();
            return Decision.yes();
        }
        return offer.originalAcceptance();
    }
    private boolean contains(int[] values, int target) {
        for (int value : values) {
            if (value == target) return true;
        }
        return false;
    }
    // EVOLVE-BLOCK-END
}