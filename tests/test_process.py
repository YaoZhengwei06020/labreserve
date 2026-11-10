from copy import deepcopy
from pathlib import Path

import yaml

from scripts.check_project_process import validate_status

ROOT = Path(__file__).resolve().parents[1]


def baseline():
    return deepcopy(yaml.safe_load((ROOT / "sprint-status.yaml").read_text(encoding="utf-8")))


def test_done_requires_evidence_and_review():
    data = baseline()
    data["stories"]["US-01"]["status"] = "done"
    errors = validate_status(data)
    assert "US-01: done requires acceptance evidence" in errors
    assert "US-01: done requires the assigned reviewer's acceptance" in errors


def test_technical_spike_does_not_complete_story():
    data = baseline()
    data["stories"]["US-09"]["status"] = "done"
    assert "US-09: done requires acceptance evidence" in validate_status(data)


def test_unknown_owner_and_self_review_rejected():
    data = baseline()
    data["stories"]["US-01"]["owner"] = "UNKNOWN"
    data["stories"]["US-02"]["reviewer"] = data["stories"]["US-02"]["owner"]
    errors = validate_status(data)
    assert "US-01: owner/reviewer missing from team" in errors
    assert "US-02: independent reviewer required" in errors


def test_all_stories_must_be_tracked():
    data = baseline()
    del data["stories"]["US-13"]
    assert "Story IDs must exactly match US-01 through US-13" in validate_status(data)
