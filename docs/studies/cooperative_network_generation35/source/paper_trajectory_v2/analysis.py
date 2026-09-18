"""Descriptive paper comparisons from verified cached histories; never executes a case.

The regression is an explicitly reconstructed OLS estimator with a sandwich
covariance clustered on external history seeds. The publication's unidentified
mixed-effects specification is not claimed to have been recovered.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import lzma
import math
import os
from pathlib import Path
import statistics
import tempfile
from datetime import datetime, timezone

import numpy as np
from scipy.stats import t as student_t

from paper_trajectory_v2.design import ROOT, GRID, NOISE, reference_cases

METRICS = ('degree', 'clustering', 'spillover', 'utility')
PREDICTORS = ('constant', 'pre_statistic', 'shocked_x_noise', 'noise',
              'neighbor_exposure', 'shocked', 'spillover_payoff', 'triangle_payoff')
NETWORK_KEYS = dict(degree='mean_total_degree', clustering='mean_clustering',
                    spillover='mean_spillover_fraction', utility='mean_utility')
REGRESSION_NOTE = ('Reconstructed Equation7 OLS with CR1 history-clustered covariance '
                   'and Student-t intervals (clusters minus1 degrees of freedom); '
                   'the published mixed-effect grouping and covariance are unavailable. '
                   'Common seeds across related conditions share a cluster. '
                   'Incomplete grids may change the covariate distribution.')
SCHEDULER_NOTE = ('Source p is the noisy-action probability. Literal paper p is the episode-branch '
                  'probability; one strategic episode has N actions and one noisy episode has1, '
                  'so its long-run noisy-action fraction is p/[N*(1-p)+p]. Differences across '
                  'these schedules are differences between model interpretations, not policy gains.')


def _dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def _csv(path, rows):
    rows = list(rows)
    if not rows:
        Path(path).write_text('')
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list, tuple)) else v
                        for k, v in row.items()})


def _condition(case):
    a, b = case['cost_before'], case['cost_after']
    return 'LL' if a == b == .2 else 'HH' if a == b == .6 else 'LH' if a < b else 'HL'


def _method(case):
    return (case['interpretation'], int(case['n']), case['sampling'])


def _method_name(method):
    return f'{method[0]}_N{method[1]}_{method[2]}'


def _history(case):
    # Related shock-count/cost trajectories share randomness and are not independent.
    return (int(case['n']), int(case['seed']), int(case['shock_seed']))


def _summary(values, clusters=None):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return dict(observations=0, mean=None, sd=None, histories=0, history_se=None, history_ci95=None)
    grouped = defaultdict(list)
    for i, value in enumerate(values):
        grouped[clusters[i] if clusters is not None else i].append(float(value))
    # Descriptive uncertainty: one equally weighted mean per independent seed family.
    means = np.asarray([statistics.mean(v) for v in grouped.values()])
    se = float(np.std(means, ddof=1) / math.sqrt(len(means))) if len(means) > 1 else None
    interval = None
    if se is not None:
        half = float(student_t.ppf(.975, len(means) - 1)) * se
        interval = [float(means.mean() - half), float(means.mean() + half)]
    return dict(observations=len(values), mean=float(values.mean()),
                sd=float(values.std(ddof=1)) if len(values) > 1 else None,
                histories=len(means), history_mean=float(means.mean()), history_se=se,
                history_ci95=interval)


class EmpiricalCDF:
    """Exact common baseline pool with bounded RAM and an in-place disk sort.

    The raw sample sort is temporary; only unique values and exact counts are
    published. No rounding or approximate quantile sketch is used.
    """
    def __init__(self,path=None):
        self._temporary=tempfile.TemporaryDirectory(prefix='paper-cdf-') if path is None else None
        self.path=Path(path) if path is not None else Path(self._temporary.name)/'utility.f64'
        self.path.write_bytes(b'')
        self.total=0

    def add(self, values):
        values = np.asarray(values,dtype='<f8')
        if not np.all(np.isfinite(values)):
            raise ValueError('Nonfinite utility in reference CDF')
        with self.path.open('ab') as f:
            values.tofile(f)
        self.total+=len(values)

    def freeze(self):
        raw=np.memmap(self.path,dtype='<f8',mode='r+',shape=(self.total,)) if self.total else np.array([],dtype=float)
        raw.sort(kind='quicksort')
        if self.total:raw.flush()
        unique_path=self.path.with_suffix('.unique.f64')
        counts_path=self.path.with_suffix('.counts.i64')
        self.distinct=0
        pending=None
        with unique_path.open('wb') as vf,counts_path.open('wb') as cf:
            for start in range(0,self.total,500000):
                values,counts=np.unique(raw[start:start+500000],return_counts=True)
                if pending is not None:
                    if values[0]==pending[0]:counts[0]+=pending[1]
                    else:
                        np.asarray([pending[0]],dtype='<f8').tofile(vf)
                        np.asarray([pending[1]],dtype='<i8').tofile(cf)
                        self.distinct+=1
                values[:-1].astype('<f8',copy=False).tofile(vf)
                counts[:-1].astype('<i8',copy=False).tofile(cf)
                self.distinct+=len(values)-1
                pending=(values[-1],counts[-1])
            if pending is not None:
                np.asarray([pending[0]],dtype='<f8').tofile(vf)
                np.asarray([pending[1]],dtype='<i8').tofile(cf)
                self.distinct+=1
        if self.total:raw._mmap.close()
        self.path.unlink()
        self.values=np.memmap(unique_path,dtype='<f8',mode='r',shape=(self.distinct,)) if self.distinct else np.array([],dtype=float)
        self.frequency=np.memmap(counts_path,dtype='<i8',mode='r',shape=(self.distinct,)) if self.distinct else np.array([],dtype=np.int64)
        self.cumulative=np.memmap(self.path.with_suffix('.cumulative.i64'),dtype='<i8',mode='w+',shape=(self.distinct,)) if self.distinct else np.array([],dtype=np.int64)
        if self.distinct:np.cumsum(self.frequency,out=self.cumulative)
        return self

    def transform(self, values):
        if not self.total:
            raise ValueError('Cannot normalize against an empty reference pool')
        indexes=np.searchsorted(self.values,values,side='right')
        return np.where(indexes>0,self.cumulative[np.maximum(indexes-1,0)],0)/self.total

    def save(self,path):
        np.savez_compressed(path,values=self.values,counts=self.frequency)

    def close(self):
        for name in ('values','frequency','cumulative'):
            array=getattr(self,name,None)
            if isinstance(array,np.memmap):array._mmap.close()
        if self._temporary:self._temporary.cleanup()


def clustered_ols(x, y, clusters):
    """OLS + CR1; rank deficiency is reported rather than hidden by a pseudo-inverse."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.ndim != 2 or len(y) != len(x) or len(clusters) != len(y):
        raise ValueError('Regression arrays have incompatible dimensions')
    n, k = x.shape
    rank = int(np.linalg.matrix_rank(x)) if n else 0
    labels = list(dict.fromkeys(clusters))
    result = dict(n=n, parameters=k, rank=rank, histories=len(labels),
                  estimator=REGRESSION_NOTE, coefficients=None)
    if n <= k or rank < k:
        result['status'] = 'insufficient_rows_or_rank'
        return result
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ beta
    scores = defaultdict(lambda: np.zeros(k))
    for label, score in zip(clusters, x * residual[:, None]):
        scores[label] += score
    result.update(status='executed', residual_sum_squares=float(residual @ residual),
                  coefficients=[float(b) for b in beta], standard_errors=None, ci95=None)
    if len(scores) > 1:
        bread = np.linalg.inv(x.T @ x)
        meat = sum(np.outer(s, s) for s in scores.values())
        correction = len(scores) / (len(scores) - 1) * (n - 1) / (n - k)
        covariance = correction * bread @ meat @ bread
        standard_errors = np.sqrt(np.maximum(0, np.diag(covariance)))
        critical = float(student_t.ppf(.975, len(scores) - 1))
        result.update(standard_errors=standard_errors.tolist(),
                      ci95=np.column_stack((beta-critical*standard_errors,
                                            beta+critical*standard_errors)).tolist(),
                      covariance=covariance.tolist(), cluster_df=len(scores)-1)
    return result


def _actors(snapshot):
    return {int(a['actor']): a for a in snapshot['actors']}


def _actor_metric(actor, metric):
    if metric == 'degree':
        return actor['degree0'] + actor['degree1']
    if metric == 'clustering':
        return (actor['clustering0'] + actor['clustering1']) / 2
    if metric == 'spillover':
        return actor['spillover_fraction']
    return actor['utility']


def _load_verified(index_path):
    raw = (Path(index_path).read_bytes() if not isinstance(index_path, dict) else
           json.dumps(index_path,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
    index = json.loads(raw)
    # Keep the exact atomic input read, even if the controller publishes a newer index.
    index['_analysis_index_sha256'] = hashlib.sha256(raw).hexdigest()
    index['_analysis_index_bytes'] = raw
    receipts, seen = [], {}
    for entry in index.get('cases', []):
        receipt = json.loads((ROOT / entry).read_text()) if isinstance(entry, str) else entry
        case_id = receipt['identity']['case']['case_id']
        identity = receipt['identity']
        if not identity['program_sha256'].startswith('reference:'):
            raise ValueError('Reference report cannot combine candidate outcomes into its baseline CDF')
        if case_id in seen:
            if seen[case_id] != receipt['trajectory_sha256']:
                raise ValueError('Conflicting completed outcomes for one declared case')
            continue
        path = ROOT / receipt['trajectory_path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != receipt['trajectory_sha256']:
            raise ValueError('Completed trajectory hash mismatch: ' + str(path))
        seen[case_id] = receipt['trajectory_sha256']
        receipts.append(receipt)
    engines = {r['identity']['engine_sha256'] for r in receipts}
    programs = {r['identity']['program_sha256'] for r in receipts}
    if len(engines) > 1 or len(programs) > 1:
        raise ValueError('Reference report requires one frozen engine and reference program')
    return index, sorted(receipts, key=lambda r: r['case_id'])


def _load(receipt):
    path = ROOT / receipt['trajectory_path']
    opener = {'.gz':gzip.open, '.xz':lzma.open}.get(path.suffix)
    if opener is None:
        raise ValueError('Unsupported trajectory codec: ' + str(path))
    with opener(path, 'rt') as f:
        data = json.load(f)
    case = receipt['identity']['case']
    trajectory = data['trajectory']
    if len(trajectory) != case['horizon'] + 1:
        raise ValueError('Incomplete trajectory: ' + case['case_id'])
    if [int(s['round']) for s in trajectory] != list(range(case['horizon'] + 1)):
        raise ValueError('Trajectory must record every integer round, including0')
    for snapshot in trajectory:
        if len(_actors(snapshot)) != case['n']:
            raise ValueError('Missing or duplicate actor in trajectory')
    return data


def _target(case, name):
    main = case['n'] == 40 and case['sampling'] == 'random'
    changed = case['cost_before'] != case['cost_after']
    ll = _condition(case) == 'LL'
    medium = 26 if case['n'] == 40 else 66
    if name == 'Figure2':
        return main and case['p'] == 0 and (changed or ll)
    if name == 'Figure3':
        return main and changed and case['shock_count'] == 26 and case['p'] <= .5
    if name == 'Figure5':
        return main and case['d'] == case['e'] == 1.2 and case['repetition'] == 0 and (not changed or case['shock_count'] == 26)
    if name == 'Figure6':
        return main and changed
    if name == 'Figure7':
        return main and changed and case['shock_count'] == 26
    if name == 'TableS1':
        return main and not changed
    if name == 'S1':
        return case['p'] == 0 and (changed or ll)
    if name == 'S2':
        return changed
    if name == 'S3':
        return case['n'] == 100 and case['p'] == 0 and (changed or ll)
    if name == 'S4':
        return case['n'] == 100 and changed and case['shock_count'] == medium
    return False


def _coverage(completed_ids):
    declared = reference_cases()
    rows = []
    for target in ('Figure2', 'Figure3', 'Figure5', 'Figure6', 'Figure7', 'TableS1', 'S1', 'S2', 'S3', 'S4'):
        ids = {c['case_id'] for c in declared if _target(c, target)}
        complete = len(ids & completed_ids)
        rows.append(dict(target=target, implemented=True, declared_cases=len(ids), completed_cases=complete,
                         remaining_cases=len(ids)-complete,
                         execution_status='complete' if complete == len(ids) else 'partial' if complete else 'pending',
                         reproduction_status='not_established',
                         limitations='Source ambiguities and declared v2 reconstruction choices remain; completion alone is not reproduction.'))
    return rows


SOURCE_AMBIGUITIES = {
    'published_grid_repetitions': 'Historical grid/seed/repetition metadata remain unavailable. The declared source-anchored grid and five repeats can be a documented v2 methodological choice under a verified explicit user decision, without claiming historical replication.',
    'scheduler_and_sampling': 'Paper prose and executable scheduling/search differ. A verified explicit user decision can select pinned source behavior as primary and paper-directed behavior as sensitivity; the historical discrepancy remains documented.',
    'smart_search_executable': 'The dormant original smart-add routine can return a candidate inconsistent with its gain; the active main is random. Source-smart behavior must not be silently repaired or skipped.',
    'regression_grouping': 'The published mixed-effect grouping/covariance are unidentified; this report reconstructs clustered OLS, with history rather than nodes as the sampling unit.',
    'neighbor_exposure': 'Equation8 counts layer edges whereas original nodal analysis counts unique neighbors; both versions are exported.',
    'cdf_reference_pool': 'The main article refers to N40 random-search conditions. Each scheduler interpretation has its own N40 random pool; supplemental N/search methods have separate reconstructed pools. Retained CDF times, tie handling and the supplemental pooling specification are unidentified. Every method pool spans all its conditions, actors and101 times, shared by pre/post and shock groups.',
    'figure3_color_transform': 'Published Figure3 has a0–1 colorbar but its utility transformation is not specified; raw terminal utility is the primary report.',
    'figure5_graph_settings': 'Published Figure5 does not specify cost, shock condition, selected layer, time or example seed; v2 examples disclose all settings.',
    's1_caption_shock_counts': 'SupplementS1 has three shock-level columns but its caption says26 shocked and includes N100; v2 uses the explicit Figure2/S3 count grids.',
}


def _sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()


def _relative(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(Path(path).resolve())


def _behavior_binding(decisions,engine_sha256):
    """Verify the recorded user precedence; it resolves only two named choices."""
    binding=decisions.get('behavior_precedence',{})
    errors=[];paths=[];authority={}

    def anchor(record):
        if not isinstance(record,dict) or not record.get('path') or not record.get('sha256'):
            raise ValueError('Missing path/hash anchor')
        path=(ROOT/record['path']).resolve()
        path.relative_to(ROOT.resolve())
        if _sha(path)!=record['sha256']:raise ValueError('Anchor hash mismatch: '+record['path'])
        paths.append(_relative(path))
        return path

    if not binding:
        return dict(valid=False,errors=['No explicit primary-behavior decision binding'],source_paths=[])
    try:
        authority=json.loads(anchor(binding.get('authority')).read_text())
        anchor(binding.get('source_mapping'))
        expected=dict(primary='source_executable',sensitivity=['paper_directed'],outcome_independent=True,
                      upstream_commit='b3d7737613578da260fee561b6f73122dc4f2ab0',engine_sha256=engine_sha256)
        for key,value in expected.items():
            if binding.get(key)!=value or authority.get(key)!=value:
                errors.append('Precedence identity mismatch: '+key)
        if authority.get('schema')!='paper-primary-reference-decision-v1' or authority.get('campaign_id')!='paper_trajectory_v2':
            errors.append('Unexpected user-decision schema/campaign')
        required={'scheduler_and_sampling_precedence','absence_of_original_seeds_is_not_itself_a_discovery_blocker',
                  'disagreement_between_tracks_is_not_itself_a_discovery_blocker','paper_derived_settings_override_hardcoded_batch_defaults'}
        if not required.issubset(set(authority.get('resolved_by_this_decision',[]))):
            errors.append('User decision does not authorize the declared methodological choices')
        settings=authority.get('settings_and_overrides',{})
        for key,value in dict(independent_triangle_spillover_grid=GRID,fixed_reference_noise=NOISE,
                              repetitions=5,main_n=40,supplement_n=100,m=10,
                              formation_observation=50,terminal_observation=100,
                              main_shock_counts=[13,26,40],supplement_shock_counts=[33,66,100]).items():
            if settings.get(key)!=value:errors.append('Declared experimental setting mismatch: '+key)
        evidence=authority.get('equivalence_evidence',{})
        check_name='docs/paper_trajectory_v2/engine_checks.json'
        if check_name not in evidence:errors.append('Missing source-equivalence receipt')
        for name,digest in evidence.items():
            evidence_path=anchor(dict(path=name,sha256=digest))
            if name==check_name:
                checks=json.loads(evidence_path.read_text())
                if checks.get('pass') is not True or checks.get('engine_sha256')!=engine_sha256 or checks.get('checks',0)<=0:
                    errors.append('Source-equivalence receipt does not confirm this engine')
    except (OSError,ValueError,TypeError,KeyError) as failure:
        errors.append(str(failure))
    return dict(valid=not errors,errors=errors,source_paths=sorted(set(paths)),
                authority=binding.get('authority'),source_mapping=binding.get('source_mapping'),
                primary=binding.get('primary'),sensitivity=binding.get('sensitivity'),
                upstream_commit=binding.get('upstream_commit'),engine_sha256=binding.get('engine_sha256'),
                outcome_independent=binding.get('outcome_independent'),decision_id=authority.get('decision_id'),
                interpretation_note='Prospective source-fidelity choice made after partial outputs existed; it does not recover historical production behavior or select a favorable result.')


def _resolution_evidence(resolution):
    """A resolution cannot clear a blocker using missing or altered evidence."""
    errors=[];paths=[]
    records=resolution.get('evidence',[]) if isinstance(resolution,dict) else []
    if not isinstance(records,list) or not records:
        return dict(valid=False,errors=['Resolution has no path/hash evidence'],source_paths=[])
    for record in records:
        try:
            if not isinstance(record,dict):raise ValueError('Evidence must contain path/hash records')
            name,digest=record.get('path'),record.get('sha256')
            if not isinstance(name,str) or not name or Path(name).is_absolute():
                raise ValueError('Evidence path must be repository-relative')
            relative=Path(name)
            if '..' in relative.parts or relative.as_posix()!=name:
                raise ValueError('Evidence path is not canonical: '+name)
            path=(ROOT/relative).resolve()
            path.relative_to(ROOT.resolve())
            if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('Invalid evidence SHA256: '+name)
            if _sha(path)!=digest:raise ValueError('Resolution evidence hash mismatch: '+name)
            paths.append(name)
        except (OSError,ValueError,TypeError,KeyError) as failure:
            errors.append(str(failure))
    return dict(valid=not errors,errors=errors,source_paths=sorted(set(paths)))


def _contrast(records,low,high,value,matching_fields):
    """Compare only shared parameter/repetition cells; noise seeds are distinct."""
    a,b=defaultdict(list),defaultdict(list)
    for row in records:
        if row.get(value) is None:continue
        key=tuple(row[field] for field in matching_fields)
        if low(row):a[key].append(float(row[value]))
        if high(row):b[key].append(float(row[value]))
    shared=sorted(a.keys()&b.keys())
    left=[statistics.mean(a[k]) for k in shared]
    right=[statistics.mean(b[k]) for k in shared]
    low_n=sum(len(a[k]) for k in shared);high_n=sum(len(b[k]) for k in shared)
    return dict(low_cases=low_n,high_cases=high_n,matched_cells=len(shared),
                available_low_cases=sum(map(len,a.values())),available_high_cases=sum(map(len,b.values())),
                unmatched_low_cases=sum(map(len,a.values()))-low_n,
                unmatched_high_cases=sum(map(len,b.values()))-high_n,
                matching_fields=list(matching_fields),
                matching_note='Equal-weight contrasts over shared parameter/repetition cells; differing noise/reward values have distinct random seeds, so this is not a paired-random-history estimator.',
                low_mean=statistics.mean(left) if shared else None,
                high_mean=statistics.mean(right) if shared else None,
                difference=statistics.mean(y-x for x,y in zip(left,right)) if shared else None)


def _comparisons(target,endpoints,effects,regressions,statuses,drift_rows,examples):
    """Source-anchored descriptive tests; never convert a mismatch into agreement."""
    comparisons=[]
    if target in ('Figure2','S1','S3'):
        selected=[r for r in effects if _target(r,target) and r['p']==0]
        for method in sorted({_method(r) for r in selected}):
            for condition in ('LH','HL'):
                for metric in METRICS if target!='S1' else ('utility',):
                    group=[r for r in selected if _method(r)==method and r['condition']==condition and r['metric']==metric]
                    value=_contrast(group,lambda r:r['d']==0,lambda r:r['d']==2,'normalized',
                                    ('e','p','cost_before','cost_after','shock_count','repetition'))
                    comparisons.append(dict(method=method,condition=condition,metric=metric,
                                            reference='Higher triangle incentives tend to increase resilience/flexibility.',
                                            comparison='d2 minus d0 over shared e/noise/cost/shock/repetition cells',
                                            expected_sign=1,**value))
    elif target=='Figure3':
        selected=[r for r in endpoints if _target(r,target) and r['d']>=1.2]
        for method in sorted({_method(r) for r in selected}):
            for condition in ('LH','HL'):
                group=[r for r in selected if _method(r)==method and r['condition']==condition]
                value=_contrast(group,lambda r:r['p']==0,lambda r:r['p']==.5,'post_utility',
                                ('d','e','cost_before','cost_after','shock_count','repetition'))
                comparisons.append(dict(method=method,condition=condition,
                                        reference='Noise can increase terminal utility above the triangle-reward threshold near1.',
                                        comparison='p.5 minus p0, d>=1.2; shared d/e/cost/shock/repetition cells; raw utility',expected_sign=1,**value))
    elif target in ('Figure6','S2'):
        for fit in regressions:
            if fit['exposure']!='paper_layer_weighted' or (target=='Figure6' and (fit['n'],fit['sampling'])!=(40,'random')):
                continue
            for predictor,expected in [('pre_statistic',1),('triangle_payoff',1),('shocked',-1 if fit['condition']=='LH' else 1)]:
                coefficient=None if fit['coefficients'] is None else fit['coefficients'][PREDICTORS.index(predictor)]
                comparisons.append(dict(method=[fit['interpretation'],fit['n'],fit['sampling']],condition=fit['condition'],metric=fit['metric'],
                                        predictor=predictor,reference='Published qualitative marginal-effect direction.',
                                        difference=coefficient,expected_sign=expected,fit_status=fit['status'],
                                        reconstruction='History-clustered OLS; unidentified published mixed-effect model remains a separate ambiguity.'))
    elif target in ('Figure7','S4'):
        n=40 if target=='Figure7' else 100
        selected=[r for r in endpoints if _target(r,target)]
        for method in sorted({_method(r) for r in selected}):
            for condition in ('LH','HL'):
                for metric in METRICS:
                    for shocked in (False,True):
                        group=[r for r in selected if _method(r)==method and r['condition']==condition]
                        if condition=='LH':expected=-1 if shocked or metric in ('clustering','spillover') else 1
                        elif metric=='clustering':expected=-1 if shocked else 1
                        elif metric=='spillover':expected=1 if shocked else -1
                        else:expected=1
                        value=_contrast(group,lambda r:r['p']==0,lambda r:r['p']==.75,
                                        f'post_{metric}_'+('shocked' if shocked else 'unshocked'),
                                        ('d','e','cost_before','cost_after','shock_count','repetition'))
                        comparisons.append(dict(method=method,condition=condition,metric=metric,shocked=shocked,
                                                reference='Published shocked/unshocked noise direction; weak/unshocked changes may be negligible.',
                                                comparison='p.75 minus p0 over shared d/e/cost/shock/repetition cells',expected_sign=expected,**value))
    elif target=='TableS1':
        published={'LL':[(0,0), (66.39,254.73),(34.70,195.82),(11.93,96.63)],
                   'HH':[(0,0),(8.08,29.98),(22.17,68.34),(40.62,131.95)]}
        for row in drift_rows:
            if (row['n'],row['sampling'])!=(40,'random'):continue
            mean,sd=published[row['condition']][NOISE.index(row['p'])]
            comparisons.append(dict(method=_method(row),condition=row['condition'],p=row['p'],
                                    published_mean=mean,published_sd=sd,published_nodal_observations=21600,
                                    observed_mean=row['mean'],observed_sd=row['sd'],observed_nodal_observations=row['observations'],
                                    independent_histories=row['histories'],difference=row['mean']-mean,
                                    matches_published_rounding=abs(row['mean']-mean)<=.005 and row['sd'] is not None and abs(row['sd']-sd)<=.005,
                                    reference='Published TableS1 numerical moments; exact seeds/data unavailable; v2 removes redundant no-shock nominal shock-count copies.'))
    elif target=='Figure5':
        for key,(case,adjacency) in sorted(examples.items()):
            if (case['n'],case['sampling'])!=(40,'random'):continue
            layer_edges=[sum(int(x) for x in layer) for layer in adjacency]
            comparisons.append(dict(method=_method(case),condition=_condition(case),p=case['p'],
                                    case_id=case['case_id'],seed=case['seed'],repetition=case['repetition'],
                                    layer_densities=[x/(case['n']*(case['n']-1)/2) for x in layer_edges],
                                    reference='Published illustrative density/clustering pairs are retained in source_methods.md; exact graph condition and seed are unknown.',
                                    exact_comparison_identifiable=False))
    if target=='TableS1':
        agreement=bool(comparisons) and all(r['matches_published_rounding'] for r in comparisons)
        evaluated=bool(comparisons)
    elif target=='Figure5':
        agreement=False; evaluated=bool(comparisons)
    else:
        evaluated=bool(comparisons) and all(r.get('difference') is not None for r in comparisons)
        agreement=evaluated and all(r['difference']*r['expected_sign']>=0 for r in comparisons)
    return dict(status='executed_agreement' if agreement else 'executed_discrepant' if evaluated else 'pending',
                consequential=not agreement,
                justification='Descriptive, source-anchored contrasts; no equivalence test or automatic waiver of scientific discrepancies.',
                values=comparisons)


def _reference_report(index_path,index,receipts,output,summary,endpoints,effects,regressions,statuses,drift_rows,examples):
    declared=reference_cases();completed={r['case_id'] for r in receipts}
    declared_ids={c['case_id'] for c in declared}
    index_sha=index['_analysis_index_sha256']
    decisions_path=ROOT/'experiments/paper_trajectory_v2/analysis_decisions.json'
    decisions=json.loads(decisions_path.read_text()) if decisions_path.exists() else {}
    resolutions=decisions.get('resolutions',{})
    resolution_evidence={key:_resolution_evidence(value) for key,value in resolutions.items()}
    reviews=decisions.get('comparison_reviews',{})
    review_evidence={key:_resolution_evidence(value) for key,value in reviews.items()}
    engine_sha256=receipts[0]['identity']['engine_sha256'] if receipts else index.get('engine_sha256')
    behavior=_behavior_binding(decisions,engine_sha256)
    source_paths=['docs/paper_trajectory_v2/source_methods.md','docs/paper_trajectory_v2/source_provenance.json',
                  'docs/paper_trajectory_v2/sources/article.xml','docs/paper_trajectory_v2/sources/article.pdf',
                  'docs/paper_trajectory_v2/sources/supplement.pdf','docs/paper_trajectory_v2/sources/upstream_tree.json']
    code_paths=['paper_trajectory_v2/analysis.py','paper_trajectory_v2/design.py']
    if decisions_path.exists():
        source_paths.append(_relative(decisions_path))
    source_paths.extend(path for path in behavior['source_paths'] if path not in source_paths)
    for checked in [*resolution_evidence.values(),*review_evidence.values()]:
        source_paths.extend(path for path in checked['source_paths'] if path not in source_paths)
    dependency_ambiguities={
        'Figure2':['published_grid_repetitions','scheduler_and_sampling'],
        'Figure3':['published_grid_repetitions','scheduler_and_sampling','figure3_color_transform'],
        'Figure4':[],
        'Figure5':['scheduler_and_sampling','figure5_graph_settings'],
        'Figure6':['published_grid_repetitions','scheduler_and_sampling','regression_grouping','neighbor_exposure','cdf_reference_pool'],
        'Figure7':['published_grid_repetitions','scheduler_and_sampling'],
        'TableS1':['published_grid_repetitions','scheduler_and_sampling'],
        'S1':['published_grid_repetitions','scheduler_and_sampling','smart_search_executable','s1_caption_shock_counts'],
        'S2':['published_grid_repetitions','scheduler_and_sampling','smart_search_executable','regression_grouping','neighbor_exposure','cdf_reference_pool'],
        'S3':['published_grid_repetitions','scheduler_and_sampling'],
        'S4':['published_grid_repetitions','scheduler_and_sampling']}
    panels=[]
    for target in ('Figure2','Figure3','Figure4','Figure5','Figure6','Figure7','S1','S2','S3','S4','TableS1'):
        expected={c['case_id'] for c in declared if _target(c,target)}
        done=expected&completed
        ambiguities=[]
        for key in dependency_ambiguities[target]:
            resolution=resolutions.get(key,{})
            checked=resolution_evidence.get(key,dict(valid=False,errors=['No recorded resolution'],source_paths=[]))
            # A declared, justified interpretation resolves a v2 choice, not historical provenance.
            resolved=(resolution.get('status')=='resolved_for_v2' and bool(resolution.get('justification')) and
                      checked['valid'] and bool(resolution.get('classification')) and resolution.get('consequential') is False)
            methodological=key in ('scheduler_and_sampling','published_grid_repetitions')
            if methodological:
                resolved=resolved and behavior['valid'] and resolution.get('classification')=='declared_methodological_choice'
            ambiguities.append(dict(id=key,source_issue=SOURCE_AMBIGUITIES[key],resolved_for_v2=resolved,
                                    classification=resolution['classification'] if resolved else 'unresolved',
                                    authority_binding_valid=behavior['valid'] if methodological else None,
                                    evidence_valid=checked['valid'],evidence_errors=checked['errors'],
                                    resolution=resolution or None))
        blocking=[a['id'] for a in ambiguities if not a['resolved_for_v2']]
        configuration=dict(grid=GRID,noise=NOISE,source_anchored_repetitions=5,
                           main_n=40,supplement_n=100,shock_time=50,horizon=100,
                           interpretations=['source_executable','paper_directed'],
                           methods=[[40,'random'],[40,'smart'],[100,'random']])
        if behavior['valid']:
            configuration.update(primary_interpretation='source_executable',sensitivity_interpretations=['paper_directed'],
                                 precedence_authority=behavior['authority'],source_behavior_mapping=behavior['source_mapping'])
        execution='complete' if expected and done==expected else 'partial' if done else 'pending'
        comparison=_comparisons(target,endpoints,effects,regressions,statuses,drift_rows,examples)
        if target=='Figure4':
            fixture_path=ROOT/'docs/paper_trajectory_v2/figure4_fixture.json'
            if fixture_path.exists():
                fixture=json.loads(fixture_path.read_text())
                configuration.update(fixture_path=_relative(fixture_path),fixture_sha256=_sha(fixture_path),
                                     engine_fixture=dict(path=_relative(fixture_path),sha256=_sha(fixture_path)))
                checks=fixture.get('checks',[])
                executed=fixture.get('executed') is True and bool(checks) and all(c.get('passed') is True for c in checks)
                engines={r['identity']['engine_sha256'] for r in receipts}
                if not engines and index.get('engine_sha256'):
                    engines.add(index['engine_sha256'])
                if len(engines)!=1 or fixture.get('engine_sha256') not in engines:
                    executed=False;blocking.append('fixture_engine_identity')
                execution='complete' if executed else 'pending'
                comparison=fixture.get('reference_comparison',dict(status='pending',consequential=True,justification='Fixture comparison receipt missing.'))
                comparison=dict(comparison)
                comparison['status']={'agreement':'executed_agreement','discrepant':'executed_discrepant'}.get(comparison.get('status'),comparison.get('status','pending'))
                comparison.setdefault('consequential',comparison['status']!='executed_agreement')
                comparison.setdefault('justification',comparison.get('qualification','Executable fixture compared with the source mechanism.'))
            else:
                comparison=dict(status='pending',consequential=True,justification='Actual executable fixture receipt not yet available.')
        elif execution!='complete':
            comparison['descriptive_subset_status']=comparison['status']
            comparison['status']='pending'
        if behavior['valid']:
            comparison.update(agreement_between_interpretations_required=False,
                              historical_seed_recovery_required=False,
                              interpretation_roles={'source_executable':'primary','paper_directed':'sensitivity'},
                              discrepancy_policy='Retain descriptive non-reproduction. Explained implementation/publication differences may receive an evidenced methodological review; unresolved numerical/evaluator defects remain blocking.')
            for value in comparison.get('values',[]):
                method=value.get('method')
                if method:value['interpretation_role']='primary' if method[0]=='source_executable' else 'sensitivity'
        review=reviews.get(target,{})
        checked=review_evidence.get(target,dict(valid=False,errors=['No recorded comparison review'],source_paths=[]))
        if review:
            comparison.update(review_evidence_valid=checked['valid'],review_evidence_errors=checked['errors'])
            if not checked['valid']:blocking.append('invalid_comparison_review_evidence:'+target)
        if comparison['status']=='executed_discrepant' and review.get('consequential') is False and review.get('justification') and checked['valid']:
            comparison.update(consequential=False,discrepancy_review=review)
        comparison_complete=(comparison.get('status')=='executed_agreement' or
                             (comparison.get('status')=='executed_discrepant' and comparison.get('consequential') is False))
        panels.append(dict(id=target,source=source_paths,code=code_paths,configuration=configuration,
                           expected_case_ids=sorted(expected),executed_case_ids=sorted(done),
                           execution_status=execution,comparison=comparison,
                           discrepancies=[r for r in comparison.get('values',[]) if (r.get('difference') is not None and r.get('expected_sign') is not None and r['difference']*r['expected_sign']<0) or r.get('matches_published_rounding') is False or r.get('exact_comparison_identifiable') is False],
                           ambiguities=ambiguities,consequential_ambiguities=blocking,
                           complete=execution=='complete' and comparison_complete and not blocking))
    baseline_paths=['utility_cdf_reference.json']
    for pool in summary['utility_cdf']['pools']:
        baseline_paths.extend([pool['pool_file'],pool['metadata_file']])
    baseline_files={_relative(output/name):_sha(output/name) for name in baseline_paths}
    blockers=sorted({issue for panel in panels for issue in panel['consequential_ambiguities']})
    blockers.extend('invalid_resolution_evidence:'+key for key,checked in sorted(resolution_evidence.items()) if not checked['valid'])
    blockers.extend('invalid_comparison_review_evidence:'+key for key,checked in sorted(review_evidence.items())
                    if not checked['valid'] and 'invalid_comparison_review_evidence:'+key not in blockers)
    if completed != declared_ids:blockers.append('reference_matrix_incomplete_or_extra_cases')
    return dict(schema_version=1,campaign_id='paper_trajectory_v2',index_sha256=index_sha,
                index_snapshot_path=_relative(output/'reference-index.snapshot.json'),
                engine_sha256=engine_sha256,
                program_sha256=receipts[0]['identity']['program_sha256'] if receipts else None,
                declared_cases=len(declared_ids),verified_completed_cases=len(completed),
                baseline_identity=dict(index_sha256=index_sha,files=baseline_files),
                panels=panels,blocking_ambiguities=blockers,
                decisions_path=_relative(decisions_path) if decisions_path.exists() else None,
                decisions_sha256=_sha(decisions_path) if decisions_path.exists() else None,
                behavior_precedence=behavior,
                resolution_evidence=resolution_evidence,
                comparison_review_evidence=review_evidence,
                complete=completed==declared_ids and all(p['complete'] for p in panels) and not blockers,
                figure1_empirical=dict(status='unavailable_provenance',required_for_simulation_gate=False),
                source_note='A resolved v2 interpretation never establishes the undocumented historical publication detail.')


def generate_report(index_path, output_dir):
    """Read completed reference-index receipts and write summaries and static figures."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    index, receipts = _load_verified(index_path)
    (output/'reference-index.snapshot.json').write_bytes(index.pop('_analysis_index_bytes'))
    cdfs, endpoints, nodes, examples = {}, [], defaultdict(list), {}
    pool_cases=defaultdict(list)
    controls, drift = defaultdict(list), defaultdict(lambda: ([], []))
    tables={}
    (output/'tables').mkdir(exist_ok=True)
    nodal_fields = ['case_id','round','actor','degree','clustering','utility','shocked',
                    'spillover_numerator','spillover_denominator','spillover_ratio','spillover_fraction_source_zero',
                    'clustering_ratio0','clustering_ratio1',
                    'paper_exposure_numerator','paper_exposure_denominator','paper_exposure_fraction',
                    'source_exposure_numerator','source_exposure_denominator','source_exposure_ratio','source_exposure_fraction']
    for receipt in receipts:
        case = receipt['identity']['case']
        method=_method(case)
        if method not in cdfs:cdfs[method]=EmpiricalCDF()
        pool_cases[method].append(case['case_id'])
        if method not in tables:
            prefix=f'{method[0]}_N{method[1]}_{method[2]}'
            tables[method]=(output/'tables'/f'{prefix}_network_trajectories.csv.gz',
                            output/'tables'/f'{prefix}_nodal_endpoint_metrics.csv.gz')
            with gzip.open(tables[method][0],'wt',newline='') as f:
                csv.writer(f).writerow(['case_id','round',*METRICS])
            with gzip.open(tables[method][1],'wt',newline='') as f:
                csv.writer(f).writerow(nodal_fields)
        trajectory_path,nodal_path=tables[method]
        data = _load(receipt)
        times = data['trajectory']
        cdfs[method].add([a['utility'] for snapshot in times for a in snapshot['actors']])
        pre, post = _actors(times[50]), _actors(times[100])
        recipients = set(int(i) for i in data['shock_recipients'])
        if len(recipients) != case['shock_count']:
            raise ValueError('Shock recipient count differs from declared case')
        row = {**case, 'condition': _condition(case), 'history': _history(case),
               'trajectory_path': receipt['trajectory_path'], 'trajectory_sha256': receipt['trajectory_sha256']}
        for metric in METRICS:
            row['pre_' + metric] = statistics.mean(_actor_metric(a, metric) for a in pre.values())
            row['post_' + metric] = statistics.mean(_actor_metric(a, metric) for a in post.values())
            for shocked in (False,True):
                values=[_actor_metric(a,metric) for actor,a in post.items() if (actor in recipients)==shocked]
                row[f'post_{metric}_'+('shocked' if shocked else 'unshocked')]=statistics.mean(values) if values else None
        endpoints.append(row)
        if row['condition'] == 'LL':
            controls[(*_method(case), case['d'], case['e'], case['p'])].append(row)
        if row['condition'] in ('LL', 'HH'):
            values, clusters = drift[(*_method(case), row['condition'], case['p'])]
            values.extend(post[i]['utility'] - pre[i]['utility'] for i in pre)
            clusters.extend([_history(case)] * case['n'])
        if row['condition'] in ('LH', 'HL'):
            # N x (pre/post four metrics + source/paper exposure + shocked), compact arrays.
            array = np.array([[_actor_metric(pre[i], metric) for metric in METRICS] +
                              [_actor_metric(post[i], metric) for metric in METRICS] +
                              [pre[i]['exposure']['paper_fraction'],
                               pre[i]['exposure']['source_union_fraction'], float(i in recipients)]
                              for i in sorted(pre)], dtype=float)
            nodes[(*_method(case), row['condition'])].append((case, array))
        if case['d'] == case['e'] == 1.2 and case['repetition'] == 0 and (
                case['shock_count'] in (0, 26 if case['n'] == 40 else 66)):
            examples[(*_method(case), row['condition'], case['p'])] = (case, data['adjacency']['100'])
        # Retain per-case network trajectories; all nodes/edges remain in hashed source files.
        with gzip.open(trajectory_path,'at',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['case_id','round',*METRICS])
            for snapshot in times:
                w.writerow(dict(case_id=case['case_id'],round=snapshot['round'],
                                **{k:snapshot['network'][v] for k,v in NETWORK_KEYS.items()}))
        with gzip.open(nodal_path,'at',newline='') as f:
            w=csv.DictWriter(f,fieldnames=nodal_fields)
            for round_number,actors in ((50,pre),(100,post)):
                for actor_id,a in actors.items():
                    x=a['exposure']
                    w.writerow(dict(case_id=case['case_id'],round=round_number,actor=actor_id,
                                    degree=_actor_metric(a,'degree'),clustering=_actor_metric(a,'clustering'),
                                    utility=a['utility'],shocked=actor_id in recipients,
                                    spillover_numerator=2*a['overlap'],
                                    spillover_denominator=a['degree0']+a['degree1'],
                                    spillover_ratio=a.get('spillover_ratio'),
                                    spillover_fraction_source_zero=a['spillover_fraction'],
                                    clustering_ratio0=a.get('clustering_ratio0'),clustering_ratio1=a.get('clustering_ratio1'),
                                    paper_exposure_numerator=x['paper_numerator'],
                                    paper_exposure_denominator=x['paper_denominator'],
                                    paper_exposure_fraction=x['paper_fraction'],
                                    source_exposure_numerator=x['source_union_numerator'],
                                    source_exposure_denominator=x['source_union_denominator'],
                                    source_exposure_ratio=x.get('source_union_ratio'),
                                    source_exposure_fraction=x['source_union_fraction']))
    _csv(output/'case_endpoints.csv', endpoints)
    (output/'cdf').mkdir(exist_ok=True)
    pool_metadata=[]
    for method,cdf in sorted(cdfs.items()):
        cdf.freeze()
        name=_method_name(method)
        pool_file=f'cdf/{name}.npz';metadata_file=f'cdf/{name}.json'
        cdf.save(output/pool_file)
        metadata=dict(method=list(method),observations=cdf.total,distinct_utility_values=cdf.distinct,
                      scope='Main N40 random-search conditions' if method[1:]==(40,'random') else 'Explicitly reconstructed supplemental method pool',
                      pool='All conditions, actors and101 integer times within this scheduler/N/search method only.',
                      tie_rule='Right-continuous empirical CDF: count(method reference utility <= value)/method pool size.',
                      common_for_pre_post_and_all_shock_groups=True,candidate_values_in_pool=False,
                      partial_pool_changes_only_when_this_method_gains_reference_cases=True,
                      reference_cases=pool_cases[method],pool_file=pool_file,metadata_file=metadata_file,
                      value_dtype='<f8',count_dtype='<i8',
                      storage='Exact sorted unique utilities with integer multiplicities; raw sort scratch is temporary.',
                      pool_sha256=_sha(output/pool_file))
        _dump(output/metadata_file,metadata)
        pool_metadata.append(metadata)
    cdf_metadata = dict(schema_version=2,scope='per_method',method_fields=['interpretation','n','sampling'],
                        observations=sum(c.total for c in cdfs.values()),
                        distinct_utility_values=pool_metadata[0]['distinct_utility_values'] if len(pool_metadata)==1 else None,
                        pools=pool_metadata,candidate_values_in_pool=False,
                        cross_method_pooling=False,
                        source_ambiguity=SOURCE_AMBIGUITIES['cdf_reference_pool'])
    _dump(output/'utility_cdf_reference.json', cdf_metadata)
    # The superseded global-pool artifact is not a valid normalizer for this schema.
    (output/'utility_cdf_reference.npz').unlink(missing_ok=True)

    effect_rows = []
    for row in endpoints:
        if row['condition'] not in ('LH', 'HL'):
            continue
        group = controls.get((*_method(row), row['d'], row['e'], row['p']), [])
        for metric in METRICS:
            denominator = statistics.mean(r['pre_' + metric] for r in group) if group else None
            numerator = row['post_' + metric] - row['pre_' + metric]
            value = (1 if row['condition'] == 'LH' else 0) + numerator / denominator if denominator not in (None, 0) else None
            effect_rows.append({k: row[k] for k in ('case_id','interpretation','n','sampling','condition','cost_before','cost_after','d','e','p','shock_count','repetition','seed')} |
                               dict(metric=metric, pre=row['pre_'+metric], post=row['post_'+metric],
                                    numerator_post_minus_pre=numerator, denominator_LL_at50=denominator,
                                    denominator_cases=len(group), denominator_zero=denominator == 0,
                                    denominator_near_zero=denominator is not None and abs(denominator) < 1e-12,
                                    normalization_status='missing_control' if denominator is None else 'zero_denominator' if denominator == 0 else 'defined',
                                    normalized=value, metric_name='resilience' if row['condition']=='LH' else 'flexibility'))
    _csv(output/'resilience_flexibility.csv', effect_rows)

    regressions = []
    status_rows = []
    for (interpretation, n, sampling, condition), blocks in nodes.items():
        method_cdf=cdfs[(interpretation,n,sampling)]
        for metric_index, metric in enumerate(METRICS):
            for exposure_index, exposure_name in ((8, 'paper_layer_weighted'), (9, 'source_unique_neighbor')):
                xs, ys, labels = [], [], []
                for case, array in blocks:
                    prior, final = array[:,metric_index], array[:,4+metric_index]
                    if metric == 'utility':
                        prior, final = method_cdf.transform(prior), method_cdf.transform(final)
                    shocked = array[:,10]
                    xs.append(np.column_stack((np.ones(len(array)), prior, shocked*case['p'],
                                               np.full(len(array),case['p']), array[:,exposure_index], shocked,
                                               np.full(len(array),case['e']), np.full(len(array),case['d']))))
                    ys.append(final)
                    labels.extend([_history(case)]*len(array))
                x,y=np.concatenate(xs),np.concatenate(ys)
                finite=np.all(np.isfinite(x),axis=1)&np.isfinite(y)
                fitted_labels=[label for label,keep in zip(labels,finite) if keep]
                fit = clustered_ols(x[finite],y[finite],fitted_labels)
                fit.update(total_rows_before_undefined_exclusion=len(y),
                           excluded_undefined_rows=int((~finite).sum()),
                           excluded_history_count=len(set(labels)-set(fitted_labels)),
                           undefined_handling='Paper Eq8 isolate ratios remain null and are excluded; source unique-neighbor convention assigns0 in the separate sensitivity fit.')
                fit['observations']=fit.pop('n')
                regressions.append(dict(interpretation=interpretation,n=n,sampling=sampling,condition=condition,
                                        metric='utility_cdf' if metric=='utility' else metric,
                                        cdf_pool=f'cdf/{_method_name((interpretation,n,sampling))}.json' if metric=='utility' else None,
                                        exposure=exposure_name,predictors=PREDICTORS,**fit))
        medium = 26 if n == 40 else 66
        groups = defaultdict(lambda:([],[]))
        for case, array in blocks:
            if case['shock_count'] != medium:
                continue
            for shocked in (False,True):
                selected = array[array[:,10] == int(shocked)]
                if not len(selected):
                    continue
                for j,metric in enumerate(METRICS):
                    values, clusters = groups[(case['p'], shocked, metric)]
                    values.append(float(selected[:,4+j].mean()))
                    clusters.append(_history(case))
        for (noise,shocked,metric),(values,clusters) in groups.items():
            status_rows.append(dict(interpretation=interpretation,n=n,sampling=sampling,condition=condition,
                                    p=noise,shocked=shocked,metric=metric,**_summary(values,clusters)))
    _dump(output/'regressions.json',dict(note=REGRESSION_NOTE,reference_cdf=cdf_metadata,fits=regressions))
    _csv(output/'shock_status_outcomes.csv',status_rows)
    drift_rows = [dict(interpretation=k[0],n=k[1],sampling=k[2],condition=k[3],p=k[4],
                       **_summary(values,clusters)) for k,(values,clusters) in drift.items()]
    _csv(output/'table_s1_no_shock_drift.csv',drift_rows)
    coverage = _coverage({r['case_id'] for r in receipts})
    coverage.insert(0,dict(target='Figure1',implemented=False,execution_status='unavailable_provenance',
                           reproduction_status='not_established',limitations='No original empirical data or analysis recipe in pinned code/source packet.'))
    coverage.insert(4,dict(target='Figure4',implemented=True,execution_status='pending',
                           reproduction_status='not_established',limitations='This report does not infer a passed executable barrier test from equations.'))
    artifacts = _plots(output,endpoints,effect_rows,regressions,status_rows,examples)
    summary = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
                   declared_cases=index.get('planned',34560),completed_cases=len(receipts),
                   input_index_snapshot='reference-index.snapshot.json',input_index_sha256=index['_analysis_index_sha256'],
                   reference_histories=len({_history(r['identity']['case']) for r in receipts}),
                   interpretation_methods=sorted({_method(r['identity']['case']) for r in receipts}),
                   scheduler_interpretation=SCHEDULER_NOTE,
                   coverage=coverage,utility_cdf=cdf_metadata,regression_note=REGRESSION_NOTE,
                   uncertainty='Intervals cluster complete simulated histories or related external-seed families; node counts are not independent repetitions. Incomplete parameter grids are descriptive subsets.',
                   reproduction_claim=False,source_audit='docs/paper_trajectory_v2/source_methods.md',
                   artifacts=artifacts,
                   tables={'network_trajectories':[str(pair[0].relative_to(output)) for pair in tables.values()],
                           'nodal_endpoint_metrics':[str(pair[1].relative_to(output)) for pair in tables.values()]})
    reference_report = _reference_report(index_path,index,receipts,output,summary,endpoints,effect_rows,
                                         regressions,status_rows,drift_rows,examples)
    panel_by_id={panel['id']:panel for panel in reference_report['panels']}
    for row in coverage:
        panel=panel_by_id.get(row['target'])
        if panel is None:continue
        row['execution_status']=panel['execution_status']
        row['comparison_status']=panel['comparison']['status']
        row['complete']=panel['complete']
        if row['target']=='Figure4':
            row['reproduction_status']=panel['comparison']['status']
            row['limitations']=panel['comparison'].get('justification','Actual engine fixture receipt required.')
            row['fixture']=panel['configuration'].get('engine_fixture')
    _dump(output/'coverage.json',coverage)
    lines=['# Executed reference coverage','',f"Verified completed cases: {len(receipts)} / {summary['declared_cases']}.",
           '', 'Plots use completed cases only. Blank cells are missing evidence. Numerical completion does not establish reproduction.',
           '', '| Target | Executed | Remaining | Status |','|---|---:|---:|---|']
    for row in coverage:
        lines.append(f"| {row['target']} | {row.get('completed_cases','—')} | {row.get('remaining_cases','—')} | {row['execution_status']}; {row['reproduction_status']} |")
    lines.extend(['',REGRESSION_NOTE,'','Source and implementation ambiguities remain documented in `docs/paper_trajectory_v2/source_methods.md`.'])
    (output/'coverage.md').write_text('\n'.join(lines)+'\n')
    reference_report['artifacts_sha256']={
        str(path.relative_to(output)):_sha(path)
        for path in sorted(output.rglob('*'))
        if path.is_file() and path.relative_to(output).as_posix() not in ('reference-report.json','summary.json')
    }
    _dump(output/'reference-report.json',reference_report)
    summary['reference_report']='reference-report.json'
    summary['reference_complete']=reference_report['complete']
    _dump(output/'summary.json',summary)
    for cdf in cdfs.values():cdf.close()
    return summary


def _plots(output,endpoints,effects,regressions,statuses,examples,heatmaps_only=False):
    os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'paper-trajectory-v2-matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    artifacts=[]

    def save(fig,name):
        fig.tight_layout(rect=(0,0,1,.90),h_pad=1.8,w_pad=1.5)
        fig.savefig(output/name,dpi=150,bbox_inches='tight')
        plt.close(fig);artifacts.append(name)

    fixture_path=ROOT/'docs/paper_trajectory_v2/figure4_fixture.json'
    if fixture_path.exists() and not heatmaps_only:
        fixture=json.loads(fixture_path.read_text())
        checks=fixture.get('checks',[])
        if checks:
            fig,axs=plt.subplots(len(checks),3,figsize=(11,3*len(checks)),squeeze=False)
            xy=np.array([[-.7,0],[.7,0],[0,1.]])
            for row,check in enumerate(checks):
                for col,state in enumerate(('single_edge','bridge','triangle')):
                    ax=axs[row,col];graph=check[state]
                    for bit,(a,b) in zip(graph['adjacency'][0],((0,1),(0,2),(1,2))):
                        if int(bit):ax.plot(xy[[a,b],0],xy[[a,b],1],c='#607d8b',linewidth=2)
                    ax.scatter(xy[:,0],xy[:,1],s=150,c='#1976d2',zorder=3)
                    for i,(point,utility) in enumerate(zip(xy,graph['actual_actor_utilities'])):
                        ax.text(point[0],point[1]+.12,f'{i}: u={utility:.3g}',ha='center',fontsize=9)
                    ax.set_title(f'd={check["d"]:g}: {state.replace("_"," ")}')
                    ax.set_xlim(-1.2,1.2);ax.set_ylim(-.35,1.55);ax.set_aspect('equal');ax.axis('off')
                axs[row,2].text(.5,-.04,f'actual closure gain={check["actual_closure_gain"]:.4g}',ha='center',transform=axs[row,2].transAxes)
            fig.suptitle('Figure4: actual three-actor fixture, c=.6; d=.8 is strict closure/Pareto threshold in exact arithmetic\nOriginal floating-point comparisons retained; aggregate-welfare crossover2/3 is a different criterion')
            save(fig,'Figure4_executed_barrier.png')

    def heat_values(rows,value):
        cells=defaultdict(list)
        for row in rows:
            if row.get(value) is not None:
                cells[(row['d'],row['e'])].append(row[value])
        matrix=np.full((len(GRID),len(GRID)),np.nan)
        for (d,e),values in cells.items():matrix[GRID.index(d),GRID.index(e)]=statistics.mean(values)
        return matrix,cells

    def shared_limits(panels,value='normalized'):
        matrices=[heat_values(rows,value)[0] for rows in panels]
        values=np.concatenate([matrix[np.isfinite(matrix)] for matrix in matrices])
        return (float(values.min()),float(values.max())) if len(values) else (None,None)

    def heat(ax,rows,title,value='normalized',limits=(None,None)):
        matrix,cells=heat_values(rows,value)
        im=ax.imshow(np.ma.masked_invalid(matrix),origin='lower',aspect='auto',interpolation='nearest',
                     vmin=limits[0],vmax=limits[1])
        ax.set_xticks(range(len(GRID)),[f'{x:g}' for x in GRID],fontsize=6)
        ax.set_yticks(range(len(GRID)),[f'{x:g}' for x in GRID],fontsize=6)
        ax.set_title(title+f'\n{len(rows)} case-metrics; {len(cells)}/36 cells',fontsize=8)
        ax.set_xlabel('spillover reward e',fontsize=7);ax.set_ylabel('triangle reward d',fontsize=7)
        if cells:plt.colorbar(im,ax=ax,shrink=.75)
        else:ax.text(.5,.5,'pending',ha='center',transform=ax.transAxes)

    methods=sorted({_method(row) for row in endpoints})
    for method in methods:
        interpretation,n,sampling=method;prefix=f'{interpretation}_N{n}_{sampling}'
        p_label='episode branch probability p' if interpretation=='paper_directed' else 'action noise probability p'
        selected=[r for r in effects if _method(r)==method and r['p']==0]
        counts=(13,26,40) if n==40 else (33,66,100)
        fig,axs=plt.subplots(4,6,figsize=(18,11))
        for i,metric in enumerate(METRICS):
            for direction,condition in enumerate(('LH','HL')):
                panels=[[r for r in selected if r['metric']==metric and r['condition']==condition and r['shock_count']==count] for count in counts]
                limits=shared_limits(panels)
                for j,(count,rows) in enumerate(zip(counts,panels)):
                    heat(axs[i,direction*3+j],rows,f'{metric} {condition}, shocked={count}',limits=limits)
        fig.suptitle(f'{prefix}: Eq4/5; LL reference at50; missing/zero denominators omitted\nShared scale across shock counts within each statistic and cost direction',fontsize=12)
        save(fig,f'{prefix}_'+('S3' if n==100 else 'Figure2')+'.png')
        fig,axs=plt.subplots(2,4,figsize=(13,6))
        for i,condition in enumerate(('LH','HL')):
            panels=[[r for r in endpoints if _method(r)==method and r['condition']==condition and r['p']==noise and r['shock_count']==counts[1]] for noise in NOISE]
            limits=shared_limits(panels,'post_utility')
            for j,(noise,rows) in enumerate(zip(NOISE,panels)):
                heat(axs[i,j],rows,f'{condition} p={noise:g}',value='post_utility',limits=limits)
        fig.suptitle(f'{prefix}: terminal raw mean utility; shared scale within direction\n{p_label}; published color transform unresolved; distinct models')
        save(fig,f'{prefix}_Figure3_raw_utility.png')
        if heatmaps_only:continue
        fig,axs=plt.subplots(4,2,figsize=(10,11))
        for i,metric in enumerate(METRICS):
            for j,condition in enumerate(('LH','HL')):
                ax=axs[i,j]
                for shocked in (False,True):
                    rows=sorted([r for r in statuses if _method(r)==method and r['condition']==condition and r['metric']==metric and r['shocked']==shocked],key=lambda r:r['p'])
                    if rows:
                        means=np.array([r['history_mean'] for r in rows])
                        lo=np.array([r['history_ci95'][0] if r['history_ci95'] else r['history_mean'] for r in rows])
                        hi=np.array([r['history_ci95'][1] if r['history_ci95'] else r['history_mean'] for r in rows])
                        ax.errorbar([r['p'] for r in rows],means,yerr=[means-lo,hi-means],marker='o',label='shocked' if shocked else 'unshocked')
                ax.set(title=f'{condition}: {metric}',xlabel=p_label);ax.set_xticks(NOISE)
                if ax.lines:ax.legend(fontsize=7)
        fig.suptitle(f'{prefix}: terminal status means; history95% intervals; partial grid may be unbalanced')
        save(fig,f'{prefix}_'+('S4' if n==100 else 'Figure7')+'.png')
        for condition in ('LL','HH','LH','HL'):
            fig,axs=plt.subplots(2,4,figsize=(14,7))
            any_example=False
            for col,noise in enumerate(NOISE):
                example=examples.get((*method,condition,noise))
                for layer in (0,1):
                    ax=axs[layer,col];ax.axis('off')
                    if example is None:
                        ax.set_title(f'p={noise:g}, layer{layer}: pending');continue
                    any_example=True;case,adjacency=example
                    bits=adjacency[layer]
                    if isinstance(bits,str):bits=[int(x) for x in bits]
                    if len(bits)!=n*(n-1)//2:raise ValueError('Unexpected adjacency encoding')
                    angle=np.arange(n)*2*np.pi/n
                    xy=np.column_stack((np.cos(angle),np.sin(angle)));edges=[];degrees=np.zeros(n);adj=np.zeros((n,n),dtype=int);pos=0
                    for a in range(n-1):
                        for b in range(a+1,n):
                            if bits[pos]:edges.append([xy[a],xy[b]]);degrees[a]+=1;degrees[b]+=1;adj[a,b]=adj[b,a]=1
                            pos+=1
                    triangles=np.diag(adj@adj@adj)/2
                    denominators=degrees*(degrees-1)/2
                    clustering=np.divide(triangles,denominators,out=np.zeros(n),where=denominators>0).mean()
                    ax.add_collection(LineCollection(edges,colors='#607d8b',linewidths=.35,alpha=.45))
                    ax.scatter(xy[:,0],xy[:,1],s=8,c='#1976d2');ax.set_xlim(-1.1,1.1);ax.set_ylim(-1.1,1.1);ax.set_aspect('equal')
                    ax.set_title(f'p={noise:g}, layer{layer}\ndensity={len(edges)/(n*(n-1)/2):.3f}; C={clustering:.3f}',fontsize=9)
            if any_example:
                fig.suptitle(f'{prefix} {condition}: d=e=1.2, t100, predetermined repetition0; circular layout')
                save(fig,f'{prefix}_Figure5_{condition}.png')
            else:plt.close(fig)

    for interpretation in sorted({r['interpretation'] for r in endpoints}):
        fig,axs=plt.subplots(3,6,figsize=(18,8))
        for i,(n,sampling) in enumerate(((40,'random'),(40,'smart'),(100,'random'))):
            counts=(13,26,40) if n==40 else (33,66,100)
            for direction,condition in enumerate(('LH','HL')):
                panels=[[r for r in effects if r['interpretation']==interpretation and r['n']==n and r['sampling']==sampling and r['condition']==condition and r['shock_count']==count and r['p']==0 and r['metric']=='utility'] for count in counts]
                limits=shared_limits(panels)
                for j,(count,rows) in enumerate(zip(counts,panels)):
                    heat(axs[i,direction*3+j],rows,f'N{n} {sampling} {condition} shocked{count}',limits=limits)
        fig.suptitle(f'{interpretation}: S1 utility; shared scale across shock counts within method/direction\nPublished caption shock count is inconsistent')
        save(fig,f'{interpretation}_S1.png')
        if heatmaps_only:continue
        for target,method_list in [('Figure6',[(40,'random')]),('S2',[(40,'random'),(40,'smart'),(100,'random')])]:
            fig,axs=plt.subplots(4,2,figsize=(12,14))
            for i,metric in enumerate(('degree','clustering','spillover','utility_cdf')):
                for j,condition in enumerate(('LH','HL')):
                    ax=axs[i,j]
                    for mi,(n,sampling) in enumerate(method_list):
                        fit=next((r for r in regressions if r['interpretation']==interpretation and r['n']==n and r['sampling']==sampling and r['condition']==condition and r['metric']==metric and r['exposure']=='paper_layer_weighted'),None)
                        if fit and fit['coefficients'] is not None:
                            b=np.asarray(fit['coefficients']);se=np.asarray(fit['standard_errors']) if fit['standard_errors'] is not None else np.zeros(len(b))
                            critical=float(student_t.ppf(.975,fit['histories']-1)) if fit['histories']>1 else 0
                            ax.errorbar(b,np.arange(len(b))+(mi-1)*.15,xerr=se*critical,fmt='o',markersize=3,label=f'N{n} {sampling}; G={fit["histories"]}')
                    ax.axvline(0,color='gray',linewidth=.8);ax.set_yticks(range(len(PREDICTORS)),PREDICTORS,fontsize=7)
                    ax.set_title(f'{condition} {metric}')
                    if ax.lines and len(ax.lines)>1:ax.legend(fontsize=7)
            fig.suptitle(f'{interpretation}: reconstructed OLS, history-clustered95% intervals; Eq8 exposure')
            save(fig,f'{interpretation}_{target}_reconstructed_OLS.png')
    return artifacts


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    result=generate_report(args.index,args.output)
    print(json.dumps({'completed_cases':result['completed_cases'],'declared_cases':result['declared_cases'],'artifacts':result['artifacts']}))
