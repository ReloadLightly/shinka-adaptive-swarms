import paper.*;

/** Initial v2 candidate: the original behavior, using the case's configured fixed noise. */
public final class CandidatePolicy implements ActorPolicy {
    public void act(Turn turn, Memory memory) { turn.originalTurn(); }
    public Decision accept(Offer offer, Memory memory) { return offer.originalAcceptance(); }
}
