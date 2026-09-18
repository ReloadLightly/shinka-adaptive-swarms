package agents;

import paper.*;
import java.util.*;
import java.nio.file.*;

/** Synthetic focused checks. These are not paper replications or development-selection cases. */
public final class PaperChecks {
    static int checks;
    static final List<Map<String,Object>> figureChecks=new ArrayList<>();
    static Map<String,Object> smartFailure;
    static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    static void exact(double a,double b,String message){check(Double.doubleToLongBits(a)==Double.doubleToLongBits(b),message+": "+a+" != "+b);}
    static void close(double a,double b,String message){check(Math.abs(a-b)<1e-10,message+": "+a+" != "+b);}
    static Map<String,Object> config(int n) {
        Map<String,Object> c=new LinkedHashMap<>();c.put("n",n);c.put("m",Math.min(10,n));c.put("d",.8);c.put("e",.4);c.put("p",0.0);
        c.put("cost_before",.2);c.put("cost_after",.6);c.put("shock_count",2*n/3);c.put("shock_time",50);c.put("horizon",100);c.put("seed",9183L);c.put("shock_seed",317L);c.put("interpretation","source_executable");return c;
    }
    static PaperSimulation empty(int n){return PaperRunner.create(config(n),ReferencePolicy::new);}
    static void edge(PaperSimulation s,int layer,int i,int j){s.tie_form(s.agentList[i],s.agentList[j],layer);}
    static boolean[][][] hypothetical(PaperSimulation s,int ego,int add,int al,int drop,int dl){
        boolean[][][] matrix=s.cloneMatrix(s.coplayerMatrix);
        if(add>=0)matrix[al][ego][add]=matrix[al][add][ego]=true;
        if(drop>=0)matrix[dl][ego][drop]=matrix[dl][drop][ego]=false;
        return matrix;
    }
    static void utilityOracle(){
        Random random=new Random(234);
        for(int graph=0;graph<8;graph++) {
            PaperSimulation s=empty(8);
            AgentsSimulation.triangle_payoff_1=graph*.21;AgentsSimulation.triangle_payoff_2=graph*.17;AgentsSimulation.spillover_payoff=graph*.23;
            for(int l=0;l<2;l++)for(int i=0;i<8;i++)for(int j=i+1;j<8;j++)if(random.nextBoolean())edge(s,l,i,j);
            for(Agent a:s.agentList) {
                a.tie_cost_1=graph%2==0?-.2:-.6;a.tie_cost_2=graph%3==0?-.6:-.2;
                exact(s.currentUtility(a),s.utility(a,s.coplayerMatrix),"Current utility bitwise original oracle");
                for(int al=0;al<2;al++)for(int add=0;add<8;add++)if(add!=a.index&&!s.coplayerMatrix[al][a.index][add]) {
                    exact(s.utilityIfAdded(a,s.agentList[add],al),s.utility(a,hypothetical(s,a.index,add,al,-1,0)),"Addition bitwise original oracle");
                    for(int dl=0;dl<2;dl++)for(int drop=0;drop<8;drop++)if(drop!=add&&s.coplayerMatrix[dl][a.index][drop])
                        exact(s.utilityIfAddDrop(a,s.agentList[add],s.agentList[drop],al,dl),s.utility(a,hypothetical(s,a.index,add,al,drop,dl)),"Swap bitwise original oracle");
                }
                for(int dl=0;dl<2;dl++)for(int drop=0;drop<8;drop++)if(s.coplayerMatrix[dl][a.index][drop])
                    exact(s.hypothetical(a,-1,0,drop,dl),s.utility(a,hypothetical(s,a.index,-1,0,drop,dl)),"Deletion bitwise original oracle");
            }
            for(int l=0;l<2;l++)for(int i=0;i<8;i++)for(int j=i+1;j<8;j++)if(s.coplayerMatrix[l][i][j]&&random.nextBoolean())s.tie_delete(s.agentList[i],s.agentList[j],l);
            for(Agent a:s.agentList)exact(s.currentUtility(a),s.utility(a,s.coplayerMatrix),"Caches after deletions");
        }
    }
    static void sourceEquivalence(){
        for(double p:new double[]{0,.25,.5,.75}) {
            Map<String,Object> c=config(40);c.put("p",p);c.put("d",0.4);c.put("e",0.8);
            PaperSimulation adapted=PaperRunner.create(c,ReferencePolicy::new);
            PaperSimulation seed=PaperRunner.create(c,()->{try{return (ActorPolicy)Class.forName("CandidatePolicy").getDeclaredConstructor().newInstance();}catch(ReflectiveOperationException failure){throw new IllegalStateException(failure);}});
            AgentsSimulation original=new AgentsSimulation(9183);original.start();
            List<Integer> recipients=PaperRunner.shockRecipients(c);
            for(int round=1;round<=100;round++) {
                // Direct calls intentionally disable native schedule-driven shock/stopping in both.
                adapted.round();seed.round();original.gpa.step(original);
                check(PaperRunner.adjacency(adapted).equals(PaperRunner.adjacency(original)),"Source topology every round p="+p+" round="+round);
                check(PaperRunner.adjacency(seed).equals(PaperRunner.adjacency(adapted)),"Compiled CandidatePolicy seed equals reference topology");
                check(adapted.random.stateEquals(original.random),"Source RNG state every round p="+p+" round="+round);
                check(seed.random.stateEquals(adapted.random),"Compiled CandidatePolicy seed equals reference RNG state");
                for(int i=0;i<40;i++) {
                    exact(adapted.currentUtility(adapted.agentList[i]),original.currentUtility(original.agentList[i]),"Source individual utility");
                    exact(adapted.agentList[i].cumulativeUtil,original.agentList[i].cumulativeUtil,"Source cumulative utility");
                    exact(seed.agentList[i].cumulativeUtil,adapted.agentList[i].cumulativeUtil,"Compiled CandidatePolicy seed equals reference cumulative utility");
                }
                if(round==50){PaperRunner.applyShock(adapted,recipients);PaperRunner.applyShock(seed,recipients);PaperRunner.applyShock(original,recipients);}
            }
            check(adapted.activationId==4000,"Full 100x40 activations");
            System.out.println("source equivalence p="+p+": 100 rounds, 40 actors, exact adjacency/utilities/RNG");
        }
    }
    static void consentAndEvents(){
        PaperSimulation s=empty(3);
        s.policies[0]=new ReferencePolicy(){public void act(Turn t,Memory m){check(t.observation().microstep()==0,"First turn time");m.set(0,7);check(!t.add(1,0),"Receiver may reject beneficial offer");}};
        s.policies[1]=new ReferencePolicy(){public Decision accept(Offer o,Memory m){check(o.gain()>0,"Beneficial offer fixture");check(o.observation().actor()==1&&o.observation().microstep()==0,"Receiver actual event identity/time");m.set(1,13);return Decision.no();}public void act(Turn t,Memory m){check(t.observation().previousOutcome().equals("offer_rejected"),"Rejection survives until recipient's own turn");check(t.observation().previousPartner()==0,"Rejection partner identity");close(t.observation().time(),1.0/3,"Recipient true time");check(m.get(1)==13&&m.get(0)==0,"Recipient private memory");t.noOp();}};
        s.act(0,null);s.act(1,null);
        check(s.memories[0].get(0)==7&&s.memories[0].get(1)==0,"Private proposer memory");check(s.offers==1&&s.rejections==1&&s.additions==0,"Separate rejection accounting");
        long previous=s.previousEvent[0];check(previous>0&&s.previousEvent[1]==previous,"Shared result event identifies same rejected offer");
        PaperRunner.applyShock(s,List.of(0));check(s.memories[0].get(0)==7,"Shock preserves policy memory");
        final Turn[] expired={null};s.policies[2]=new ReferencePolicy(){public void act(Turn t,Memory m){expired[0]=t;t.noOp();}};s.act(2,null);
        boolean refused=false;try{expired[0].neighbors(0);}catch(IllegalStateException expected){refused=true;}check(refused,"Expired turn cannot inspect future state");
    }
    static void budgets(){
        PaperSimulation s=empty(4);
        s.policies[1]=s.policies[2]=new ReferencePolicy(){public Decision accept(Offer o,Memory m){return Decision.no();}};
        s.policies[0]=new ReferencePolicy(){public void act(Turn t,Memory m){t.add(1,0);t.add(2,0);}};
        boolean refused=false;try{s.act(0,null);}catch(IllegalStateException expected){refused=true;}check(refused&&s.offers==1,"Rejected first proposal still consumes only proposal slot");
        s=empty(4);s.policies[0]=new ReferencePolicy(){public void act(Turn t,Memory m){for(int i=0;i<=4;i++)t.inspectAdd(1,0);}};
        refused=false;try{s.act(0,null);}catch(IllegalStateException expected){refused=true;}check(refused,"m-per-layer inspection budget enforced");
        final boolean[] invalid={false};s=empty(4);s.policies[0]=new ReferencePolicy(){public void act(Turn t,Memory m){t.noOp();try{t.originalTurn();}catch(IllegalStateException e){invalid[0]=true;}}};s.act(0,null);check(invalid[0],"Cannot combine reference with manual actions");
    }
    @SuppressWarnings("unchecked") static void timingAndMetrics(){
        Map<String,Object> c=config(4);c.put("record_events",true);c.put("shock_count",4);
        Map<String,Object> result=PaperRunner.run(c,ReferencePolicy::new);
        List<Map<String,Object>> trajectory=(List<Map<String,Object>>)result.get("trajectory");
        check(trajectory.size()==101,"Retain empty initial state and all100 rounds");
        for(int round:new int[]{0,50,51,100})for(Map<String,Object> a:(List<Map<String,Object>>)trajectory.get(round).get("actors"))close(((Number)a.get("cost0")).doubleValue(),round<=50?.2:.6,"Shock just after50");
        PaperSimulation s=empty(4);edge(s,0,0,1);edge(s,1,0,1);edge(s,0,0,2);
        List<Map<String,Object>> rows=(List<Map<String,Object>>)PaperRunner.snapshot(s,0,List.of(1)).get("actors");
        Map<String,Object> exposure=(Map<String,Object>)rows.get(0).get("exposure");
        close(((Number)exposure.get("paper_fraction")).doubleValue(),2.0/3,"Paper exposure counts layers");close(((Number)exposure.get("source_union_fraction")).doubleValue(),.5,"Source exposure counts unique neighbors");
        close(((Number)rows.get(0).get("spillover_fraction")).doubleValue(),2.0/3,"Eq6 overlap fraction");
        close(((Number)rows.get(3).get("spillover_fraction")).doubleValue(),0,"Isolate convention disclosed");check(((Number)rows.get(3).get("spillover_denominator")).intValue()==0,"Retain raw zero denominator");
        check(rows.get(3).get("spillover_ratio")==null,"Undefined isolate spillover raw ratio is null");check(((Map<?,?>)rows.get(3).get("exposure")).get("paper_fraction")==null,"Undefined Eq8 isolate exposure is null");
        for(String interpretation:List.of("source_executable","paper_directed")) {
            c=config(100);c.put("horizon",3);c.put("shock_time",1);c.put("shock_count",66);c.put("interpretation",interpretation);c.put("sampling",interpretation.equals("paper_directed")?"smart":"random");
            result=PaperRunner.run(c,ReferencePolicy::new);
            check(((Number)((Map<?,?>)result.get("usage")).get("actor_activations")).intValue()==300,"N100 real arbitrary-size graph "+interpretation);
            List<String> finalLayers=(List<String>)((Map<?,?>)result.get("adjacency")).get("3");check(finalLayers.get(0).length()==4950,"N100 adjacency no64bit truncation");
        }
        c=config(4);c.put("interpretation","paper_directed");s=PaperRunner.create(c,ReferencePolicy::new);s.round();
        check(Arrays.stream(s.turns).max().orElse(0)==4,"Paper strategic episode repeats SAME actor N times");
        c=config(100);c.put("horizon",3);c.put("shock_time",1);c.put("shock_count",66);c.put("sampling","smart");
        boolean sourceSmartInvalid=false;s=PaperRunner.create(c,ReferencePolicy::new);
        List<Integer> ids=PaperRunner.shockRecipients(c);
        try{for(int round=1;round<=3;round++){s.round();if(round==1)PaperRunner.applyShock(s,ids);}}
        catch(IllegalArgumentException failure){
            sourceSmartInvalid=failure.getMessage().startsWith("Invalid proposal:");System.out.println("Preserved dormant source-smart defect: "+failure.getMessage());
            smartFailure=new LinkedHashMap<>();smartFailure.put("case",c);smartFailure.put("shock_recipients",ids);smartFailure.put("error",failure.getMessage());smartFailure.put("returned_action",s.failedReferenceProposal);
        }
        check(sourceSmartInvalid,"Dormant source-smart stale-index defect remains visible rather than silently repaired");
    }
    static void figure4(){
        for(double d:new double[]{.79,.8,.81}) {
            Map<String,Object> c=config(3);c.put("cost_before",.6);c.put("d",d);c.put("e",0.0);
            PaperSimulation s=PaperRunner.create(c,ReferencePolicy::new);edge(s,0,0,1);
            Map<String,Object> fixture=new LinkedHashMap<>();fixture.put("name","figure4_three_actor_transition_d_"+d);fixture.put("d",d);
            fixture.put("single_edge",figureState(s));
            close(s.currentUtility(s.agentList[0]),.4,"Fig4 single edge endpoint");
            close(s.utilityIfAdded(s.agentList[0],s.agentList[2],0),-.4,"Fig4 bridge utility barrier");
            edge(s,0,0,2);close(s.utilityIfAdded(s.agentList[1],s.agentList[2],0)-s.currentUtility(s.agentList[1]),d-.8,"Fig4 strict closure threshold");
            fixture.put("bridge",figureState(s));fixture.put("actual_closure_gain",s.utilityIfAdded(s.agentList[1],s.agentList[2],0)-s.currentUtility(s.agentList[1]));fixture.put("analytic_closure_gain",d-.8);
            edge(s,0,1,2);for(Agent a:s.agentList)close(s.currentUtility(a),d-.4,"Fig4 triangle each actor");
            fixture.put("triangle",figureState(s));fixture.put("passed",true);figureChecks.add(fixture);
            check((s.currentUtility(s.agentList[0])>.4+1e-12)==(d>.8),"Fig4 analytic strict endpoint threshold (1e-12 assertion tolerance only)");
        }
        close(3*(2.0/3)-1.2,.8,"Fig4 total-welfare equality at2/3 differs from strict closure .8");
    }
    static Map<String,Object> figureState(PaperSimulation s){
        List<Double> actual=new ArrayList<>(),oracle=new ArrayList<>();
        for(Agent a:s.agentList){actual.add(s.currentUtility(a));oracle.add(s.utility(a,s.coplayerMatrix));exact(s.currentUtility(a),s.utility(a,s.coplayerMatrix),"Figure4 actual graph agrees bitwise with unchanged utility oracle");}
        return Map.of("adjacency",PaperRunner.adjacency(s),"actual_actor_utilities",actual,"unchanged_oracle_actor_utilities",oracle);
    }
    @SuppressWarnings("unchecked")
    public static void main(String[] args)throws Exception {
        long start=System.nanoTime();utilityOracle();consentAndEvents();budgets();timingAndMetrics();figure4();sourceEquivalence();
        Map<String,Object> receipt=new LinkedHashMap<>();receipt.put("pass",true);receipt.put("checks",checks);receipt.put("elapsed_seconds",(System.nanoTime()-start)/1e9);receipt.put("scope","focused synthetic checks, not a paper reproduction");
        if(args.length==1) {
            Path directory=Path.of(args[0]);Files.createDirectories(directory);
            Map<String,Object> build=(Map<String,Object>)PaperJson.parse(Files.readString(Path.of("build/paper-build-identity.json")));
            String engine=build.get("engine_sha256").toString();receipt.put("engine_sha256",engine);
            Files.writeString(directory.resolve("engine_checks.json"),PaperJson.write(receipt)+"\n");
            Map<String,Object> figure=new LinkedHashMap<>();figure.put("fixture",true);figure.put("executed",true);figure.put("engine_sha256",engine);figure.put("configuration",Map.of("n",3,"b",1,"cost",.6,"e",0,"analytic_closure_threshold_d",.8,"initial_layer0_edges",List.of(List.of(0,1)),"initial_layer1_edges",List.of()));figure.put("checks",figureChecks);
            figure.put("reference_comparison",Map.of("status","discrepant","mechanism","Executed three-actor graph verifies the utility barrier and strict triangle-closing/endpoint-improvement threshold d>0.8.","qualification","Caption labels d*=0.8 a global-maxima threshold. Aggregate triangle welfare actually exceeds the single-edge graph for d>2/3; 0.8 is the sufficient strict endpoint/Pareto and closure threshold.","floating_point","At d=0.8 binary arithmetic leaves approximately 1e-16 residual gains. Engine preserves original strict > comparisons; assertion tolerance1e-12 only describes analytic equality."));
            Files.writeString(directory.resolve("figure4_fixture.json"),PaperJson.write(figure)+"\n");
            smartFailure.put("engine_sha256",engine);smartFailure.put("executed",true);smartFailure.put("status","blocked_source_smart_diagnostic");smartFailure.put("source_file","upstream/multiplex/Agents/Agent.java");smartFailure.put("source_lines",List.of(257,339,345,346,354,369));
            smartFailure.put("cause","Dormant bestAddSmartSearch retains a positive maxGain from smart search but resets bestIndex/bestLayer before its random-fill phase. When no later candidate beats that gain, the returned identity can be an existing edge or self; the observed case returns an existing edge with stale positive gain. Native tie_form would silently no-op for an existing edge (or permit a diagonal self edge); a genuine new-edge proposal through the bounded simple-graph interface is invalid. Source main does not call this dormant method. No repair or replacement result is manufactured.");
            Files.writeString(directory.resolve("source_smart_failure.json"),PaperJson.write(smartFailure)+"\n");
        }
        System.out.println(PaperJson.write(receipt));
    }
}
