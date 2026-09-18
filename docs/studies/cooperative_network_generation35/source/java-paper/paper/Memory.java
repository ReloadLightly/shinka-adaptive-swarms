package paper;

/** Bounded persistent actor-local storage. Never shared between actors or reset at a shock. */
public final class Memory {
    private final double[] values = new double[64];
    public double get(int index) { return values[index]; }
    public void set(int index, double value) {
        if (!Double.isFinite(value) || Math.abs(value) > 1e12)
            throw new IllegalArgumentException("Memory value must be finite and bounded");
        values[index] = value;
    }
    public int size() { return values.length; }
}
