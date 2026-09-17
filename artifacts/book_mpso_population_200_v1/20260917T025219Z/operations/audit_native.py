#!/usr/bin/env python3
"""Read-only chapter-population-200 snapshot using the existing native machinery auditor."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--label', required=True, help='Unique immutable snapshot label, e.g. first or final')
args = parser.parse_args()
repo = Path.cwd().resolve()
sys.path[:0] = [str(repo / 'scripts'), str(repo / 'src')]
from audit_joint_machinery import Evidence, audit_search, write_exclusive
from adaptive_swarms.engine_progress import terminal_failure_generations
run = args.run.resolve()
sprint = run.parent.parent
out = sprint / 'operations' / ('native-inspection-' + args.label + '.json')
evidence = Evidence(sprint)
audit, raw, _ = audit_search(run, evidence)
if audit['status'] == 'not_started':
    receipts = list((run / 'engine_calls').glob('*.json'))
    programs = list(run.glob('gen_*/main.py'))
    database = run / 'programs.sqlite'
    if receipts or programs or database.exists():
        raise RuntimeError('Native manifest absent but execution artifacts exist; inspect incomplete launch.')
    record = {
        'created_at': datetime.now(timezone.utc).isoformat(), 'label': args.label,
        'status': 'native_not_launched', 'run': str(run.relative_to(sprint)),
        'reason': 'Runtime-constrained stop before mutation; planned native machinery is not represented as executed.',
        'terminal_slots': 0, 'valid_descendants': 0, 'native_seed_evaluations': 0,
        'native_wrappers': 0, 'native_logical_responses': 0,
        'model_role_counts': {'mutation': 0, 'novelty': 0, 'meta': 0},
        'local_embedding_requests_for_this_search': 0,
        'native_prompt_source_checks': 0, 'native_meta_recommendation_insertions': 0,
        'actual_inner_model_and_effort': 'No internal calls; gpt-6-astra/xhigh was prepared, not invoked.',
        'native_database_exists': False, 'native_webui_launched': False,
        'scope': 'Filesystem evidence confirms no run manifest, native database, generated programs or call receipts. Existing independent viewers/services remain outside this run.',
        'audit_model_calls': 0, 'audit_objective_queries': 0,
        'audit_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    write_exclusive(out, record)
    print(json.dumps({'saved': str(out), 'status': record['status'],
                      'terminal_slots': 0, 'logical_responses': 0}), flush=True)
    sys.exit(0)
audit['retry_context_association'] = 'Most recent native_sampling event before wrapper start; this sprint uses one proposal worker. Full saved prompt source/feedback checks verify context separately.'
by_call = {receipt['call_id']: receipt for _, receipt in raw}
for receipt in audit['role_receipts']:
    original = by_call[receipt['call_id']]
    for key in ('initial_logical_responses', 'exposed_native_retry_responses', 'native_dispatch_attempts', 'reservation_scope', 'logical_response_limit', 'run_reserved_logical_responses_at_reservation'):
        receipt[key] = original.get(key)
for role, totals in audit['role_totals'].items():
    receipts = [value for _, value in raw if value['role'] == role]
    totals['initial_logical_responses'] = sum(value.get('initial_logical_responses', value['requested_logical_responses']) for value in receipts)
    totals['exposed_native_retry_responses'] = sum(value.get('exposed_native_retry_responses', 0) for value in receipts)
    totals['observed_native_dispatch_attempts'] = sum(len(value.get('native_dispatch_attempts', [])) for value in receipts)
    totals['native_dispatch_status_counts'] = dict(Counter(attempt['status'] for value in receipts for attempt in value.get('native_dispatch_attempts', [])))
    totals['closed_response_shortfall'] = sum(max(0, value.get('initial_logical_responses', value['requested_logical_responses']) - (value.get('valid_responses') or 0)) for value in receipts if value['status'] != 'started')
checks = [check for sample in audit['native_sampling'] for check in sample['saved_attempt_prompt_checks']]
source_checks = [check for prompt in checks for check in prompt['sources']]
audit['prompt_verification_summary'] = {
    'saved_attempt_prompts': len(checks),
    'full_frozen_task_context_present': sum(bool(check['frozen_task_context_present']) for check in checks),
    'source_context_references': len(source_checks),
    'full_sources_present': sum(bool(check.get('full_source_present')) for check in source_checks),
    'full_feedback_present': sum(bool(check.get('full_feedback_present')) for check in source_checks),
    'sampling_events_without_saved_prompt_yet': sum(not sample['saved_attempt_prompt_checks'] for sample in audit['native_sampling']),
}
task = evidence.bytes(run / 'task_snapshot/task_system_prompt.txt').decode()
suite = evidence.json(sprint / 'search_suite.json')
audit['current_condition_consistency'] = {
    'case_count': len(suite['cases']),
    'all_cases_200_peaks_500000_queries': all(c['npeaks'] == 200 and c['budget'] == 500000 for c in suite['cases']),
    'control_roles': sorted(suite['feedback_references']),
    'explicit_four_new_development_cases_in_prompt': 'FOUR newly registered DEVELOPMENT cases' in task,
    'explicit_200_conical_peaks_in_prompt': '200 conical peaks' in task,
    'explicit_two_current_controls_in_prompt': 'References are fixed targets 3 and 5' in task,
    'global_workload_and_history_available_in_prompt': all(k in task for k in ('swarm_count', 'total_particle_count', 'previous_requested_target')),
    'ten_peak_context_labeled_historical': 'historical ten-peak development' in task,
}
observed_path = sprint / 'operations/native-codex-process-settings-observed.json'
if observed_path.exists():
    observed = evidence.json(observed_path)
    audit['visible_cli_evidence'] = {
        'source': evidence.label(observed_path),
        'process_observation_count_not_response_count': len(observed['observations']),
        'model_effort_arguments': [list(pair) for pair in sorted({tuple(setting)
            for row in observed['observations'] for setting in row['visible_model_and_effort_arguments']})],
        'roles_matched_by_exact_prompt_messages': sorted({match['role'] for row in observed['observations']
            for prompt in row.get('headless_prompt_evidence', [])
            for match in prompt['exact_system_and_user_message_matches']}),
        'scope': 'Visible CLI arguments tied to this run by ancestry and prompt identity; no provider-independent or supervisory effort attestation.',
    }
else:
    audit['visible_cli_evidence'] = {'status': 'not_yet_observed'}
generations = []
for folder in sorted(run.glob('gen_*'), key=lambda p: int(p.name[4:])):
    metrics_path = folder / 'results/metrics.json'
    checkpoint_path = folder / 'results/evaluation-checkpoint.json'
    if not checkpoint_path.exists():
        continue
    checkpoint = evidence.json(checkpoint_path)
    events = evidence.lines(folder / 'results/events.jsonl')
    row = {'generation': int(folder.name[4:]), 'checkpoint_status': checkpoint['status'],
           'completed_cases': len(checkpoint['completed_cases']),
           'completed_new_cases': sum(e.get('event') == 'case_complete' for e in events),
           'new_completed_objective_queries': sum(e.get('new_objective_queries', 0) for e in events if e.get('event') == 'case_complete'),
           'reuse_events': sum(e.get('event') in {'case_reused', 'case_reused_exact_source'} for e in events),
           'source_sha256': hashlib.sha256(evidence.bytes(folder / 'main.py')).hexdigest()}
    if metrics_path.exists():
        metrics = evidence.json(metrics_path)
        cases = metrics['private'].get('cases', [])
        row.update(mean_offline_error=metrics['public'].get('mean_offline_error'),
                   regime_summaries=metrics['private'].get('regime_paired_summaries'),
                   subswarm_updates=sum(c.get('population_stats', {}).get('total_neutral_updates', 0) for c in cases),
                   population_policy_calls=sum(c.get('population_stats', {}).get('policy_calls', 0) for c in cases),
                   particle_additions=sum(c.get('population_stats', {}).get('additions', 0) for c in cases),
                   particle_removals=sum(c.get('population_stats', {}).get('removals', 0) for c in cases),
                   feedback_sha256=hashlib.sha256(metrics.get('text_feedback', '').encode()).hexdigest())
    generations.append(row)
ids = set(audit['original_evaluated_generation_ids'])
failed_without_archive = sorted(terminal_failure_generations(run) - ids)
invalid_archived = sorted({r['generation'] for r in audit['database_rows'] if not r['correct'] and r['generation'] in ids})
failed = sorted(set(failed_without_archive + invalid_archived))
audit.update(terminal_failed_slots=failed, terminal_rejected_without_archive=failed_without_archive,
             archived_invalid_generations=invalid_archived, terminal_slots=len(ids) + len(failed_without_archive),
             evaluated_descendants=sum(g > 0 for g in ids),
             valid_descendants=len({r['generation'] for r in audit['database_rows'] if r['correct'] and r['generation'] in ids and r['generation'] > 0}),
             generation_progress=generations,
             evaluated_descendants_semantics='All archived descendant outcomes including evaluator-rejected invalid source; valid_descendants counts only correct archived descendants.')
record = {'created_at': datetime.now(timezone.utc).isoformat(), 'label': args.label,
          'scope': 'Read-only native machinery snapshot; zero model or numerical executions. Live files can advance between reads; hashes describe each captured read.',
          'status': 'completed' if audit['status'] == 'search_complete' else 'snapshot',
          'audit_model_calls': 0, 'audit_objective_queries': 0,
          'run': str(run.relative_to(sprint)), 'native': audit,
          'input_evidence': evidence.files, 'limitations': evidence.limitations,
          'scripts': {'scripts/audit_joint_machinery.py': hashlib.sha256((repo / 'scripts/audit_joint_machinery.py').read_bytes()).hexdigest(),
                      'operations/audit_native.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
write_exclusive(out, record)
print(json.dumps({'saved': str(out), 'status': record['status'], 'terminal_slots': audit['terminal_slots'], 'evaluated_descendants': audit['evaluated_descendants'], 'valid_descendants': audit['valid_descendants'], 'role_totals': audit['role_totals'], 'prompt_verification_summary': audit['prompt_verification_summary'], 'meta_updates': len(audit['meta']['updates_completed']), 'meta_injections': sum(bool(i['matched_recommendations']) for i in audit['meta']['mutation_prompt_injections']), 'migrations': len(audit['migration_history']), 'degradation_events': len(audit['degradation_events']), 'novelty': {k: audit['novelty'][k] for k in ('accepted','rejected','fallback')}}))
