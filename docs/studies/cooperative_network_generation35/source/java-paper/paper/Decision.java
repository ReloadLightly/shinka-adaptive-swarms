package paper;

/** A recipient owns its decision, including a choice to reject a beneficial offer. */
public record Decision(boolean stochastic, double probability) {
    public Decision {
        if (!Double.isFinite(probability) || probability < 0 || probability > 1)
            throw new IllegalArgumentException("Acceptance probability outside [0,1]");
        if (!stochastic && probability != 0 && probability != 1)
            throw new IllegalArgumentException("Deterministic acceptance must be zero or one");
    }
    public static Decision yes() { return new Decision(false, 1); }
    public static Decision no() { return new Decision(false, 0); }
    public static Decision random(double probability) { return new Decision(true, probability); }
}
