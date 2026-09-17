#!/usr/bin/env python3
"""Interim campaign analysis from saved cases only; never freezes a winner."""
from __future__ import annotations
import argparse
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


def analyze(run,output):
    manifest=read_json(run/'references/manifest.json');configs=manifest['cases'];spec=read_json(SPEC)
    data={};inventory={}
    for target in range(2,9):
        key=f'target_{target}';directory=run/'references'/key
        rows=load_complete(directory,configs)
        inventory[key]={'complete':rows is not None,'saved_case_indices':[i for i in range(4) if resolve_json(directory/f'case_{i:03d}.json').exists()]}
        if rows:data[key]=rows
    programs=[]
    for directory in sorted((run/'evolution/search_seed_670001').glob('gen_*'),key=lambda p:int(p.name[4:])):
        path=directory/'results/evaluation-checkpoint.json'
        if not path.exists():continue
        checkpoint=read_json(path)
        if checkpoint['status']!='completed' or not read_json(directory/'results/correct.json')['correct']:continue
        rows=load_complete(directory/'results',configs)
        if rows is None:continue
        source=directory/'main.py';digest=sha(source)
        if digest!=checkpoint['identity']['program_sha256']:raise ValueError('Native source checkpoint mismatch')
        row={'generation':int(directory.name[4:]),'source':str(source.relative_to(run)),'source_sha256':digest,'mean_offline_error':statistics.mean(r['offline_error'] for r in rows),'case_errors':[r['offline_error'] for r in rows],'source_observations':source_observations(source)}
        programs.append(row);data[f"g{row['generation']}"]=rows
    programs.sort(key=lambda p:(p['mean_offline_error'],p['generation'],p['source_sha256']))
    best=programs[0] if programs else None
    best_descendant=next((p for p in programs if p['generation']>0),None)
    methods=[k for k in ('target_5','target_3') if k in data]
    if best_descendant:methods.append(f"g{best_descendant['generation']}")
    analysis={'study':'book_mpso_population_200_v2','status':'interim_selection_biased','analyzed_at':datetime.now(timezone.utc).isoformat(),'inventory':inventory,'native':native_counts(run),'native_programs':programs,'interim_best_native':best,'interim_best_descendant':best_descendant,'final_selection_frozen':False,'fresh_evaluation_occurred':False,'analysis_specification_sha256':sha(SPEC),'analysis_source_sha256':sha(__file__),'methods':{},'comparisons':{}}
    for method,rows in data.items():
        errors=[r['offline_error'] for r in rows]
        analysis['methods'][method]={'errors':errors,'mean':statistics.mean(errors),'median':statistics.median(errors),'sd':statistics.stdev(errors),'behavior':population_behavior(rows),'recovery':aggregate_recovery(rows),'population_trajectory':population_curves(rows)}
        if 'target_5' in data:
            for a,b in zip(rows,data['target_5']):validate_pair(a,b)
    for method in methods:
        for reference in ('target_5','target_3'):
            if method==reference or reference not in data:continue
            effect=paired_effect([a['offline_error']-b['offline_error'] for a,b in zip(data[method],data[reference])],spec)
            effect['relative_mean_effect']=effect['mean']/statistics.mean(r['offline_error'] for r in data[reference])
            analysis['comparisons'][f'{method}_minus_{reference}']=effect
    if best_descendant and 'target_5' in data:
        analysis['episodes']=population_episode_effects(data[f"g{best_descendant['generation']}"],data['target_5'])
    elif 'target_3' in data and 'target_5' in data:
        analysis['episodes']=population_episode_effects(data['target_3'],data['target_5'])
    output.mkdir(parents=True,exist_ok=True);atomic_json(output/'analysis.json',analysis)
    if methods:render(analysis,methods,output)
    tables=['| Method | Case 000 | Case 001 | Case 002 | Case 003 | Mean |','|---|---:|---:|---:|---:|---:|']
    for key in methods:
        row=analysis['methods'][key];tables.append(f'| {key} | '+' | '.join(f'{v:.6f}' for v in row['errors'])+f" | {row['mean']:.6f} |")
    (output/'tables.md').write_text('\n'.join(tables)+'\n')
    return analysis


def render(data,methods,out):
    _style();colors=['#ce7a31','#6173b2','#167d78'];labels={'target_5':'Corrected 5+1 / target 5','target_3':'Constant target 3'}
    for method in methods:
        if method.startswith('g'):labels[method]=f'Interim best descendant {method}'
    fig,axs=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    for key,color in zip(methods,colors):
        curve=data['methods'][key]['population_trajectory'];x=[r['evaluations'] for r in curve]
        for ax,field in ((axs[0,0],'mean_neutral_count'),(axs[0,1],'total_particle_count'),(axs[1,0],'offline_error')):
            ax.plot(x,[r[field] for r in curve],label=labels[key],color=color,lw=1.5)
        axs[0,0].fill_between(x,[r['neutral_count_min'] for r in curve],[r['neutral_count_max'] for r in curve],color=color,alpha=.07)
    for ax in (axs[0,0],axs[0,1],axs[1,0]):
        ax.set(xlabel='Counted objective evaluations',xlim=(0,500000));ax.grid(alpha=.15);ax.ticklabel_format(axis='x',style='sci',scilimits=(0,0))
    axs[0,0].set(title='Realized neutral population per subswarm',ylabel='Mean neutrals',ylim=(1.8,8.2));axs[0,0].legend(frameon=False,fontsize=8)
    axs[0,1].set(title='Total optimizer population',ylabel='All particles')
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
