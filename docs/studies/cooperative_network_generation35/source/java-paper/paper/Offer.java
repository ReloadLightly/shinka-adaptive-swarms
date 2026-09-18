package paper;

/** Recipient-side offer; utilityIfAccepted is the recipient's own hypothetical utility. */
public record Offer(Observation observation, int proposer, int layer, double utilityIfAccepted) {
    public double gain() { return utilityIfAccepted - observation.utility(); }
    public Decision originalAcceptance() {
        return utilityIfAccepted > observation.utility()
            ? Decision.yes() : Decision.random(observation.configuredNoise());
    }
}
