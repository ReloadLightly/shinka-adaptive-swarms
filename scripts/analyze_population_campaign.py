#!/usr/bin/env python3
"""Interim campaign analysis from saved cases only; never freezes a winner."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime,timezone
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from adaptive_swarms.artifacts import read_json,resolve_json
from adaptive_swarms.book_population_v2 import ENGINE_VERSION
from adaptive_swarms.comparison import validate_pair
from adaptive_swarms.figures import _save,_style
from adaptive_swarms.logging import atomic_json
from analyze_book_population_200 import (population_behavior,population_curves,population_episode_effects,source_observations)
from analyze_book_mpso import paired_effect,aggregate_recovery,sha
from run_population_campaign import native_counts
import matplotlib.pyplot as plt
import numpy as np

SPEC=ROOT/'docs/studies/book_mpso_population_200_v2/analysis_specification.json'


def load_complete(directory,configs):
    rows=[]
    for i,config in enumerate(configs):
        path=resolve_json(directory/f'case_{i:03d}.json')
        if not path.exists(): return None
        row=read_json(path)
        if row['engine_version']!=ENGINE_VERSION or row['config']!=config or row['evaluations']!=500000 or row['case_id']!=f'case_{i:03d}':
            raise ValueError(f'Wrong corrected case identity: {path}')
        validate_pair(row,row); rows.append(row)
    return rows


def direct_constant_target(source):
    tree=ast.parse(source)
    body=[node for node in tree.body if not (isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str))]
    if len(body)!=1 or not isinstance(body[0],ast.FunctionDef):return None
    fun=body[0]
    if fun.name!='choose_neutral_count' or fun.decorator_list or fun.args.defaults or fun.args.kw_defaults or len(fun.body)!=1:return None
    stmt=fun.body[0]
    if isinstance(stmt,ast.Return) and isinstance(stmt.value,ast.Constant) and type(stmt.value.value) is int and 2<=stmt.value.value<=8:return stmt.value.value
    return None


def analyze(run,output):
    # Keep only the reference and one method's raw histories in memory. Summaries
    # preserve the same statistics; source cases are never simulated again.
    import gc
    manifest=read_json(run/'references/manifest.json');configs=manifest['cases'];spec=read_json(SPEC)
    baseline=load_complete(run/'references/target_5',configs)
    data={};inventory={};programs=[]
    def summarize(rows):
        if baseline:
            for a,b in zip(rows,baseline):validate_pair(a,b)
        errors=[r['offline_error'] for r in rows]
        return {'errors':errors,'mean':statistics.mean(errors),'median':statistics.median(errors),'sd':statistics.stdev(errors),'behavior':population_behavior(rows),'recovery':aggregate_recovery(rows),'population_trajectory':population_curves(rows)}
    for target in range(2,9):
        key=f'target_{target}';directory=run/'references'/key
        print(f'{datetime.now(timezone.utc).isoformat()} analyzing saved {key}',flush=True)
        rows=baseline if target==5 else load_complete(directory,configs)
        inventory[key]={'complete':rows is not None,'saved_case_indices':[i for i in range(4) if resolve_json(directory/f'case_{i:03d}.json').exists()]}
        if rows:data[key]=summarize(rows)
        del rows;gc.collect()
    for directory in sorted((run/'evolution/search_seed_670001').glob('gen_*'),key=lambda p:int(p.name[4:])):
        path=directory/'results/evaluation-checkpoint.json'
        if not path.exists():continue
        checkpoint=read_json(path)
        if checkpoint['status']!='completed' or not read_json(directory/'results/correct.json')['correct']:continue
        print(f'{datetime.now(timezone.utc).isoformat()} analyzing saved {directory.name}',flush=True)
        rows=load_complete(directory/'results',configs)
        if rows is None:continue
        source=directory/'main.py';digest=sha(source)
        if digest!=checkpoint['identity']['program_sha256']:raise ValueError('Native source checkpoint mismatch')
        generation=int(directory.name[4:]);summary=summarize(rows)
        metrics=read_json(directory/'results/metrics.json')
        if summary['mean']!=metrics['public']['mean_offline_error']:raise ValueError('Native metric differs from saved case mean')
        row={'generation':generation,'source':str(source.relative_to(run)),'source_sha256':digest,'mean_offline_error':summary['mean'],'case_errors':summary['errors'],'source_observations':source_observations(source)}
        programs.append(row);data[f'g{generation}']=summary
        del rows;gc.collect()
    programs.sort(key=lambda p:(p['mean_offline_error'],p['generation'],p['source_sha256']))
    best=programs[0] if programs else None
    best_descendant=next((p for p in programs if p['generation']>0),None)
    complete_constants=[key for key in data if key.startswith('target_')]
    best_constant=min(complete_constants,key=lambda key:(data[key]['mean'],int(key.split('_')[1]))) if complete_constants else None
    methods=[k for k in ('target_5','target_3') if k in data]
    aliases={}
    ledger=read_json(run/'references/execution_ledger.json')['attempts']
    for program in programs:
        constant=direct_constant_target(program['source_observations']['source'])
        if constant is not None and f'target_{constant}' in data:
            key=f"g{program['generation']}";target=f'target_{constant}'
            if data[key]['errors']!=data[target]['errors']:
                raise ValueError('Direct-constant execution alias contradicts observed paired outcomes')
            aliases[key]={'reference':target,'proof':'Single pure function returning the same literal integer for every observation; same corrected adapter, configs and RNG streams. Numerical equality corroborates but is not the equivalence proof.','physical_reuse':program['generation']==0,'reference_reuses_native':any(a['status']=='reused' and a['method']==target and a.get('native_generation')==program['generation'] for a in ledger)}
    if best_descendant and aliases.get(f"g{best_descendant['generation']}",{}).get('reference') not in methods:methods.append(f"g{best_descendant['generation']}")
    analysis={'study':'book_mpso_population_200_v2','status':'interim_selection_biased','analyzed_at':datetime.now(timezone.utc).isoformat(),'inventory':inventory,'native':native_counts(run),'native_programs':programs,'execution_aliases':aliases,'interim_best_native':best,'interim_best_descendant':best_descendant,'final_selection_frozen':False,'fresh_evaluation_occurred':False,'analysis_specification_sha256':sha(SPEC),'analysis_source_sha256':sha(__file__),'methods':data,'comparisons':{},'raw_history_memory_strategy':'Reference plus one method at a time; saved-data rereads only, zero simulator/model calls'}
    analysis['interim_best_constant_control']=best_constant
    analysis['all_seven_constant_controls_complete']=len(complete_constants)==7
    comparison_methods=list(dict.fromkeys(methods+([f"g{best_descendant['generation']}"] if best_descendant else [])))
    for method in comparison_methods:
        for reference in dict.fromkeys(('target_5','target_3',best_constant)):
            if method==reference or reference not in data:continue
            effect=paired_effect([a-b for a,b in zip(data[method]['errors'],data[reference]['errors'])],spec)
            effect['relative_mean_effect']=effect['mean']/data[reference]['mean']
            analysis['comparisons'][f'{method}_minus_{reference}']=effect
    if best_descendant and baseline:
        rows=load_complete(run/best_descendant['source'].rsplit('/',1)[0]/'results',configs)
        analysis['episodes']=population_episode_effects(rows,baseline)
        del rows
    elif 'target_3' in data and baseline:
        rows=load_complete(run/'references/target_3',configs)
        analysis['episodes']=population_episode_effects(rows,baseline)
        del rows
    del baseline;gc.collect()
    output.mkdir(parents=True,exist_ok=True);atomic_json(output/'analysis.json',analysis)
    if methods:render(analysis,methods,output)
    tables=['| Method | Case 000 | Case 001 | Case 002 | Case 003 | Mean |','|---|---:|---:|---:|---:|---:|']
    for key in list(dict.fromkeys(complete_constants+methods)):
        row=analysis['methods'][key];tables.append(f'| {key} | '+' | '.join(f'{v:.6f}' for v in row['errors'])+f" | {row['mean']:.6f} |")
    (output/'tables.md').write_text('\n'.join(tables)+'\n')
    return analysis


def render(data,methods,out):
    _style();colors=['#ce7a31','#6173b2','#167d78'];labels={'target_5':'Corrected 5+1 / target 5','target_3':'Constant target 3'}
    for method in methods:
        if method.startswith('g'):labels[method]=f'Interim best descendant {method}'
    fig,axs=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    swarm_axis=axs[0,1].twinx()
    for key,color in zip(methods,colors):
        curve=data['methods'][key]['population_trajectory'];x=[r['evaluations'] for r in curve]
        for ax,field in ((axs[0,0],'mean_neutral_count'),(axs[0,1],'total_particle_count'),(axs[1,0],'offline_error')):
            ax.plot(x,[r[field] for r in curve],label=labels[key],color=color,lw=1.5)
        axs[0,0].fill_between(x,[r['neutral_count_min'] for r in curve],[r['neutral_count_max'] for r in curve],color=color,alpha=.07)
        swarm_axis.plot(x,[r['swarm_count'] for r in curve],color=color,lw=1,ls='--',alpha=.75)
    for ax in (axs[0,0],axs[0,1],axs[1,0]):
        ax.set(xlabel='Counted objective evaluations',xlim=(0,500000));ax.grid(alpha=.15);ax.ticklabel_format(axis='x',style='sci',scilimits=(0,0))
    axs[0,0].set(title='Realized neutral population per subswarm',ylabel='Mean neutrals',ylim=(1.8,8.2));axs[0,0].legend(frameon=False,fontsize=8)
    axs[0,1].set(title='Optimizer population and search groups',ylabel='All particles (solid)')
    swarm_axis.set_ylabel('Subswarm count (dashed)')
    axs[1,0].set(title='Tracking performance',ylabel='Cumulative offline error',yscale='log')
    for offset,(key,color) in enumerate(zip(methods[1:],colors[1:])):
        effect=data['comparisons'].get(f'{key}_minus_target_5')
        if not effect:continue
        axs[1,1].scatter(effect['values'],np.arange(4)+offset*.16,color=color,label=labels[key],s=35)
        axs[1,1].plot(effect['descriptive_95_percent_interval'],[-1-offset*.4]*2,color=color,lw=2)
        axs[1,1].scatter(effect['mean'],-1-offset*.4,color=color,marker='D')
    axs[1,1].axvline(0,color='gray',lw=1,ls='--');axs[1,1].set(title='Paired development differences from corrected 5+1',xlabel='Offline-error difference (negative favors first)',yticks=range(4),yticklabels=[f'Case {i:03d}' for i in range(4)]);axs[1,1].legend(frameon=False,fontsize=8);axs[1,1].grid(alpha=.15)
    fig.suptitle('Corrected enclosing-ball MPSO · interim campaign development results',fontsize=14)
    fig.supxlabel('Four reused histories · 5D · 200 peaks · severity 1 · 500,000 queries per method/history.\nSelection-biased interim results; shaded population spread is not uncertainty. Intervals resample whole histories.',fontsize=9)
    _save(fig,out/'population_and_tracking')
    if 'episodes' in data:
        fig,axes=plt.subplots(1,2,figsize=(12,4),constrained_layout=True)
        for ax,name in zip(axes,('most_favorable','most_unfavorable')):
            ep=data['episodes'][name]
            for field,label,color in [('selected_trace','Interim descendant' if data['interim_best_descendant'] else 'Target 3','#167d78'),('reference_trace','Corrected 5+1','#ce7a31')]:
                ax.plot([p['evaluations'] for p in ep[field]],[p['current_error'] for p in ep[field]],label=label,color=color)
            ax.set(title=f"{name.replace('_',' ').capitalize()}: case {ep['case_index']:03d}, period {ep['environment']}\nMean error difference {ep['difference']:+.3f}",xlabel='Counted objective evaluations',ylabel='Best-discovered error');ax.grid(alpha=.15)
        axes[0].legend(frameon=False,fontsize=8)
        fig.supxlabel('Prespecified extrema rule, initialization excluded. Saved trajectories only; periods are not independent replicates.',fontsize=9)
        _save(fig,out/'tracking_episodes')
    atomic_json(out/'figure_provenance.json',{'analysis_sha256':sha(out/'analysis.json'),'script_sha256':sha(__file__),'objective_queries':0,'model_responses':0,'figures':{p.name:sha(p) for p in out.glob('*.png')}})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=analyze(a.run.resolve(),a.output.resolve());print({k:data[k] for k in ('status','interim_best_native','fresh_evaluation_occurred')})
if __name__=='__main__':main()
