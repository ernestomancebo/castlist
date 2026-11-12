"""Pick the eval cases affected by a change. Pure except `changed_paths`."""

import fnmatch
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_cases(fixtures_dir=FIXTURES):
    cases = {}
    for spec_path in sorted(Path(fixtures_dir).glob("*/expected.json")):
        cases[spec_path.parent.name] = json.loads(spec_path.read_text())
    return cases


def affected(changed, cases):
    """Case names whose `covers` globs match a changed path.

    A change under tests/evals/ selects every case; a change under
    tests/fixtures/<case>/ selects that case."""
    selected = set()
    for path in changed:
        if path.startswith("tests/evals/"):
            return sorted(cases)
        parts = path.split("/")
        if path.startswith("tests/fixtures/") and len(parts) > 2 and parts[2] in cases:
            selected.add(parts[2])
        for name, spec in cases.items():
            if any(fnmatch.fnmatchcase(path, glob) for glob in spec.get("covers", [])):
                selected.add(name)
    return sorted(selected)


def changed_paths(ref, cwd=ROOT):
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{ref}...HEAD"],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if line]
