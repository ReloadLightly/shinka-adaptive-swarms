package paper;

/** Local information only. No future shocks, shock membership, other costs, or global metrics. */
public record Observation(
    int actor, int population, long eventId, long activationId, long microstep,
    double time, int ownTurns, double utility, double utilityChange,
    double cost0, double cost1, double triangleBenefit, double spilloverBenefit,
    int degree0, int degree1, int triangles0, int triangles1, int overlap,
    double configuredNoise, int searchSize, String interpretation,
    long previousEventId, int previousPartner, int previousLayer, String previousOutcome
) {}
