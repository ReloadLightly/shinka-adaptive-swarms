import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    private boolean buildDense(Observation observation) {
        // Twice the largest cost in the declared panel: the rule survives either shock.
        return observation.triangleBenefit() >= 1.2
            && observation.triangleBenefit() >= 2.0 * observation.cost0()
            && observation.triangleBenefit() >= 2.0 * observation.cost1();
    }

    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        if (!buildDense(observation)) {
            turn.originalTurn();
            return;
        }

        int[] neighbors0 = turn.neighbors(0);
        int[] neighbors1 = turn.neighbors(1);
        int layer = neighbors0.length <= neighbors1.length ? 0 : 1;
        int[] neighbors = layer == 0 ? neighbors0 : neighbors1;
        int population = observation.population();
        int missing = population - 1 - neighbors.length;
        if (missing <= 0) {
            turn.noOp();
            return;
        }

        boolean[] unavailable = new boolean[population];
        unavailable[observation.actor()] = true;
        for (int neighbor : neighbors) {
            unavailable[neighbor] = true;
        }

        // Uniformly choose an absent partner without wasting addition opportunities.
        int rank = (int) (turn.randomUnit() * missing);
        for (int partner = 0; partner < population; partner++) {
            if (!unavailable[partner]) {
                if (rank == 0) {
                    turn.add(partner, layer);
                    return;
                }
                rank--;
            }
        }
        turn.noOp();
    }

    public Decision accept(Offer offer, Memory memory) {
        // Temporary bridge losses are tolerated only in the dense-construction regime.
        if (buildDense(offer.observation())) {
            return Decision.yes();
        }
        return offer.originalAcceptance();
    }
    // EVOLVE-BLOCK-END
}
