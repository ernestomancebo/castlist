"""Fixture projects must be well-formed, so the eval runner can trust them.

tests/fixtures/<case>/
  project/        a copy-ready scratch project (.claude/agents/*.md, CLAUDE.md, ...)
  expected.json   covers + steps (prompt, scripted answers, expected outcomes)
"""

import fnmatch
import json
from pathlib import Path

import pytest

from helpers import ROOT, frontmatter, rel, tracked_files

FIXTURES = ROOT / "tests" / "fixtures"
CASES = sorted(p for p in FIXTURES.iterdir() if p.is_dir())

KINDS = {"prune", "rehome", "new-agent", "scoped-pointer", "classification-question", "split-offer"}
# Roles proposed for creation / bootstrap don't exist in project/ yet.
ROLE_NOT_ON_DISK = {"new-agent", "split-offer"}
FILE_LISTS = ("files_created", "files_changed", "files_unchanged", "files_absent")
EXPECT_KEYS = set(FILE_LISTS) | {"file_assertions", "questions", "questions_include", "proposals", "exact"}
WHEN_KEYS = {"header", "question", "text", "option"}
ASSERTION_KEYS = {"path", "contains", "not_contains", "json_has"}


def test_fixtures_exist():
    assert len(CASES) >= 7, f"expected the seeded cases under {rel(FIXTURES)}"


@pytest.mark.parametrize("case", CASES, ids=lambda p: p.name)
def test_fixture_well_formed(case):
    spec_path = case / "expected.json"
    assert spec_path.is_file(), f"{case.name}: expected.json missing"
    assert (case / "project").is_dir(), f"{case.name}: project/ missing"
    spec = json.loads(spec_path.read_text())

    assert str(spec.get("description", "")).strip(), f"{case.name}: description missing"
    assert isinstance(spec.get("gating", True), bool), f"{case.name}: gating must be a bool"

    covers = spec.get("covers")
    assert isinstance(covers, list) and covers, f"{case.name}: covers must be a non-empty list"
    tracked = [rel(p) for p in tracked_files()]
    for glob in covers:
        assert any(fnmatch.fnmatchcase(t, glob) for t in tracked), (
            f"{case.name}: covers glob {glob!r} matches no tracked file"
        )

    steps = spec.get("steps")
    assert isinstance(steps, list) and steps, f"{case.name}: steps must be a non-empty list"

    agents_dir = case / "project" / ".claude" / "agents"
    agent_files = list(agents_dir.glob("*.md")) if agents_dir.is_dir() else []
    on_disk = {p.stem for p in agent_files}
    for agent in agent_files:
        assert frontmatter(agent).get("name") == agent.stem, f"{rel(agent)}: name != file stem"

    for index, step in enumerate(steps):
        where = f"{case.name} step {index + 1}"
        assert str(step.get("prompt", "")).startswith("/castlist:"), (
            f"{where}: prompt must start with /castlist:"
        )
        for rule in step.get("answers", []):
            assert set(rule.get("when", {})) <= WHEN_KEYS, f"{where}: bad `when` keys in {rule}"
            select = rule.get("select")
            assert isinstance(select, (str, list)) and select, f"{where}: rule needs `select`: {rule}"

        expect = step.get("expect", {})
        assert set(expect) <= EXPECT_KEYS, f"{where}: unknown expect keys {set(expect) - EXPECT_KEYS}"
        for key in FILE_LISTS:
            for path in expect.get(key, []):
                assert not path.startswith("/") and ".." not in Path(path).parts, (
                    f"{where}: {key} paths must be relative to project/: {path}"
                )
        for assertion in expect.get("file_assertions", []):
            assert set(assertion) <= ASSERTION_KEYS and "path" in assertion, (
                f"{where}: bad file_assertion {assertion}"
            )
        for proposal in expect.get("proposals", []):
            kinds = proposal.get("kinds")
            assert isinstance(kinds, list) and kinds and set(kinds) <= KINDS, (
                f"{where}: proposal kinds must be a non-empty subset of {sorted(KINDS)}: {proposal}"
            )
            if not set(kinds) <= ROLE_NOT_ON_DISK:
                assert proposal.get("role") in on_disk, (
                    f"{where}: role {proposal.get('role')!r} has no project/.claude/agents/ file"
                )
        if index == 0:  # later steps may rely on files earlier steps create
            for path in expect.get("files_changed", []) + expect.get("files_unchanged", []):
                assert (case / "project" / path).is_file(), (
                    f"{where}: {path} is expected to exist before the run"
                )
