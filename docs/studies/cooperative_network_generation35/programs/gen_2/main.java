import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) {
        Observation observation = turn.observation();
        int self = observation.actor();
        int bestPartner = -1;
        int bestLayer = -1;
        double bestGain = 0.0;
        for (int layer = 0; layer < 2; layer++) {
            for (int candidate : turn.neighbors(1 - layer)) {
                if (candidate != self && !linked(turn, candidate, layer)) {
                    double gain = additionGain(turn, observation, candidate, layer);
                    if (gain > bestGain) {
                        bestGain = gain;
                        bestPartner = candidate;
                        bestLayer = layer;
                    }
                }
            }
            for (int neighbor : turn.neighbors(layer)) {
                for (int candidate : turn.neighborsOfNeighbor(neighbor, layer)) {
                    if (candidate != self && !linked(turn, candidate, layer)) {
                        double gain = additionGain(turn, observation, candidate, layer);
                        if (gain > bestGain) {
                            bestGain = gain;
                            bestPartner = candidate;
                            bestLayer = layer;
                        }
                    }
                }
            }
        }
        if (bestPartner >= 0) {
            double utilityAfter = turn.inspectAdd(bestPartner, bestLayer);
            if (utilityAfter > observation.utility()) {
                turn.add(bestPartner, bestLayer);
            } else {
                turn.noOp();
            }
            return;
        }
        int bridgeLayer = -1;
        if (observation.time() < 40
                && observation.triangleBenefit() > 0.8
                && memory.get(0) == 0.0) {
            if (observation.degree0() == 1) {
                bridgeLayer = 0;
            } else if (observation.degree1() == 1) {
                bridgeLayer = 1;
            }
        }
        if (bridgeLayer >= 0) {
            int candidate = -1;
            for (int attempt = 0; attempt < observation.searchSize(); attempt++) {
                int sampled = turn.randomActor();
                if (sampled != self && !linked(turn, sampled, bridgeLayer)) {
                    candidate = sampled;
                    break;
                }
            }
            if (candidate >= 0) {
                double utilityAfter = turn.inspectAdd(candidate, bridgeLayer);
                double gain = utilityAfter - observation.utility();
                if (gain + observation.triangleBenefit() > 0.0) {
                    if (gain <= 0.0) {
                        memory.set(0, 1.0);
                    }
                    turn.add(candidate, bridgeLayer);
                    return;
                }
            }
            turn.noOp();
            return;
        }
        turn.originalTurn();
    }
    public Decision accept(Offer offer, Memory memory) {
        double gain = offer.gain();
        if (gain > 0.0) {
            return Decision.yes();
        }
        Observation observation = offer.observation();
        int degree = offer.layer() == 0
                ? observation.degree0()
                : observation.degree1();
        if (observation.time() < 40
                && observation.triangleBenefit() > 0.8
                && degree == 1
                && memory.get(0) == 0.0
                && gain + observation.triangleBenefit() > 0.0) {
            memory.set(0, 1.0);
            return Decision.yes();
        }
        return Decision.no();
    }
    private static boolean linked(Turn turn, int actor, int layer) {
        for (int neighbor : turn.neighbors(layer)) {
            if (neighbor == actor) {
                return true;
            }
        }
        return false;
    }
    private static int commonNeighbors(Turn turn, int actor, int layer) {
        int common = 0;
        for (int ownNeighbor : turn.neighbors(layer)) {
            for (int candidateNeighbor : turn.neighborsOfNeighbor(ownNeighbor, layer)) {
                if (candidateNeighbor == actor) {
                    common++;
                    break;
                }
            }
        }
        return common;
    }
    private static double additionGain(
            Turn turn, Observation observation, int actor, int layer) {
        int degree = layer == 0
                ? observation.degree0()
                : observation.degree1();
        double cost = layer == 0
                ? observation.cost0()
                : observation.cost1();
        double gain = 1.0 - cost * (2.0 * degree + 1.0);
        gain += observation.triangleBenefit()
                * commonNeighbors(turn, actor, layer);
        if (linked(turn, actor, 1 - layer)) {
            gain += observation.spilloverBenefit();
        }
        return gain;
    }
    // EVOLVE-BLOCK-END
}