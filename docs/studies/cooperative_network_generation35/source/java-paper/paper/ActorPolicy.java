package paper;

/** One fresh policy instance and one private Memory per actor for its complete life. */
public interface ActorPolicy {
    void act(Turn turn, Memory memory);
    Decision accept(Offer offer, Memory memory);
}
