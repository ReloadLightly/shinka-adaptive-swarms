#!/usr/bin/env python3
"""Read-only particle-retention snapshot using the existing native machinery auditor."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', type=Path, required=True)
parser.add_argument('--label', choices=('4', '8', 'final'), required=True)
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
                   retention_decisions=sum(c.get('retention_decisions', 0) for c in cases),
                   heuristic_agreements=sum(c.get('heuristic_agreements', 0) for c in cases),
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
             evaluated_descendants_semantics='All archived descendant outcomes including evaluator-rejected invalid source; valid_descendants counts only correct archived descendants.',
             interim_legacy_field_note='Earlier native-inspection-4.json used radius-velocity-only response_count/reset_velocity_count defaults of zero. They are unavailable fields, not measured zero particle-retention decisions. Final audit reports actual retention_decisions and heuristic_agreements.')
record = {'created_at': datetime.now(timezone.utc).isoformat(), 'label': args.label,
          'scope': 'Read-only native machinery snapshot; zero model or numerical executions. Live files can advance between reads; hashes describe each captured read.',
          'status': 'completed' if audit['status'] == 'search_complete' else 'snapshot',
          'run': str(run.relative_to(sprint)), 'native': audit,
          'input_evidence': evidence.files, 'limitations': evidence.limitations,
          'scripts': {'scripts/audit_joint_machinery.py': hashlib.sha256((repo / 'scripts/audit_joint_machinery.py').read_bytes()).hexdigest(),
                      'operations/audit_native_retention.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
write_exclusive(out, record)
print(json.dumps({'saved': str(out), 'status': record['status'], 'terminal_slots': audit['terminal_slots'], 'evaluated_descendants': audit['evaluated_descendants'], 'valid_descendants': audit['valid_descendants'], 'role_totals': audit['role_totals'], 'prompt_verification_summary': audit['prompt_verification_summary'], 'meta_updates': len(audit['meta']['updates_completed']), 'meta_injections': sum(bool(i['matched_recommendations']) for i in audit['meta']['mutation_prompt_injections']), 'migrations': len(audit['migration_history']), 'degradation_events': len(audit['degradation_events']), 'novelty': {k: audit['novelty'][k] for k in ('accepted','rejected','fallback')}}))
