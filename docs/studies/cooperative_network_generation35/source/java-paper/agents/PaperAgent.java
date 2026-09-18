package agents;

/** v2 adapter; SOURCE preserves unchanged search, PAPER resets the documented counter. */
final class PaperAgent extends Agent {
    PaperAgent(int i,double cost0,double cost1) { super(i,cost0,cost1); }
    @Override public boolean addTie(AgentsSimulation state,double[] addition) {
        return addTie(state,state.agentList[(int)addition[1]],(int)addition[0]);
    }
    @Override public boolean addTie(AgentsSimulation state,Agent other,int layer) {
        return ((PaperSimulation)state).offer(this,other,layer);
    }
    @Override public double[] bestAddSmartSearch(AgentsSimulation state,int m) {
        PaperSimulation s=(PaperSimulation)state;
        if(s.interpretation==PaperSimulation.Interpretation.SOURCE_EXECUTABLE)
            return super.bestAddSmartSearch(state,m);
        double current=s.currentUtility(this),gain=-998;int layer=0,partner=-1;
        for(int[] candidate:smartCandidates(s,m)) {
            int l=candidate[0],j=candidate[1];
            if(j==index||s.coplayerMatrix[l][index][j])continue;
            double g=s.utilityIfAdded(this,s.agentList[j],l)-current;
            if(g>gain){gain=g;layer=l;partner=j;}
        }
        return new double[]{layer,partner,gain};
    }
    private java.util.List<int[]> smartCandidates(PaperSimulation s,int requested) {
        int m=Math.min(requested,s.NUM_PLAYERS);
        java.util.List<int[]> candidates=new java.util.ArrayList<>();
        int first=s.random.nextInt(2);
        for(int offset=0;offset<2;offset++) {
            int layer=(first+offset)%2,used=0;
            // Paper does not specify neighbor order: preserve source ascending identity order.
            for(int neighbor=0;neighbor<s.NUM_PLAYERS&&used<m;neighbor++)if(s.coplayerMatrix[layer][index][neighbor]) {
                used++;
                if(s.random.nextBoolean(.5))candidates.add(new int[]{1-layer,neighbor});
                else {
                    java.util.List<Integer> eligible=new java.util.ArrayList<>();
                    for(int friend=0;friend<s.NUM_PLAYERS;friend++)if(friend!=index&&s.coplayerMatrix[layer][neighbor][friend]&&!s.coplayerMatrix[layer][index][friend])eligible.add(friend);
                    if(!eligible.isEmpty())candidates.add(new int[]{layer,eligible.get(s.random.nextInt(eligible.size()))});
                }
            }
            while(used++<m)candidates.add(new int[]{layer,s.random.nextInt(s.NUM_PLAYERS)});
        }
        return candidates;
    }
    private double[][] paperSmartSwap(PaperSimulation s,int m) {
        if(noTies(s)||fullyConnected(s))return new double[][]{{0,-1,0},{0,-1,0}};
        double current=s.currentUtility(this),gain=-998;int al=0,ap=-1,dl=0,dp=-1;
        for(int[] addition:smartCandidates(s,m)) {
            int l=addition[0],j=addition[1];
            if(j==index||s.coplayerMatrix[l][index][j])continue;
            int first=s.random.nextInt(2);
            for(int offset=0;offset<2;offset++)for(int q=0;q<Math.min(m,s.NUM_PLAYERS);q++) {
                int dropLayer=(first+offset)%2,drop=s.random.nextInt(s.NUM_PLAYERS);
                if(drop==index||drop==j||!s.coplayerMatrix[dropLayer][index][drop])continue;
                double g=s.utilityIfAddDrop(this,s.agentList[j],s.agentList[drop],l,dropLayer)-current;
                if(g>gain){gain=g;al=l;ap=j;dl=dropLayer;dp=drop;}
            }
        }
        return new double[][]{{al,ap,gain},{dl,dp,gain}};
    }
    @Override
	public double[][] bestAddDropCombo(AgentsSimulation as, int searchSize){
        if (((PaperSimulation)as).interpretation == PaperSimulation.Interpretation.SOURCE_EXECUTABLE)
            return super.bestAddDropCombo(as, searchSize);
        if (((PaperSimulation)as).smartSearch)
            return paperSmartSwap((PaperSimulation)as,searchSize);
		if(this.noTies(as) || this.fullyConnected(as)){//don't bother if agent no current edges or fully connected
			double[][] temp =  {{0.0, -1, 0}, {0.0, -1, 0}};
			return temp;
		}
		
		if(searchSize > as.NUM_PLAYERS)
			searchSize = as.NUM_PLAYERS;
		double currentUtil = as.currentUtility(this); //agent's current utility
		double maxGain = -998; 	
		int addLayer = as.random.nextInt(2); //to get next, i = i + 1 - 2*i (starts search at random layer)
		int dropLayer = as.random.nextInt(2);
		if(as.alwaysStartSearchAtLayer0 || as.oneLayerOnly){
			addLayer = 0; 
			dropLayer = 0; 
		}			
		int i = as.random.nextInt(as.NUM_PLAYERS); //start add search at random player
		int j = as.random.nextInt(as.NUM_PLAYERS); //start drop search at random player
		int bestAddIndex = i; 
		int init_i = i;
		int init_j = j;
		int bestAddLayer = addLayer; 
		int bestDropIndex = j; 
		int bestDropLayer = dropLayer; 
		int addCount = 0; 
		int dropCount = 0; 	
		int countADDPLAYER = 0; 
		int countDROPPLAYER = 0; 
		int max = 2;
		if(as.oneLayerOnly) max = 1;
		while(addCount < max){//start at random layer			
			while(countADDPLAYER < searchSize){ //as.NUM_PLAYERS){//loop over potential adds
				if(i != this.index && !isTie(as, as.agentList[i], addLayer)){ //if no tie exists 					
					Agent addAgent = as.agentList[i];
					dropCount = 0; // clarified: restart deletion search for EVERY proposed addition					
					while(dropCount < max){ //loop over potential deletes
						while(countDROPPLAYER < searchSize){ //as.NUM_PLAYERS){
							if(j != this.index && j != i && isTie(as, as.agentList[j], dropLayer)){ //if tie exists
								Agent dropAgent = as.agentList[j];
								double newUtil = as.utilityIfAddDrop(this, addAgent, dropAgent, addLayer, dropLayer);
								double gain = newUtil - currentUtil;
								if(gain > maxGain){//if best move
									maxGain = gain;
									bestAddIndex = i; 
									bestAddLayer = addLayer; 
									bestDropIndex = j; 
									bestDropLayer = dropLayer; 
								}	
							}
							j = as.random.nextInt(as.NUM_PLAYERS);;
							//if(j >= as.NUM_PLAYERS) j = 0;
							countDROPPLAYER++;	
						}
						dropLayer = dropLayer + 1 - 2*dropLayer;
						dropCount++;	
						countDROPPLAYER = 0;
						//j = as.random.nextInt(as.NUM_PLAYERS);
						j = init_j; //search same set of nodes each time. 
					}
				}
				i = as.random.nextInt(as.NUM_PLAYERS);
				//if(i >= as.NUM_PLAYERS) i = 0;
				countADDPLAYER++;				
			}
			addLayer = addLayer + 1 - 2*addLayer;
			addCount++;
			countADDPLAYER = 0;
			//i = as.random.nextInt(as.NUM_PLAYERS); 
			i = init_i; //search the same set of agents each time
		}
		double[][] bestAddDrop = {{bestAddLayer, bestAddIndex, maxGain}, {bestDropLayer, bestDropIndex, maxGain}};
		return bestAddDrop; 
	}
	
}
