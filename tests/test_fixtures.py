"""Fixture projects must be well-formed, so a future eval runner can trust them.

tests/fixtures/<case>/
  project/        a copy-ready scratch project (.claude/agents/*.md, CLAUDE.md, ...)
  expected.json   what a correct run must produce (graded on files, not wording)
"""

import json
from pathlib import Path

import pytest

from helpers import ROOT, frontmatter, rel

FIXTURES = ROOT / "tests" / "fixtures"
CASES = sorted(p for p in FIXTURES.iterdir() if p.is_dir())

COMMANDS = {"prune", "setup"}
KINDS = {
    "prune",
    "rehome",
    "new-agent",
    "scoped-pointer",
    "classification-question",
    "split-offer",
}
# Roles proposed for creation / bootstrap don't exist in project/ yet.
ROLE_NOT_ON_DISK = {"new-agent", "split-offer"}
FILE_LISTS = ("files_created", "files_changed", "files_unchanged")


def test_fixtures_exist():
    assert len(CASES) >= 7, f"expected the seeded cases under {rel(FIXTURES)}"


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_fixture_well_formed(case):
    spec_path = case / "expected.json"
    assert spec_path.is_file(), f"{case.name}: expected.json missing"
    assert (case / "project").is_dir(), f"{case.name}: project/ missing"
    spec = json.loads(spec_path.read_text())

    assert str(spec.get("description", "")).strip(), f"{case.name}: description missing"
    assert spec.get("command") in COMMANDS, f"{case.name}: command must be one of {sorted(COMMANDS)}"
    answers = spec.get("answers")
    assert isinstance(answers, list) and all(isinstance(a, str) for a in answers), (
        f"{case.name}: answers must be a list of strings"
    )

    expect = spec.get("expect")
    assert isinstance(expect, dict), f"{case.name}: expect missing"
    assert isinstance(expect.get("proposals"), list), f"{case.name}: expect.proposals must be a list"

    agents_dir = case / "project" / ".claude" / "agents"
    on_disk = {p.stem for p in agents_dir.glob("*.md")} if agents_dir.is_dir() else set()
    for agent in agents_dir.glob("*.md") if agents_dir.is_dir() else []:
        assert frontmatter(agent).get("name") == agent.stem, f"{rel(agent)}: name != file stem"

    for proposal in expect["proposals"]:
        kinds = proposal.get("kinds")
        assert isinstance(kinds, list) and kinds and set(kinds) <= KINDS, (
            f"{case.name}: proposal kinds must be a non-empty subset of {sorted(KINDS)}: {proposal}"
        )
        assert isinstance(proposal.get("role"), str) and proposal["role"], (
            f"{case.name}: proposal needs a role: {proposal}"
        )
        if not set(kinds) <= ROLE_NOT_ON_DISK:
            assert proposal["role"] in on_disk, (
                f"{case.name}: role {proposal['role']!r} has no project/.claude/agents/ file"
            )

    for key in FILE_LISTS:
        for path in expect.get(key, []):
            assert not path.startswith("/") and ".." not in Path(path).parts, (
                f"{case.name}: {key} paths must be relative to project/: {path}"
            )
    for path in expect.get("files_changed", []) + expect.get("files_unchanged", []):
        assert (case / "project" / path).is_file(), (
            f"{case.name}: {path} is expected to exist before the run"
        )

    second = spec.get("second_run")
    if second is not None:
        assert second.get("proposals") == [] and second.get("questions") == 0, (
            f"{case.name}: second_run should expect no proposals and 0 questions"
        )
