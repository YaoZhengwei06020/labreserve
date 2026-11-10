"""Validate process records without treating templates as completed work."""
import argparse
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPRINT_1 = {"US-01", "US-02", "US-04", "US-05", "US-08", "US-09"}
STORY_IDS = {f"US-{i:02}" for i in range(1, 14)}
STATES = {"draft", "ready-for-dev", "in-progress", "review", "done"}


def validate_status(data, root=ROOT):
    errors = []
    members = data.get("team", {}).get("members", [])
    if len(members) != 4 or len(set(members)) != 4:
        errors.append("Team roster must contain four distinct members")
    stories = data.get("stories", {})
    if set(stories) != STORY_IDS:
        errors.append("Story IDs must exactly match US-01 through US-13")
    totals = {"sprint-1": 0, "sprint-2": 0}
    for story_id, story in stories.items():
        if story.get("owner") not in members or story.get("reviewer") not in members:
            errors.append(f"{story_id}: owner/reviewer missing from team")
        if story.get("owner") == story.get("reviewer"):
            errors.append(f"{story_id}: independent reviewer required")
        if story.get("status") not in STATES:
            errors.append(f"{story_id}: invalid status")
        sprint = "sprint-1" if story_id in SPRINT_1 else "sprint-2"
        if story.get("sprint") != sprint:
            errors.append(f"{story_id}: sprint differs from the candidate baseline")
        points = story.get("points")
        if not isinstance(points, int) or points <= 0:
            errors.append(f"{story_id}: invalid estimate")
        else:
            totals[sprint] += points
        card = root / story.get("card", "missing")
        if not card.is_file() or f"# {story_id} " not in card.read_text(encoding="utf-8"):
            errors.append(f"{story_id}: missing/mismatched Story card")
        if not story.get("requirements") or any(not re.fullmatch(r"FR-(0[1-9]|1[0-5])", fr) for fr in story.get("requirements", [])):
            errors.append(f"{story_id}: invalid requirement mapping")
        evidence = story.get("acceptance_evidence", [])
        for item in evidence:
            if not item.startswith("https://") and not (root / item).is_file():
                errors.append(f"{story_id}: evidence path does not exist")
        if story.get("status") == "done":
            review = story.get("review", {})
            if not evidence:
                errors.append(f"{story_id}: done requires acceptance evidence")
            if review.get("status") != "accepted" or review.get("approved_by") != story.get("reviewer"):
                errors.append(f"{story_id}: done requires the assigned reviewer's acceptance")
    if totals != {"sprint-1": 25, "sprint-2": 23}:
        errors.append("Candidate estimates must remain 25 + 23 = 48 SP until explicitly revised")
    for item in ["decision-log.md", "retrospective.md", "docs/team.md", "docs/reviews/baseline-review.md"]:
        if not (root / item).is_file():
            errors.append("Missing process artifact: " + item)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true", help="Also require final submission readiness")
    args = parser.parse_args()
    data = yaml.safe_load((ROOT / "sprint-status.yaml").read_text(encoding="utf-8"))
    errors = validate_status(data)
    log = (ROOT / "decision-log.md").read_text(encoding="utf-8")
    decisions = re.findall(r"^## D-\d+\b.*?(?=^## |\Z)", log, re.M | re.S)
    changed = [text for text in decisions if re.search(r"^人工判断[：:]\s*(修改|否决)", text, re.M)]
    gaps = []
    if len(decisions) < 15:
        gaps.append(f"Formal decision records: {len(decisions)}/15")
    if len(changed) < 5:
        gaps.append(f"Rejected/substantively modified records: {len(changed)}/5")
    if any(story["status"] != "done" for story in data["stories"].values()):
        gaps.append("Story acceptance remains incomplete")
    if data["target_users"]["contact_status"] != "confirmed":
        gaps.append("Actual user/laboratory confirmation remains pending")
    if data["experiment_a"]["status"] != "completed":
        gaps.append("Experiment A remains incomplete")
    if args.final:
        errors.extend(gaps)
    if errors:
        raise SystemExit("\n".join(errors))
    print("PASS: process structure, 13 Story cards, owners/reviewers, states and evidence guards")
    for gap in gaps:
        print("PENDING:", gap)


if __name__ == "__main__":
    main()
