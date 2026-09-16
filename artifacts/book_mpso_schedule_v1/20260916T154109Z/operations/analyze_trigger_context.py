#!/usr/bin/env python3
"""Post hoc public-observation context for generation6; reads saved cases only.

Usage: python operations/analyze_trigger_context.py --run RUN --output OUTPUT.json
No objective or model calls. It does not execute candidate programs.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import statistics

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
cases, inputs = [], {}
for index in range(8):
    path = args.run / f'evolution/search_seed_640001/gen_6/results/case_{index:03d}.json.gz'
    case = json.load(gzip.open(path, 'rt'))
    inputs[str(path.relative_to(args.run))] = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = [row for row in case['response_log'] if row['observation']['change_detected']]
    groups = {str(k): [row for row in rows if row['decision']['temporary_quantum_count'] == k] for k in (4, 5)}
    cases.append({'case_index': index, 'detected_decisions': len(rows), 'count4_fraction': len(groups['4']) / len(rows), 'groups': {
        k: {'n': len(values), 'negative_previous_quality_fraction': statistics.mean(row['observation']['previous_best_fitness'] < 0 for row in values) if values else None,
            'median_neutral_diameter_in_radii': statistics.median(row['observation']['neutral_diameter'] / row['observation']['default_radius'] for row in values) if values else None,
            'median_speed_in_radii': statistics.median(row['observation']['mean_neutral_speed'] / row['observation']['default_radius'] for row in values) if values else None}
        for k, values in groups.items()}})
result = {'generation': 6, 'source_proof': 'Count4 iff detected and absolute relative observed fitness change<=0.01; count5 otherwise at detection; zero between. All environmental severities fixed1.',
    'analysis_scope': 'Post hoc descriptive behavior using already saved public observations, not a causal mediator or additional experiment.',
    'cases': cases, 'equal_case_count4_fraction_at_detection': statistics.mean(case['count4_fraction'] for case in cases),
    'equal_case_negative_previous_quality_by_count': {str(k): statistics.mean(case['groups'][str(k)]['negative_previous_quality_fraction'] for case in cases if case['groups'][str(k)]['n']) for k in (4, 5)},
    'input_sha256': inputs, 'analysis_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'objective_queries': 0, 'model_calls': 0}
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key not in ('cases', 'input_sha256')}, indent=2))
