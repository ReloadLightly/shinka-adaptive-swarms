import argparse
import json
import time

import pytest

from adaptive_swarms import cli
from adaptive_swarms.logging import EventLogger


def test_resume_rejects_changed_simulator_and_preserves_origin(tmp_path, monkeypatch):
    config = tmp_path / "suite.json"
    config.write_text(json.dumps({"budget": 31, "period": 10, "cases": [{}]}))
    folder = tmp_path / "run"
    args = argparse.Namespace(config=str(config), budget=None, run=str(folder), resume=False, policy=None)
    monkeypatch.setattr(cli, "source_revision", lambda: "first-revision")
    cli.baseline(args)
    args.resume = True
    monkeypatch.setattr(cli, "source_revision", lambda: "documentation-only-change")
    cli.baseline(args)
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["source_revision"] == "first-revision"
    assert manifest["continuations"][0]["source_revision"] == "documentation-only-change"
    monkeypatch.setattr(cli, "simulator_fingerprint", lambda: {"simulator.py": "changed"})
    with pytest.raises(SystemExit, match="differs"):
        cli.baseline(args)


def test_heartbeat_and_failure_are_persisted(tmp_path, capsys):
    with pytest.raises(RuntimeError, match="observed failure"):
        with EventLogger(tmp_path, heartbeat_seconds=.01) as log:
            log.set_activity("waiting for proposal")
            log.event("proposal_start", generation=1)
            time.sleep(.04)
            raise RuntimeError("observed failure")
    records = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert records[0]["event"] == "proposal_start"
    assert any(r["event"] == "heartbeat" and r["activity"] == "waiting for proposal" for r in records)
    assert records[-1]["event"] == "failed"
    assert "observed failure" in (tmp_path / "run.log").read_text()
    assert "heartbeat" in capsys.readouterr().out
