"""Grade a step by the files it left behind, not by the model's wording."""

import hashlib
import json
from pathlib import Path

KIND_WORDS = {
    "prune": ["prune", "remove", "trim"],
    "rehome": ["re-home", "rehome", "move"],
    "new-agent": ["new agent", "create"],
    "scoped-pointer": ["scoped", "only", "pointer"],
    "classification-question": ["archetype", "classif"],
    "split-offer": ["split", "two roles"],
}


def snapshot(root):
    """relative posix path -> sha256 of contents, for every file under root."""
    root = Path(root)
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def diff(before, after):
    created = sorted(set(after) - set(before))
    deleted = sorted(set(before) - set(after))
    changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
    return created, changed, deleted


def _subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            k in actual and _subset(v, actual[k]) for k, v in expected.items()
        )
    return expected == actual


def grade_step(expect, before, after, root, questions_asked, unmatched, texts):
    """Return (failures, warnings). Failures gate; warnings only report."""
    failures, warnings = [], []
    created, changed, deleted = diff(before, after)
    touched = set(created) | set(changed) | set(deleted)

    for p in expect.get("files_created", []):
        if p not in created:
            failures.append(f"expected {p} to be created")
    for p in expect.get("files_changed", []):
        if p not in changed:
            failures.append(f"expected {p} to be changed")
    for p in expect.get("files_unchanged", []):
        if p in touched:
            failures.append(f"expected {p} to stay unchanged")
    for p in expect.get("files_absent", []):
        if p in after:
            failures.append(f"expected {p} not to exist")

    if expect.get("exact"):
        allowed = set(expect.get("files_created", [])) | set(expect.get("files_changed", []))
        for p in sorted(touched - allowed):
            failures.append(f"unexpected change to {p}")
    else:
        allowed = set(expect.get("files_created", [])) | set(expect.get("files_changed", []))
        for p in sorted(touched - allowed):
            warnings.append(f"unlisted change to {p}")

    for assertion in expect.get("file_assertions", []):
        path = Path(root) / assertion["path"]
        if not path.is_file():
            failures.append(f"assertion on missing file {assertion['path']}")
            continue
        text = path.read_text()
        if "contains" in assertion and assertion["contains"] not in text:
            failures.append(f"{assertion['path']} should contain {assertion['contains']!r}")
        if "not_contains" in assertion and assertion["not_contains"] in text:
            failures.append(f"{assertion['path']} should not contain {assertion['not_contains']!r}")
        if "json_has" in assertion:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                failures.append(f"{assertion['path']} is not valid JSON")
                continue
            if not _subset(assertion["json_has"], data):
                failures.append(f"{assertion['path']} missing {assertion['json_has']!r}")

    if "questions" in expect and expect["questions"] != questions_asked:
        failures.append(f"expected {expect['questions']} question(s), got {questions_asked}")
    for q in unmatched:
        failures.append(f"no answer rule for question: {q!r}")

    blob = " ".join(texts).casefold()
    for proposal in expect.get("proposals", []):
        role = proposal["role"].casefold()
        words = [w for k in proposal["kinds"] for w in KIND_WORDS.get(k, [k])]
        if role not in blob or not any(w in blob for w in words):
            warnings.append(f"soft: no sign of a {proposal['kinds']} proposal for {proposal['role']}")
    return failures, warnings
