"""Validate source-derived counts, estimates, coverage and local links."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
docs = root / "docs"
errors = []


def expect(condition, message):
    if not condition:
        errors.append(message)


prd = (docs / "prd.md").read_text(encoding="utf-8")
stories = (docs / "epics-and-stories.md").read_text(encoding="utf-8")
context = (docs / "project-context.md").read_text(encoding="utf-8")
matrix = (docs / "traceability.md").read_text(encoding="utf-8")
expect(re.findall(r"^### FR-(\d\d) ", prd, re.M) == [f"{i:02}" for i in range(1,16)], "15 FR headings")
expect(re.findall(r"^### NFR-(\d\d) ", prd, re.M) == [f"{i:02}" for i in range(1,7)], "6 NFR headings")
expect(re.findall(r"^# Epic E-(\d\d)", stories, re.M) == [f"{i:02}" for i in range(1,5)], "4 Epics")
expect(re.findall(r"^## US-(\d\d) ", stories, re.M) == [f"{i:02}" for i in range(1,14)], "13 Stories")
expect(re.findall(r"\*\*RULE-(\d\d)", context) == [f"{i:02}" for i in range(1,13)], "12 RULEs")
points = {int(n):int(sp) for n,sp in re.findall(r"^## US-(\d\d) .*?，(\d+) SP", stories, re.M)}
sprint1 = [1,2,4,5,8,9]
expect(sum(points.values()) == 48, "48 AI-estimated SP")
expect(sum(points.get(i,0) for i in sprint1) == 25, "Sprint 1 25 SP")
expect(sum(v for k,v in points.items() if k not in sprint1) == 23, "Sprint 2 23 SP")
adrs = sorted((docs / "adr").glob("[0-9]*.md"))
expect(len(adrs) == 7, "7 ADRs")
for i, path in enumerate(adrs,1):
    text = path.read_text(encoding="utf-8")
    expect(f"# ADR-{i:03}" in text and "Status: PROPOSED" in text, f"proposed ADR-{i:03}")
for i in range(1,16):
    expect(bool(re.search(rf"^\| FR-{i:02} \| US-", matrix, re.M)), f"FR-{i:02} Story coverage")
for i in range(1,14):
    expect(f"US-{i:02}" in matrix, f"US-{i:02} traceability")
for path in root.rglob("*.md"):
    if any(p in {".git", ".venv", ".agents", "_bmad", "node_modules"} for p in path.parts):
        continue
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        if "://" in target or target.startswith("#"):
            continue
        expect((path.parent / target.split("#")[0]).exists(), f"broken link {path.relative_to(root)}: {target}")
if errors:
    raise SystemExit("\n".join(errors))
print("PASS: 4 Epic / 13 Story / 15 FR / 6 NFR / 7 PROPOSED ADR / 12 RULE; 25+23=48 SP; coverage; Markdown links")
