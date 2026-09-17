"""Conservative research accounting shared by the single campaign controller/evaluator."""
from pathlib import Path
from .artifacts import read_json
from .execution import InfrastructureError

MAX_ATTEMPTS = 400
MAX_QUERIES = 200_000_000


def research_accounting(folder):
    folder = Path(folder)
    controls = []
    for stage in ('references', 'fresh'):
        ledger = folder / stage / 'execution_ledger.json'
        if ledger.exists():
            controls.extend({**item, 'stage': stage} for item in read_json(ledger).get('attempts', []))
    records = []
    for item in controls:
        if item['status'] != 'reused':
            records.append({'source': 'control', **item,
                            'conservative_queries': item.get('reserved_queries', 500000)})
    for path in sorted((folder / 'evolution').glob('search_seed_*/gen_*/results/execution-attempts.json')):
        for item in read_json(path):
            records.append({'source': str(path.relative_to(folder)), **item,
                            'conservative_queries': item.get('reserved_objective_queries', 500000)})
    return {'full_case_attempts': len(records),
            'completed_full_cases': sum(r['status'] == 'completed' for r in records),
            'conservative_research_queries': sum(r['conservative_queries'] for r in records),
            'known_completed_queries': sum(r.get('actual_queries', r.get('exact_objective_queries', 0)) or 0 for r in records if r['status'] == 'completed'),
            'attempts': records}


def enforce_research_allowance(folder, additional_cases=1):
    state = research_accounting(folder)
    if state['full_case_attempts'] + additional_cases > MAX_ATTEMPTS or state['conservative_research_queries'] + additional_cases*500000 > MAX_QUERIES:
        raise InfrastructureError('Immutable campaign research allowance exhausted; preserve completed/partial work')
    return state
