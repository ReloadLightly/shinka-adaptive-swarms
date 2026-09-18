"""Read-only explanations of native proposals and measured outcomes.

No new model calls, candidate feedback, RNG draws or objective evaluations.
The native author's explanation is a hypothesis, never a measured conclusion.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path


def log_test_contract(log, suite_path, task):
    suite = json.loads(Path(suite_path).read_text())
    cases = suite.get("cases", [])
    log.event(
        "scientific_test", task=task,
        message="Test whether this population rule lowers mean offline error on the same development histories at equal counted objective budgets.",
        case_count=len(cases), budgets=[c["budget"] for c in cases],
        dimensions=sorted({c["dimension"] for c in cases}),
        peaks=sorted({c["npeaks"] for c in cases}),
        feedback_comparators=list(suite.get("feedback_references", {})),
        intervention="choose_neutral_count: target 2..8; at most one resize after detected change and counted memory refresh",
        fixed="corrected enclosing-ball engine, permanent quantum particle, movement, exclusion, birth/removal, separate environment RNG",
        accounting="Detection and memory refresh consume objective queries; completed cases are checkpointed.",
        interpretation="Development selection only. No fresh histories or causal emergence test in this session.",
    )


def log_proposal(log, job, parent):
    source = Path(job.exec_fname).read_text()
    previous = parent.code if parent is not None else ""
    meta = job.meta_patch_data or {}
    try:
        tree = ast.parse(source)
        fields = sorted({n.slice.value for n in ast.walk(tree)
                         if isinstance(n, ast.Subscript)
                         and isinstance(n.value, ast.Name) and n.value.id == "observation"
                         and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)})
    except SyntaxError:
        fields = []  # The evaluator owns acceptance; logging never validates fitness.
    delta = "\n".join(difflib.unified_diff(previous.splitlines(), source.splitlines(),
                                         fromfile="parent", tofile=f"generation_{job.generation}", lineterm=""))
    log.event("program_under_test", generation=job.generation,
              parent_id=job.parent_id, parent_generation=getattr(parent, "generation", None),
              archive_inspiration_ids=job.archive_insp_ids, top_inspiration_ids=job.top_k_insp_ids,
              mutation_type=meta.get("patch_type"), name=meta.get("patch_name"),
              author_hypothesis=meta.get("patch_description"),
              hypothesis_status="Native proposal description; benefits remain unverified until measured.",
              observation_fields_referenced=fields, source=str(job.exec_fname),
              source_sha256=hashlib.sha256(source.encode()).hexdigest(),
              exact_parent_diff=delta)
    # Every terminal line carries generation and timestamp, including source/diff lines.
    for line in delta.splitlines():
        log.event("program_change", generation=job.generation, diff=line)


def log_outcome(log, program, parent):
    metrics = program.public_metrics or {}
    mean = metrics.get("mean_offline_error") if program.correct else None
    parent_mean = (parent.public_metrics or {}).get("mean_offline_error") if parent is not None and parent.correct else None
    log.event("program_measured", generation=program.generation, program_id=program.id,
              valid=bool(program.correct), cases_completed=metrics.get("cases_completed"),
              mean_offline_error=mean, parent_generation=getattr(parent, "generation", None),
              difference_from_parent=(mean-parent_mean if mean is not None and parent_mean is not None else None),
              public_metrics=metrics,
              interpretation="Negative error difference favors the child on development histories; this is not fresh confirmation or a causal component test.")
