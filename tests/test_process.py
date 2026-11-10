from copy import deepcopy
from pathlib import Path

import yaml

from scripts.check_project_process import decision_counts, validate_status

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


def test_decision_headings_and_templates_do_not_count():
    text = "\n".join(f"## D-{i:03} Empty\n人工判断：否决\n" for i in range(1, 16))
    assert decision_counts(text) == (0, 0)
    assert decision_counts("```text\n## D-001 Example\n人工判断：否决\n```") == (0, 0)


def test_decision_without_verification_is_not_complete():
    text = """## D-001 Synthetic test fixture
发生日期：2030-01-01
参与者：test reviewer
触发与上下文：test workflow
AI建议及备选：test suggestion
人工判断：修改
依据：FR-09
改动产物与提交：test commit
事后验证：待填写
相关证据：test evidence
"""
    assert decision_counts(text) == (0, 0)
    blank_date = text.replace("事后验证：待填写", "事后验证：test verification").replace("发生日期：2030-01-01", "发生日期：")
    assert decision_counts(blank_date) == (0, 0)
