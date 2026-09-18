import paper.*;

/** Unfrozen extension seed: the original behavior, using the configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    // EVOLVE-BLOCK-START
    public void act(Turn turn, Memory memory) { turn.originalTurn(); }
    public Decision accept(Offer offer, Memory memory) { return offer.originalAcceptance(); }
    // EVOLVE-BLOCK-END
}
