package agents;

import paper.*;
import java.util.*;
import java.util.function.Supplier;
import sim.util.Double2D;

/** Separate full-life model. Upstream adjacency, networks and utility oracle remain intact. */
public final class PaperSimulation extends AgentsSimulation {
    public enum Interpretation { SOURCE_EXECUTABLE, PAPER_DIRECTED }
    final Interpretation interpretation;
    final ActorPolicy[] policies;
    final Memory[] memories;
    final int[][] degrees, triangles;
    final int[] overlaps, turns, previousPartner, previousLayer;
    final long[] previousEvent;
    final String[] previousOutcome;
    final double[] previousUtility;
    final boolean[] hasObserved, shocked;
    final List<Map<String,Object>> events = new ArrayList<>();
    Map<String,Object> failedReferenceProposal;
    final boolean recordEvents, smartSearch;
    long microstep, eventId, activationId;
    int additions, deletions, offers, acceptances, rejections, policyCalls;
    int actorInEpisode = -1, episodeRemaining;
    boolean episodeExplores;
    private Capability active;
    private boolean recipientCallback;

    public PaperSimulation(long seed, Interpretation interpretation, Supplier<ActorPolicy> factory,
                           boolean recordEvents, boolean smartSearch) {
        super(seed);
        this.interpretation = interpretation;
        this.recordEvents = recordEvents;
        this.smartSearch = smartSearch;
        policies = new ActorPolicy[NUM_PLAYERS]; memories = new Memory[NUM_PLAYERS];
        degrees = new int[2][NUM_PLAYERS]; triangles = new int[2][NUM_PLAYERS];
        overlaps = new int[NUM_PLAYERS]; turns = new int[NUM_PLAYERS];
        previousPartner = new int[NUM_PLAYERS]; previousLayer = new int[NUM_PLAYERS];
        previousEvent = new long[NUM_PLAYERS]; previousOutcome = new String[NUM_PLAYERS];
        previousUtility = new double[NUM_PLAYERS]; hasObserved = new boolean[NUM_PLAYERS];
        shocked = new boolean[NUM_PLAYERS];
        Arrays.fill(previousPartner, -1); Arrays.fill(previousLayer, -1);
        Arrays.fill(previousOutcome, "none");
        for (int i=0; i<NUM_PLAYERS; i++) { policies[i]=factory.get(); memories[i]=new Memory(); }
    }

    @Override public void createAgents() {
        agentList = new Agent[NUM_PLAYERS];
        for (int i=0; i<NUM_PLAYERS; i++) {
            Agent a = new PaperAgent(i, tie_cost_1, tie_cost_2);
            agentList[i] = a;
            agentsSpace1.setObjectLocation(a, new Double2D(i,0));
            agentsSpace2.setObjectLocation(a, new Double2D(i,0));
            for (int layer=0; layer<3; layer++) links[layer].addNode(a);
        }
        // Full-horizon driver owns time. Never run the inherited scheduled controller too.
        gpa = new GamePlayerAgent();
    }

    private double utilityCounts(Agent a, int k0, int k1, int z0, int z1, int overlap) {
        // Identical expression and operation order to unchanged AgentsSimulation.utility.
        double u=0;
        u += tie_benefit_1*(double)k0 + tie_benefit_2*(double)k1;
        u += a.tie_cost_1*((double)k0*k0) + a.tie_cost_2*((double)k1*k1);
        u += triangle_payoff_1*(double)z0 + triangle_payoff_2*(double)z1;
        u += spillover_payoff*(double)overlap;
        return u;
    }
    @Override public double currentUtility(Agent a) {
        int i=a.index;
        return utilityCounts(a,degrees[0][i],degrees[1][i],triangles[0][i],triangles[1][i],overlaps[i]);
    }
    int common(int a,int b,int layer) {
        int count=0;
        for(int i=0;i<NUM_PLAYERS;i++) if(coplayerMatrix[layer][a][i]&&coplayerMatrix[layer][b][i]) count++;
        return count;
    }
    @Override public void tie_form(Agent a,Agent b,int layer) {
        int i=a.index,j=b.index;
        if(i==j) throw new IllegalArgumentException("Self tie");
        if(coplayerMatrix[layer][i][j]) return;
        for(int k=0;k<NUM_PLAYERS;k++) if(coplayerMatrix[layer][i][k]&&coplayerMatrix[layer][j][k]) {
            triangles[layer][i]++;triangles[layer][j]++;triangles[layer][k]++;
        }
        if(coplayerMatrix[1-layer][i][j]) { overlaps[i]++;overlaps[j]++; }
        degrees[layer][i]++;degrees[layer][j]++;
        super.tie_form(a,b,layer);additions++;
    }
    @Override public void tie_delete(Agent a,Agent b,int layer) {
        int i=a.index,j=b.index;
        if(!coplayerMatrix[layer][i][j]) return;
        for(int k=0;k<NUM_PLAYERS;k++) if(coplayerMatrix[layer][i][k]&&coplayerMatrix[layer][j][k]) {
            triangles[layer][i]--;triangles[layer][j]--;triangles[layer][k]--;
        }
        if(coplayerMatrix[1-layer][i][j]) { overlaps[i]--;overlaps[j]--; }
        degrees[layer][i]--;degrees[layer][j]--;
        super.tie_delete(a,b,layer);deletions++;
        if(active!=null) {
            long id=++eventId;
            outcome(i,j,layer,"dropped",id);outcome(j,i,layer,"tie_dropped_by_partner",id);
        }
    }
    double hypothetical(Agent a, int add,int al,int drop,int dl) {
        int i=a.index;
        int[] k={degrees[0][i],degrees[1][i]}, z={triangles[0][i],triangles[1][i]};
        int overlap=overlaps[i];
        boolean adding=add>=0&&!coplayerMatrix[al][i][add];
        if(adding) { k[al]++;z[al]+=common(i,add,al);if(coplayerMatrix[1-al][i][add])overlap++; }
        if(drop>=0&&(coplayerMatrix[dl][i][drop]||(adding&&drop==add&&dl==al))) {
            k[dl]--;
            int lost=common(i,drop,dl);
            if(adding&&al==dl&&drop!=add&&coplayerMatrix[dl][add][drop])lost++;
            z[dl]-=lost;
            if(coplayerMatrix[1-dl][i][drop]||(adding&&add==drop&&al==1-dl))overlap--;
        }
        return utilityCounts(a,k[0],k[1],z[0],z[1],overlap);
    }
    @Override public double utilityIfAdded(Agent a,Agent b,int layer) {return hypothetical(a,b.index,layer,-1,0);}
    @Override public double utilityIfAddDrop(Agent a,Agent b,Agent d,int al,int dl) {return hypothetical(a,b.index,al,d.index,dl);}
    @Override public double[][] addUtilities(Agent a) {
        double[][] values=new double[2][NUM_PLAYERS];
        for(int l=0;l<2;l++)for(int j=0;j<NUM_PLAYERS;j++) values[l][j]=j==a.index||coplayerMatrix[l][a.index][j]?-9999:utilityIfAdded(a,agentList[j],l);
        return values;
    }
    @Override public double[][] lossUtilities(Agent a) {
        double[][] values=new double[2][NUM_PLAYERS];
        for(int l=0;l<2;l++)for(int j=0;j<NUM_PLAYERS;j++) values[l][j]=j==a.index||!coplayerMatrix[l][a.index][j]?-9999:hypothetical(a,-1,0,j,l);
        return values;
    }

    Observation observe(int i,long id) {
        Agent a=agentList[i];double u=currentUtility(a);
        Observation o=new Observation(i,NUM_PLAYERS,id,activationId,microstep,(double)microstep/NUM_PLAYERS,
            turns[i],u,hasObserved[i]?u-previousUtility[i]:0,-a.tie_cost_1,-a.tie_cost_2,
            triangle_payoff_1,spillover_payoff,degrees[0][i],degrees[1][i],triangles[0][i],triangles[1][i],overlaps[i],
            noise,searchSize,interpretation.name(),previousEvent[i],previousPartner[i],previousLayer[i],previousOutcome[i]);
        previousUtility[i]=u;hasObserved[i]=true;
        return o;
    }
    void outcome(int actor,int partner,int layer,String value,long event) {
        previousEvent[actor]=event;previousPartner[actor]=partner;previousLayer[actor]=layer;previousOutcome[actor]=value;
    }
    void record(String type,Observation o,int partner,int layer,Object result) {
        if(!recordEvents)return;
        Map<String,Object> row=new LinkedHashMap<>();
        row.put("kind",type);row.put("observation",PaperRunner.observationMap(o));
        row.put("partner",partner);row.put("layer",layer);row.put("result",result);events.add(row);
    }
    boolean offer(Agent a,Agent b,int layer) {
        if(a.index==b.index||coplayerMatrix[layer][a.index][b.index])throw new IllegalArgumentException("Invalid proposal: proposer="+a.index+", recipient="+b.index+", layer="+layer+", microstep="+microstep+", interpretation="+interpretation+", smart="+smartSearch);
        if(active!=null) active.countProposal();
        offers++;long id=++eventId;
        Observation o=observe(b.index,id);
        Decision decision;
        recipientCallback=true;
        try { decision=policies[b.index].accept(new Offer(o,a.index,layer,utilityIfAdded(b,a,layer)),memories[b.index]); }
        finally { recipientCallback=false; }
        policyCalls++;
        if(decision==null)throw new IllegalArgumentException("Null acceptance decision");
        boolean yes=decision.stochastic()?random.nextBoolean(decision.probability()):decision.probability()==1;
        if(yes){tie_form(a,b,layer);acceptances++;if(active!=null){active.addedPartner=b.index;active.addedLayer=layer;}}else rejections++;
        long resultId=++eventId;
        outcome(a.index,b.index,layer,yes?"proposal_accepted":"proposal_rejected",resultId);
        outcome(b.index,a.index,layer,yes?"offer_accepted":"offer_rejected",resultId);
        record("offer",o,a.index,layer,Map.of("accepted",yes,"result_event_id",resultId,"utility_if_accepted",utilityCountsForOffer(o,a,b,layer,yes)));
        return yes;
    }
    private double utilityCountsForOffer(Observation o,Agent a,Agent b,int layer,boolean accepted) {
        return accepted?currentUtility(b):utilityIfAdded(b,a,layer);
    }

    void act(int actor,Boolean forcedExploration) {
        activationId++;turns[actor]++;
        Observation o=observe(actor,++eventId);
        Capability turn=new Capability(actor,o,forcedExploration);active=turn;
        try { policies[actor].act(turn,memories[actor]);policyCalls++;turn.validate(); }
        finally { turn.valid=false;active=null; }
        record("turn",o,-1,-1,Map.of("additions",additions-turn.addStart,"deletions",deletions-turn.dropStart,"proposals",turn.proposals));
        microstep++;
    }
    void round() {
        if(interpretation==Interpretation.SOURCE_EXECUTABLE) {
            for(Agent a:shuffle(agentList))act(a.index,null);
        } else {
            long until=microstep+NUM_PLAYERS;
            while(microstep<until) {
                if(episodeRemaining==0) {
                    actorInEpisode=random.nextInt(NUM_PLAYERS);
                    episodeExplores=random.nextBoolean(noise);
                    episodeRemaining=episodeExplores?1:NUM_PLAYERS;
                }
                act(actorInEpisode,episodeExplores);episodeRemaining--;
            }
        }
        for(Agent a:agentList) {a.util=currentUtility(a);a.cumulativeUtil+=a.util;agentUtils[0][a.index]=a.util;agentUtils[1][a.index]=a.cumulativeUtil;}
    }
    @Override public void shockNetwork() {
        int n=Math.min(numAgentsShocked,NUM_PLAYERS);
        Agent[] order=n==NUM_PLAYERS?agentList:shuffle(agentList);
        for(int j=0;j<n;j++){Agent a=order[j];a.tie_cost_1=postShockTieCost_1;a.tie_cost_2=postShockTieCost_2;shocked[a.index]=true;}
        preshock=false;
    }

    void referenceAct(Agent a,Boolean forcedExploration) {
        boolean explore=forcedExploration==null?random.nextBoolean(noise):forcedExploration;
        if(explore){gpa.randomTie(a,this);return;}
        double[] add=smartSearch?a.bestAddSmartSearch(this,searchSize):a.bestAdd(this,searchSize);
        double[] drop=a.bestDrop(this);
        double[][] swap=a.bestAddDropCombo(this,searchSize);
        if(add[1]>=0&&add[2]>0&&add[2]>drop[2]&&add[2]>swap[0][2]) {
            int partner=(int)add[1],layer=(int)add[0];
            if(partner==a.index||coplayerMatrix[layer][a.index][partner]) {
                failedReferenceProposal=new LinkedHashMap<>();
                failedReferenceProposal.put("proposer",a.index);failedReferenceProposal.put("recipient",partner);failedReferenceProposal.put("layer",layer);
                failedReferenceProposal.put("returned_gain",add[2]);failedReferenceProposal.put("actual_gain",utilityIfAdded(a,agentList[partner],layer)-currentUtility(a));
                failedReferenceProposal.put("microstep",microstep);failedReferenceProposal.put("self",partner==a.index);failedReferenceProposal.put("existing_edge",coplayerMatrix[layer][a.index][partner]);
                failedReferenceProposal.put("adjacency",PaperRunner.adjacency(this));
            }
            if(a.addTie(this,add))drop=a.bestDrop(this);
            if(drop[1]>=0&&drop[2]>0&&!(drop[0]==add[0]&&drop[1]==add[1]))a.dropTie(this,drop);
        } else {
            boolean usedSwap=swap[0][1]>=0&&swap[0][2]>0&&swap[0][2]>drop[2];
            if(usedSwap) {
                if(a.addTie(this,swap[0]))a.dropTie(this,swap[1]);
                else if(drop[2]>0)a.dropTie(this,drop);
            }
            if((interpretation==Interpretation.SOURCE_EXECUTABLE||!usedSwap)&&drop[1]>=0&&drop[2]>0)a.dropTie(this,drop);
        }
    }

    private final class Capability implements Turn {
        final int actor,addStart=additions,dropStart=deletions;
        final Observation initial;final Boolean forcedExploration;
        boolean valid=true,manual=false,reference=false;
        int proposals,randomCalls;
        int addedPartner=-1,addedLayer=-1;
        final int[] addQueries={0,0};
        final Set<String>[] swapAdds=new Set[]{new HashSet<String>(),new HashSet<String>()};
        final Map<String,int[]> swapDrops=new HashMap<>();
        String sourceSwapAdd;
        Capability(int actor,Observation initial,Boolean forcedExploration){this.actor=actor;this.initial=initial;this.forcedExploration=forcedExploration;}
        void check(){if(!valid||active!=this||recipientCallback)throw new IllegalStateException("Expired or non-owner turn capability");}
        void manual(){check();if(reference)throw new IllegalStateException("Reference action is exclusive");manual=true;}
        void indices(int partner,int layer){if(layer<0||layer>1||partner<0||partner>=NUM_PLAYERS)throw new IllegalArgumentException("Invalid actor/layer");}
        void countProposal(){if(++proposals>1)throw new IllegalStateException("At most one proposal per activation");}
        void validate(){if(additions-addStart>1||deletions-dropStart>dropBudget())throw new IllegalStateException("Edit budget exceeded");}
        int dropBudget(){return interpretation==Interpretation.SOURCE_EXECUTABLE&&additions>addStart?2:1;}
        public Observation observation(){check();return initial;}
        public int[] neighbors(int layer){check();indices(actor,layer);return neighborIds(actor,layer);}
        public int[] neighborsOfNeighbor(int neighbor,int layer){check();indices(neighbor,layer);if(!coplayerMatrix[layer][actor][neighbor])throw new IllegalArgumentException("Only an existing neighbor's same-layer neighbors are local");return neighborIds(neighbor,layer);}
        public int randomActor(){manual();if(++randomCalls>8*NUM_PLAYERS*searchSize)throw new IllegalStateException("Random query budget exceeded");return random.nextInt(NUM_PLAYERS);}
        public double randomUnit(){manual();if(++randomCalls>8*NUM_PLAYERS*searchSize)throw new IllegalStateException("Random query budget exceeded");return random.nextDouble();}
        public double inspectAdd(int partner,int layer){manual();indices(partner,layer);if(++addQueries[layer]>searchSize)throw new IllegalStateException("Addition search budget exceeded");return partner==actor||coplayerMatrix[layer][actor][partner]?Double.NaN:utilityIfAdded(agentList[actor],agentList[partner],layer);}
        public double inspectDrop(int partner,int layer){manual();indices(partner,layer);return partner==actor||!coplayerMatrix[layer][actor][partner]?Double.NaN:hypothetical(agentList[actor],-1,0,partner,layer);}
        public double inspectRewire(int add,int al,int drop,int dl){
            manual();indices(add,al);indices(drop,dl);
            String key=al+":"+add;
            if(interpretation==Interpretation.SOURCE_EXECUTABLE){
                if(sourceSwapAdd==null)sourceSwapAdd=key;
                if(!sourceSwapAdd.equals(key))throw new IllegalStateException("Source swap search examines only its first addition");
            }
            swapAdds[al].add(key);if(swapAdds[al].size()>searchSize)throw new IllegalStateException("Swap addition search budget exceeded");
            int[] counts=swapDrops.computeIfAbsent(key,k->new int[2]);
            if(++counts[dl]>searchSize)throw new IllegalStateException("Swap deletion search budget exceeded");
            if(add==actor||drop==actor||add==drop||coplayerMatrix[al][actor][add]||!coplayerMatrix[dl][actor][drop])return Double.NaN;
            return utilityIfAddDrop(agentList[actor],agentList[add],agentList[drop],al,dl);
        }
        public boolean add(int partner,int layer){manual();indices(partner,layer);boolean result=offer(agentList[actor],agentList[partner],layer);validate();return result;}
        public void drop(int partner,int layer){manual();indices(partner,layer);if(partner==addedPartner&&layer==addedLayer)throw new IllegalArgumentException("Cannot drop the edge just added");if(!coplayerMatrix[layer][actor][partner])throw new IllegalArgumentException("Can only drop an existing incident edge");if(deletions-dropStart>=dropBudget())throw new IllegalStateException("Deletion budget exceeded");tie_delete(agentList[actor],agentList[partner],layer);validate();}
        public boolean rewire(int add,int al,int drop,int dl){manual();indices(add,al);indices(drop,dl);if(add==drop||!coplayerMatrix[dl][actor][drop])throw new IllegalArgumentException("Invalid rewiring deletion");boolean yes=add(add,al);if(yes)drop(drop,dl);return yes;}
        public void noOp(){manual();}
        public void originalTurn(){check();if(manual||reference)throw new IllegalStateException("Reference action must be first and exclusive");reference=true;referenceAct(agentList[actor],forcedExploration);validate();}
    }
    int[] neighborIds(int actor,int layer) {
        int[] ids=new int[degrees[layer][actor]];int k=0;
        for(int i=0;i<NUM_PLAYERS;i++)if(coplayerMatrix[layer][actor][i])ids[k++]=i;
        return ids;
    }
}
