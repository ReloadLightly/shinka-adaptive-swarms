#!/usr/bin/env python3
"""Inspect the native, subscription-backed mutation route without model calls."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

PINNED_SHINKA = "9912af12d423504b8d580f4179fd15f5f88b8c50"
HEADLESS_COMMAND = "npx -y @roberttlange/headless@0.6.1"


def inspect_runtime(model="gpt-6-astra", effort=None, seed_only=False) -> dict:
    report = {
        "model_requested": model,
        "inner_effort_requested": effort,
        "inner_effort_effective": None,
        "inner_effort_status": "not sent; Codex profile/default applies" if effort is None else "requested; no model invocation performed",
        "outer_work_mode": "not inspected; Astra Ultra selection belongs to the outer Codex interface, separately from this launcher",
        "seed_only": seed_only,
        "paid_api_calls_authorized": False,
        "model_calls_performed_by_check": 0,
        "errors": [],
    }
    try:
        report["shinka_version"] = importlib.metadata.version("shinka-evolve")
        report["shinka_available"] = importlib.util.find_spec("shinka") is not None
    except (ImportError, importlib.metadata.PackageNotFoundError):
        report["shinka_available"] = False
        report["errors"].append("ShinkaEvolve is not installed. Run: python -m pip install -e '.[evolution]'")
    report["headless_command"] = os.environ.get("SHINKA_HEADLESS_COMMAND", HEADLESS_COMMAND)
    if seed_only:
        report["model_route"] = "disabled: native generation 0 only"
        report["ready"] = not report["errors"]
        return report
    codex = shutil.which("codex")
    report["codex_available"] = bool(codex)
    report["npx_available"] = bool(shutil.which("npx"))
    if not codex:
        report["errors"].append("Codex CLI is absent here. Launch on the machine where Codex is installed and signed in with ChatGPT.")
    else:
        try:
            version = subprocess.run([codex, "--version"], capture_output=True, text=True, timeout=15)
            report["codex_version"] = version.stdout.strip()[:200]
            auth = subprocess.run([codex, "login", "status"], capture_output=True, text=True, timeout=15)
            status = (auth.stdout + auth.stderr).lower()
            report["subscription_login_confirmed"] = auth.returncode == 0 and "chatgpt" in status
            if not report["subscription_login_confirmed"]:
                report["errors"].append("A ChatGPT subscription login was not confirmed by `codex login status`. Sign in with ChatGPT; API-key authentication is not authorized for this run.")
        except (OSError, subprocess.TimeoutExpired) as exc:
            report["errors"].append(f"Codex status check failed: {type(exc).__name__}.")
    if not report["npx_available"] and report["headless_command"].startswith("npx "):
        report["errors"].append("Node.js/npx is needed for the official Headless CLI route.")
    if effort is not None and effort not in {"low", "medium", "high", "xhigh"}:
        report["errors"].append(
            f"The pinned native Shinka Headless provider does not accept inner effort {effort!r}. "
            "Ultra in the current Codex documentation describes outer orchestration. Select Ultra "
            "in the Codex interface, and use an explicitly supported inner effort or omit --effort. "
            "No lower effort has been substituted."
        )
    report["model_route"] = f"headless/codex@{model}" + (f"?effort={effort}" if effort else "")
    report["ready"] = not report["errors"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-6-astra")
    parser.add_argument("--effort", default=None)
    parser.add_argument("--seed-only", action="store_true")
    args = parser.parse_args()
    report = inspect_runtime(args.model, args.effort, args.seed_only)
    print(json.dumps(report, indent=2), flush=True)
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
