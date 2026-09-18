package agents;

import paper.*;
import java.nio.file.*;
import java.lang.reflect.RecordComponent;
import java.util.*;
import java.util.function.Supplier;

/** One case per JVM: upstream model parameters are static. No snapshots substitute for formation. */
public final class PaperRunner {
    static Number number(Map<String,Object> c,String key,Number fallback){return (Number)c.getOrDefault(key,fallback);}
    public static void configure(Map<String,Object> c) {
        int n=number(c,"n",40).intValue(),m=number(c,"m",10).intValue();
        if(n<3||n>1000||m<1||m>n)throw new IllegalArgumentException("Require 3<=n<=1000 and 1<=m<=n");
        AgentsSimulation.NUM_PLAYERS=n;AgentsSimulation.searchSize=m;
        AgentsSimulation.noise=number(c,"p",0).doubleValue();
        AgentsSimulation.tie_cost_1=AgentsSimulation.tie_cost_2=-number(c,"cost_before",.2).doubleValue();
        AgentsSimulation.postShockTieCost_1=AgentsSimulation.postShockTieCost_2=-number(c,"cost_after",.6).doubleValue();
        AgentsSimulation.triangle_payoff_1=AgentsSimulation.triangle_payoff_2=number(c,"d",0).doubleValue();
        AgentsSimulation.spillover_payoff=number(c,"e",0).doubleValue();
        for(double x:new double[]{AgentsSimulation.noise,-AgentsSimulation.tie_cost_1,-AgentsSimulation.postShockTieCost_1,AgentsSimulation.triangle_payoff_1,AgentsSimulation.spillover_payoff})if(!Double.isFinite(x)||x<0)throw new IllegalArgumentException("Finite nonnegative parameters required");
        if(AgentsSimulation.noise>1)throw new IllegalArgumentException("p>1");
        AgentsSimulation.timeOfShock=number(c,"shock_time",50).intValue();
        AgentsSimulation.lengthOfSimulations=number(c,"horizon",100).intValue();
        AgentsSimulation.numAgentsShocked=number(c,"shock_count",26).intValue();
        if(AgentsSimulation.numAgentsShocked<0||AgentsSimulation.numAgentsShocked>n||AgentsSimulation.timeOfShock<0||AgentsSimulation.lengthOfSimulations<AgentsSimulation.timeOfShock)throw new IllegalArgumentException("Invalid shock count or timing");
        AgentsSimulation.tie_benefit_1=AgentsSimulation.tie_benefit_2=1;
        AgentsSimulation.doGraphics=false;AgentsSimulation.experimentMode=false;
        AgentsSimulation.alwaysStartSearchAtLayer0=false;AgentsSimulation.oneLayerOnly=false;
    }
    static PaperSimulation create(Map<String,Object> c,Supplier<ActorPolicy> factory) {
        configure(c);
        PaperSimulation.Interpretation interpretation=PaperSimulation.Interpretation.valueOf(c.getOrDefault("interpretation","source_executable").toString().toUpperCase(Locale.ROOT));
        String sampling=c.getOrDefault("sampling","random").toString();
        if(!Set.of("random","smart").contains(sampling))throw new IllegalArgumentException("Unknown sampling mode");
        PaperSimulation s=new PaperSimulation(number(c,"seed",1L).longValue(),interpretation,factory,
            Boolean.TRUE.equals(c.getOrDefault("record_events",false)),sampling.equals("smart"));
        s.start();return s;
    }
    static List<Integer> shockRecipients(Map<String,Object> c) {
        int n=AgentsSimulation.NUM_PLAYERS,count=AgentsSimulation.numAgentsShocked;
        List<Integer> ids=new ArrayList<>();
        if(c.containsKey("shock_recipients")) {
            for(Object value:(List<?>)c.get("shock_recipients"))ids.add(((Number)value).intValue());
            if(ids.size()!=count||new HashSet<>(ids).size()!=count||ids.stream().anyMatch(i->i<0||i>=n))throw new IllegalArgumentException("Explicit shock recipients invalid");
        } else {
            for(int i=0;i<n;i++)ids.add(i);
            Collections.shuffle(ids,new Random(number(c,"shock_seed",917L).longValue()));
            ids=new ArrayList<>(ids.subList(0,count));
        }
        return ids;
    }
    static void applyShock(AgentsSimulation s,List<Integer> recipients) {
        for(int i:recipients){s.agentList[i].tie_cost_1=AgentsSimulation.postShockTieCost_1;s.agentList[i].tie_cost_2=AgentsSimulation.postShockTieCost_2;if(s instanceof PaperSimulation p)p.shocked[i]=true;}
        s.preshock=false;
    }
    public static Map<String,Object> observationMap(Observation observation) {
        Map<String,Object> result=new LinkedHashMap<>();
        try { for(RecordComponent field:Observation.class.getRecordComponents())result.put(field.getName(),field.getAccessor().invoke(observation)); }
        catch(ReflectiveOperationException failure){throw new IllegalStateException(failure);}
        return result;
    }
    static List<String> adjacency(AgentsSimulation s) {
        List<String> layers=new ArrayList<>();
        for(int l=0;l<2;l++){StringBuilder b=new StringBuilder();for(int i=0;i<AgentsSimulation.NUM_PLAYERS;i++)for(int j=i+1;j<AgentsSimulation.NUM_PLAYERS;j++)b.append(s.coplayerMatrix[l][i][j]?'1':'0');layers.add(b.toString());}
        return layers;
    }
    static Map<String,Object> snapshot(PaperSimulation s,int round,List<Integer> recipientIds) {
        int n=AgentsSimulation.NUM_PLAYERS;boolean[] recipient=new boolean[n];for(int i:recipientIds)recipient[i]=true;
        List<Map<String,Object>> actors=new ArrayList<>();
        double utilitySum=0,spillSum=0,clusterSum=0;int totalDegree=0,totalOverlapDegree=0,totalTriangles=0,isolateCount=0;
        for(int i=0;i<n;i++) {
            Agent a=s.agentList[i];int k0=s.degrees[0][i],k1=s.degrees[1][i],z0=s.triangles[0][i],z1=s.triangles[1][i];
            double clustering0=k0<2?0:2.0*z0/(k0*(k0-1)),clustering1=k1<2?0:2.0*z1/(k1*(k1-1));
            int k=k0+k1;double spill=k==0?0:2.0*s.overlaps[i]/k;
            int exposed=0,union=0,exposedUnion=0;
            for(int j=0;j<n;j++) {
                if(s.coplayerMatrix[0][i][j]||s.coplayerMatrix[1][i][j]){union++;if(recipient[j])exposedUnion++;}
                for(int l=0;l<2;l++)if(s.coplayerMatrix[l][i][j]&&recipient[j])exposed++;
            }
            Map<String,Object> row=new LinkedHashMap<>();
            row.put("actor",i);row.put("utility",s.currentUtility(a));row.put("cumulative_utility",a.cumulativeUtil);
            row.put("cost0",-a.tie_cost_1);row.put("cost1",-a.tie_cost_2);
            row.put("degree0",k0);row.put("degree1",k1);row.put("triangles0",z0);row.put("triangles1",z1);
            row.put("overlap",s.overlaps[i]);row.put("spillover_numerator",2*s.overlaps[i]);row.put("spillover_denominator",k);row.put("spillover_fraction",spill);
            row.put("spillover_ratio",k==0?null:spill);row.put("spillover_fraction_convention","source_zero_for_isolates");
            row.put("clustering0",clustering0);row.put("clustering1",clustering1);
            row.put("clustering_ratio0",k0<2?null:clustering0);row.put("clustering_ratio1",k1<2?null:clustering1);row.put("clustering_convention","source_zero_for_degree_less_than_two");
            row.put("clustering_numerator0",2*z0);row.put("clustering_numerator1",2*z1);row.put("clustering_denominator0",k0*(k0-1));row.put("clustering_denominator1",k1*(k1-1));
            row.put("turns",s.turns[i]);row.put("previous_event_id",s.previousEvent[i]);row.put("previous_outcome",s.previousOutcome[i]);
            Map<String,Object> exposure=new LinkedHashMap<>();exposure.put("paper_numerator",exposed);exposure.put("paper_denominator",k);exposure.put("paper_fraction",k==0?null:(double)exposed/k);
            exposure.put("source_union_numerator",exposedUnion);exposure.put("source_union_denominator",union);exposure.put("source_union_fraction",union==0?0:(double)exposedUnion/union);exposure.put("source_union_ratio",union==0?null:(double)exposedUnion/union);exposure.put("source_union_fraction_convention","source_zero_for_isolates");row.put("exposure",exposure);
            if(k==0)isolateCount++;
            actors.add(row);utilitySum+=s.currentUtility(a);spillSum+=spill;clusterSum+=clustering0+clustering1;totalDegree+=k;totalOverlapDegree+=s.overlaps[i];totalTriangles+=z0+z1;
        }
        Map<String,Object> network=new LinkedHashMap<>();network.put("mean_total_degree",(double)totalDegree/n);network.put("mean_layer_degree",(double)totalDegree/(2*n));
        network.put("mean_utility",utilitySum/n);network.put("mean_spillover_fraction",spillSum/n);network.put("mean_clustering",clusterSum/(2*n));network.put("total_degree",totalDegree);
        network.put("edge_count",totalDegree/2);network.put("overlap_edges",totalOverlapDegree/2);network.put("triangles",totalTriangles/3);network.put("actor_count",n);
        network.put("utility_sum",utilitySum);network.put("spillover_fraction_sum",spillSum);network.put("clustering_sum",clusterSum);
        network.put("isolate_count",isolateCount);network.put("mean_spillover_fraction_zero_for_isolates",spillSum/n);network.put("mean_clustering_zero_for_low_degree",clusterSum/(2*n));network.put("ratio_conventions","Legacy mean_spillover_fraction and mean_clustering aliases retain explicitly disclosed source zero conventions; raw undefined actor ratios are null.");
        Map<String,Object> result=new LinkedHashMap<>();result.put("round",round);result.put("time",round);result.put("actors",actors);result.put("network",network);return result;
    }
    public static Map<String,Object> run(Map<String,Object> c,Supplier<ActorPolicy> factory) {
        PaperSimulation s=create(c,factory);List<Integer> recipients=shockRecipients(c);
        int shock=AgentsSimulation.timeOfShock,horizon=(int)AgentsSimulation.lengthOfSimulations;
        List<Map<String,Object>> trajectory=new ArrayList<>();Map<String,Object> adjacency=new LinkedHashMap<>();
        trajectory.add(snapshot(s,0,recipients));adjacency.put("0",adjacency(s));
        if(shock==0)applyShock(s,recipients);
        for(int round=1;round<=horizon;round++) {
            s.round();trajectory.add(snapshot(s,round,recipients));
            if(round==shock||round==horizon)adjacency.put(Integer.toString(round),adjacency(s));
            if(round==shock)applyShock(s,recipients);
        }
        Map<String,Object> result=new LinkedHashMap<>();result.put("schema","paper_trajectory_v2.engine.v1");result.put("case",new LinkedHashMap<>(c));
        result.put("trajectory",trajectory);result.put("adjacency",adjacency);result.put("shock_recipients",recipients);
        result.put("usage",Map.of("actor_activations",s.activationId,"policy_calls",s.policyCalls,"offers",s.offers,"accepted",s.acceptances,"rejected",s.rejections,"additions",s.additions,"deletions",s.deletions));
        if(s.recordEvents){s.events.sort(Comparator.comparingLong(e->((Number)((Map<?,?>)e.get("observation")).get("eventId")).longValue()));result.put("events",s.events);}
        result.put("interpretation_notes",List.of(
            "Independent explicit shock recipients override upstream action-RNG shock selection for paired comparisons.",
            "Full horizon; observe time50 before costs change immediately after50; no native equilibrium early stop.",
            "SOURCE_EXECUTABLE preserves shuffled activation, source swap-counter bug and possible second deletion.",
            "PAPER_DIRECTED follows literal same-actor strategic episodes of N microsteps, one noisy microstep; episodes cross round/shock boundaries and truncate only at horizon.",
            "PAPER_DIRECTED resets swap deletion search and enforces one addition/one deletion. Source-backed m-per-layer sampled swap deletions remain an explicit unresolved prose choice.",
            "Local clustering and spillover isolates use the source zero convention; raw zero denominators are preserved.",
            "Exposure reports paper layer-weighted Eq8 and original analysis union-neighbor diagnostic; observer labels never enter policy observations.",
            "Cumulative utilities sum end-of-integer-round utilities, matching source reporting; complete integer-time series is retained."));
        s.finish();return result;
    }
    @SuppressWarnings("unchecked")
    public static void main(String[] args)throws Exception {
        if(args.length<2||args.length>3)throw new IllegalArgumentException("PaperRunner CASE_JSON OUTPUT_JSON [POLICY_CLASS]");
        Map<String,Object> c=(Map<String,Object>)PaperJson.parse(Files.readString(Path.of(args[0])));
        Class<?> type=Class.forName(args.length==3?args[2]:"CandidatePolicy");
        if(!ActorPolicy.class.isAssignableFrom(type))throw new IllegalArgumentException("Candidate must implement paper.ActorPolicy");
        Supplier<ActorPolicy> factory=()->{try{return (ActorPolicy)type.getDeclaredConstructor().newInstance();}catch(ReflectiveOperationException ex){throw new IllegalArgumentException("Constructing actor policy",ex);}};
        Map<String,Object> result=run(c,factory);
        Files.writeString(Path.of(args[1]),PaperJson.write(result)+"\n");
        System.out.println(PaperJson.write(Map.of("case_id",c.getOrDefault("case_id","unnamed"),"output",args[1],"usage",result.get("usage"))));
    }
}
