"""Deterministic tests for the eval runner's pure logic (no model calls)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "evals"))

import answers  # noqa: E402
import grade  # noqa: E402
import selection  # noqa: E402

QUESTION = {
    "question": "Apply all proposed changes to the four files?",
    "header": "Apply?",
    "options": [
        {"label": "Apply all (Recommended)", "description": ""},
        {"label": "Decline", "description": ""},
    ],
    "multiSelect": False,
}


# --- answers ----------------------------------------------------------------


def test_rule_matches_header_question_and_text():
    assert answers.rule_matches(QUESTION, {"when": {"header": "apply"}})
    assert answers.rule_matches(QUESTION, {"when": {"question": "four files"}})
    assert answers.rule_matches(QUESTION, {"when": {"text": "APPLY"}})
    assert answers.rule_matches(QUESTION, {"when": {"option": "decline"}})
    assert not answers.rule_matches(QUESTION, {"when": {"option": "split"}})
    assert not answers.rule_matches(QUESTION, {"when": {"header": "archetype"}})
    assert answers.rule_matches(QUESTION, {"when": {}}), "empty when is a catch-all"


def test_select_prefers_exact_then_contains_then_free_text():
    opts = QUESTION["options"]
    assert answers._label_for("Decline", opts) == "Decline"
    assert answers._label_for("apply", opts) == "Apply all (Recommended)"
    assert answers._label_for("something else", opts) == "something else"


def test_answer_questions_first_matching_rule_and_unmatched_fallback():
    other = {**QUESTION, "question": "Which archetype is triager?", "header": "Archetype",
             "options": [{"label": "planning"}, {"label": "lookup"}]}
    rules = [{"when": {"text": "archetype"}, "select": "lookup"}, {"when": {}, "select": "Apply"}]
    got, unmatched = answers.answer_questions([QUESTION, other], rules)
    assert got == {QUESTION["question"]: "Apply all (Recommended)", other["question"]: "lookup"}
    assert unmatched == []

    got, unmatched = answers.answer_questions([other], [{"when": {"text": "nothing"}, "select": "x"}])
    assert unmatched == [other["question"]]
    assert got[other["question"]] == "planning", "unmatched falls back to the first option"


def test_multiselect_returns_a_list_of_labels():
    q = {"question": "Roles?", "header": "Roles", "multiSelect": True,
         "options": [{"label": "planner"}, {"label": "verifier"}]}
    got, _ = answers.answer_questions([q], [{"when": {}, "select": ["planner", "verifier", "builder"]}])
    assert got["Roles?"] == ["planner", "verifier", "builder"]


# --- grade ------------------------------------------------------------------


def _tree(tmp_path, files):
    for name, text in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return grade.snapshot(tmp_path)


def test_grade_files_and_assertions(tmp_path):
    before = _tree(tmp_path, {"a.md": "keep", "b.md": "old npm test", "c.md": "same"})
    (tmp_path / "b.md").write_text("new")
    (tmp_path / "d.json").write_text('{"roles": {"triager": "lookup"}}')
    after = grade.snapshot(tmp_path)

    expect = {
        "files_created": ["d.json"], "files_changed": ["b.md"], "files_unchanged": ["a.md", "c.md"],
        "file_assertions": [
            {"path": "b.md", "not_contains": "npm test"},
            {"path": "d.json", "json_has": {"roles": {"triager": "lookup"}}},
        ],
        "questions": 1,
    }
    failures, warnings = grade.grade_step(expect, before, after, tmp_path, 1, [], [])
    assert failures == [] and warnings == []


def test_grade_reports_each_kind_of_failure(tmp_path):
    before = _tree(tmp_path, {"a.md": "x", "b.md": "y"})
    (tmp_path / "a.md").write_text("changed")
    after = grade.snapshot(tmp_path)
    expect = {
        "files_created": ["new.md"], "files_unchanged": ["a.md"], "files_absent": ["b.md"],
        "file_assertions": [{"path": "a.md", "contains": "nope"}, {"path": "zzz", "contains": "x"}],
        "questions": 0, "exact": True,
    }
    failures, _ = grade.grade_step(expect, before, after, tmp_path, 2, ["why?"], [])
    text = " | ".join(failures)
    for fragment in ["new.md to be created", "a.md to stay unchanged", "b.md not to exist",
                     "should contain 'nope'", "missing file zzz", "expected 0 question(s), got 2",
                     "no answer rule for question: 'why?'", "unexpected change to a.md"]:
        assert fragment in text, f"missing failure: {fragment}\n{text}"


def test_soft_proposals_only_warn(tmp_path):
    before = after = _tree(tmp_path, {"a.md": "x"})
    expect = {"proposals": [{"role": "planner", "kinds": ["prune"]}]}
    failures, warnings = grade.grade_step(expect, before, after, tmp_path, 0, [], ["nothing relevant"])
    assert failures == [] and len(warnings) == 1
    failures, warnings = grade.grade_step(expect, before, after, tmp_path, 0, [],
                                          ["Planner: prune the npm test line"])
    assert failures == [] and warnings == []


def test_questions_include_checks_asked_question_text(tmp_path):
    before = after = _tree(tmp_path, {"a.md": "x"})
    expect = {"questions_include": ["split"]}
    failures, _ = grade.grade_step(expect, before, after, tmp_path, 1, [], [],
                                   ["Roles Which starting roles?"])
    assert failures == ["no question mentioned 'split'"]
    failures, _ = grade.grade_step(expect, before, after, tmp_path, 1, [], [],
                                   ["Builder Split builder into two roles?"])
    assert failures == []


# --- selection --------------------------------------------------------------

CASES = {
    "prune-a": {"covers": ["skills/prune/**", "agents/**"]},
    "setup-a": {"covers": ["skills/setup/**", "skills/prune/**", "skills/catch-up/**"]},
}


def test_selection_by_covers():
    assert selection.affected(["skills/prune/SKILL.md"], CASES) == ["prune-a", "setup-a"]
    assert selection.affected(["skills/catch-up/SKILL.md"], CASES) == ["setup-a"]
    assert selection.affected(["agents/planner.md"], CASES) == ["prune-a"]
    assert selection.affected(["README.md", "CONTRIBUTING.md"], CASES) == []


def test_selection_evals_and_fixture_paths():
    assert selection.affected(["tests/evals/runner.py"], CASES) == ["prune-a", "setup-a"]
    assert selection.affected(["tests/fixtures/setup-a/expected.json"], CASES) == ["setup-a"]
    assert selection.affected(["tests/fixtures/unknown/x.md"], CASES) == []
