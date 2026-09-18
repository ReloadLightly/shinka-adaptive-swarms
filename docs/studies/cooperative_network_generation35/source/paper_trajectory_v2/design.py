"""Declared condition grid. Seeds and priority are fixed before observing outcomes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = 'paper_trajectory_v2'
RESULTS = ROOT / 'results' / CAMPAIGN
EXPERIMENT = ROOT / 'experiments' / CAMPAIGN
MANIFEST = ROOT / 'campaigns' / (CAMPAIGN + '.json')
SEARCH = RESULTS / 'search'
GRID = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0]
NOISE = [0.0, 0.25, 0.5, 0.75]
INTERPRETATIONS = ['source_executable', 'paper_directed']

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def sha(value):
    return hashlib.sha256(value).hexdigest()

def seed_for(*values):
    return int(sha(canonical([CAMPAIGN, *values]))[:15], 16)

def case(n=40, d=0., e=0., p=0., cost_before=.2, cost_after=.6,
         shock_count=26, repetition=0, interpretation='source_executable', sampling='random', split='reference'):
    identity = dict(n=n, m=10, d=d, e=e, p=p, cost_before=cost_before, cost_after=cost_after,
                    shock_count=shock_count, shock_time=50, horizon=100, repetition=repetition,
                    interpretation=interpretation, sampling=sampling, split=split)
    # Common external seeds across cost conditions, interpretations and policies. N/d/e/p
    # and independent repetition identify a history family; analyses cluster full runs.
    identity['seed'] = seed_for(split, n, d, e, p, repetition, 'dynamics')
    identity['shock_seed'] = seed_for(split, n, d, e, p, repetition, 'shock')
    identity['case_id'] = sha(canonical(identity))[:24]
    return identity

def conditions(n):
    counts = [13, 26, 40] if n == 40 else [33, 66, 100]
    return [(.2, .6, k) for k in counts] + [(.6, .2, k) for k in counts] + [(.2, .2, 0), (.6, .6, 0)]

def reference_cases():
    # Five repetitions are source-anchored reconstruction, NOT recovered production metadata.
    # Complete first repetition for each method before later repeats. No outcome-based ordering.
    out=[]
    for repetition in range(5):
        for n,sampling in [(40,'random'), (40,'smart'), (100,'random')]:
            for interpretation in INTERPRETATIONS:
                block=[case(n,d,e,p,b,a,k,repetition,interpretation,sampling)
                       for d in GRID for e in GRID for p in NOISE for b,a,k in conditions(n)]
                block.sort(key=lambda x: sha(canonical(['fixed-reference-priority-v1',x['case_id']])))
                out.extend(block)
    return out

def benchmark_cases():
    return [case(n,d,e,p,.2,.6,26 if n==40 else 66,0,interpretation,split='benchmark')
            for interpretation in INTERPRETATIONS for n in (40,100)
            for d,e,p in [(0.,0.,0.),(1.2,1.2,.25),(2.,2.,.75)]]

def declaration():
    return {
      'campaign_id':CAMPAIGN,'version':1,'descendant_proposal_ceiling':50,
      'initialization_programs':1,'administrative_island_copies_excluded':True,
      'main_conditions_per_interpretation':1152,'source_anchored_repetitions':5,
      'reference_trajectories_per_interpretation_main':5760,
      'reference_trajectories_all_declared_methods_interpretations':34560,
      'incentives_independent':True,'grid':GRID,'noise':NOISE,
      'main_n':40,'supplement_n':100,'m':10,'shock_time':50,'horizon':100,
      'interpretations':INTERPRETATIONS,'methods':[[40,'random'],[40,'smart'],[100,'random']],
      'reference_reconstruction_status':'Publication exact grids/repetitions unavailable; six-value grid and five repetitions anchored to pinned source, with paper time50/100 and p0/.25/.5/.75 overrides. Numerical reproduction remains an empirical comparison, not inferred from implementation.',
      'reference_priority':'Fixed hash order within repetition/method/interpretation; independent of observed outcomes.',
      'external_shock_coupling':'Separate deterministic shock seed; same recipients and time across policy pairs, independent of policy RNG consumption.',
      'discovery_gate':'Mandatory completed reference reproduction report covering all declared main/supplement computational panels and exact frozen engine/behavior/configuration/baseline identities; incomplete executions or consequential unresolved discrepancies block any mutation.',
      'discovery_subset_authorized':False,
      'fixed_noise_role':'Reference-policy variants only, never extra external conditions for an evolved policy.',
      'discovery_target':'Mean terminal population utility at100; extension beyond descriptive paper, not author objective.',
      'fresh_comparison':'Independent held-out histories; inaccessible to discovery; selection and comparators frozen before use.',
      'scope_remains_pending_until_executed':'Full declared paper reference matrix, supplement, native discovery up to50 descendant proposals and broad fresh comparisons. A bounded session does not reduce this scope.'}
