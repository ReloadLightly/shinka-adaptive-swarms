import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        // Retain the well-tested source behavior when neither local
        // coordination mechanism offers a substantial opportunity.
        if (observation.triangleBenefit() < 1.0
                && observation.spilloverBenefit() < 0.2) {
            turn.originalTurn();
            return;
        }
        final int self = observation.actor();
        final int m = observation.searchSize();
        final double current = observation.utility();
        final double triangle = observation.triangleBenefit();
        int bestPartner = -1;
        int bestLayer = -1;
        double bestValue = current;
        int bridgePartner = -1;
        int bridgeLayer = -1;
        double bridgeValue = -1.0e300;
        for (int layer = 0; layer < 2; layer++) {
            int[] own = turn.neighbors(layer);
            int[] otherLayer = turn.neighbors(1 - layer);
            int[] inspected = new int[m];
            int used = 0;
            // Existing partners on the other layer are high-value overlap
            // candidates and require no inference about global topology.
            for (int partner : otherLayer) {
                if (used >= m) break;
                if (partner == self || contains(own, partner)
                        || contains(inspected, used, partner)) continue;
                double value = turn.inspectAdd(partner, layer);
                inspected[used++] = partner;
                if (Double.isFinite(value) && value > bestValue) {
                    bestValue = value;
                    bestPartner = partner;
                    bestLayer = layer;
                }
            }
            // Prefer observable distance-two actors, because adding them
            // closes at least one triangle on this layer.
            for (int neighbor : own) {
                if (used >= m) break;
                int[] distanceTwo =
                        turn.neighborsOfNeighbor(neighbor, layer);
                for (int partner : distanceTwo) {
                    if (used >= m) break;
                    if (partner == self || contains(own, partner)
                            || contains(inspected, used, partner)) continue;
                    double value = turn.inspectAdd(partner, layer);
                    inspected[used++] = partner;
                    if (Double.isFinite(value) && value > bestValue) {
                        bestValue = value;
                        bestPartner = partner;
                        bestLayer = layer;
                    }
                }
            }
            int degree = layer == 0
                    ? observation.degree0() : observation.degree1();
            double cost = layer == 0
                    ? observation.cost0() : observation.cost1();
            // Fill the remaining addition budget with bounded exploration.
            // A degree-one actor may retain one temporary bridge only when
            // one subsequent triangle would more than recover its exact loss.
            for (int draw = 0; used < m && draw < 4 * m; draw++) {
                int partner = turn.randomActor();
                if (partner == self || contains(own, partner)
                        || contains(inspected, used, partner)) continue;
                double value = turn.inspectAdd(partner, layer);
                inspected[used++] = partner;
                if (!Double.isFinite(value)) continue;
                if (value > bestValue) {
                    bestValue = value;
                    bestPartner = partner;
                    bestLayer = layer;
                } else if (degree == 1
                        && observation.time() < 92.0
                        && value < current
                        && triangle > 3.0 * cost - 1.0 + 0.05
                        && value + triangle > current + 0.02
                        && value > bridgeValue) {
                    bridgeValue = value;
                    bridgePartner = partner;
                    bridgeLayer = layer;
                }
            }
        }
        if (bestPartner >= 0) {
            turn.add(bestPartner, bestLayer);
            return;
        }
        if (bridgePartner >= 0) {
            if (turn.add(bridgePartner, bridgeLayer)) {
                // Protect both edges of the nascent path on this layer long
                // enough for an endpoint to observe and close the triangle.
                memory.set(bridgeLayer, observation.time() + 8.0);
            }
            return;
        }
        int dropPartner = -1;
        int dropLayer = -1;
        double dropValue = current;
        for (int layer = 0; layer < 2; layer++) {
            if (memory.get(layer) > observation.time()) continue;
            int[] own = turn.neighbors(layer);
            for (int partner : own) {
                double value = turn.inspectDrop(partner, layer);
                if (Double.isFinite(value) && value > dropValue) {
                    dropValue = value;
                    dropPartner = partner;
                    dropLayer = layer;
                }
            }
        }
        if (dropPartner >= 0) {
            turn.drop(dropPartner, dropLayer);
        } else {
            turn.noOp();
        }
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        double gain = offer.gain();
        if (!Double.isFinite(gain)) return Decision.no();
        if (gain > 0.0) return Decision.yes();
        int layer = offer.layer();
        int degree = layer == 0
                ? observation.degree0() : observation.degree1();
        double cost = layer == 0
                ? observation.cost0() : observation.cost1();
        double triangle = observation.triangleBenefit();
        if (gain < 0.0
                && degree == 1
                && observation.time() < 92.0
                && triangle > 3.0 * cost - 1.0 + 0.05
                && gain + triangle > 0.02) {
            memory.set(layer, observation.time() + 8.0);
            return Decision.yes();
        }
        return Decision.no();
    }
    private boolean contains(int[] values, int target) {
        for (int value : values) {
            if (value == target) return true;
        }
        return false;
    }
    private boolean contains(int[] values, int length, int target) {
        for (int index = 0; index < length; index++) {
            if (values[index] == target) return true;
        }
        return false;
    }
    // EVOLVE-BLOCK-END
}