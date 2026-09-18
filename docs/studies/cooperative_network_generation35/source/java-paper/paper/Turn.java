package paper;

/**
 * A capability valid only during one actor activation. Methods cannot edit another actor's
 * ties or bypass recipient consent. Every proposal counts, including a rejected proposal.
 * Candidate utility inspections and successful edits have enforced, documented budgets.
 */
public interface Turn {
    Observation observation();
    int[] neighbors(int layer);
    int[] neighborsOfNeighbor(int neighbor, int layer);
    int randomActor();
    double randomUnit();
    /** Spend one of m per-layer addition opportunities; NaN means self/existing edge. */
    double inspectAdd(int partner, int layer);
    /** Existing incident ties may be inspected, matching original exhaustive bestDrop. */
    double inspectDrop(int partner, int layer);
    /** Spend a bounded swap opportunity; returns the actor's hypothetical utility. */
    double inspectRewire(int addPartner, int addLayer, int dropPartner, int dropLayer);
    boolean add(int partner, int layer);
    void drop(int partner, int layer);
    boolean rewire(int addPartner, int addLayer, int dropPartner, int dropLayer);
    void noOp();
    /** Execute the audited reference action once; exclusive with manual edits/inspections. */
    void originalTurn();
}
