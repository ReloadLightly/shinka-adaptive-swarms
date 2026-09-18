import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        double triangle = observation.triangleBenefit();
        if (triangle < 1.2
                || triangle < 2.0 * observation.cost0()
                || triangle < 2.0 * observation.cost1()) {
            turn.originalTurn();
            return;
        }
        int population = observation.population();
        int layer = observation.degree0() <= observation.degree1() ? 0 : 1;
        int[] neighbors = turn.neighbors(layer);
        if (neighbors.length >= population - 1) {
            turn.noOp();
            return;
        }
        // Build both layers without deleting temporary coordination ties.
        // Even near completion, sampling remains strictly bounded.
        for (int draw = 0; draw < 8 * population; draw++) {
            int partner = turn.randomActor();
            if (partner == observation.actor()) continue;
            boolean existing = false;
            for (int neighbor : neighbors) {
                if (neighbor == partner) {
                    existing = true;
                    break;
                }
            }
            if (existing) continue;
            turn.add(partner, layer);
            return;
        }
        turn.noOp();
    }
    public Decision accept(Offer offer, Memory memory) {
        Observation observation = offer.observation();
        double triangle = observation.triangleBenefit();
        if (triangle >= 1.2
                && triangle >= 2.0 * observation.cost0()
                && triangle >= 2.0 * observation.cost1()) {
            if (!Double.isFinite(offer.gain())) return Decision.no();
            return Decision.yes();
        }
        return offer.originalAcceptance();
    }
    // EVOLVE-BLOCK-END
}