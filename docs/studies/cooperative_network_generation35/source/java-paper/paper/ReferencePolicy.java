package paper;

/** Original behavior through the same all-actor action and acceptance interfaces. */
public class ReferencePolicy implements ActorPolicy {
    public void act(Turn turn, Memory memory) { turn.originalTurn(); }
    public Decision accept(Offer offer, Memory memory) { return offer.originalAcceptance(); }
}
