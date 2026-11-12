"""Shared helpers for the repo checks. Only tracked files are inspected."""

import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [ROOT / line for line in out.splitlines() if (ROOT / line).is_file()]


def tracked(pattern):
    """Tracked files whose repo-relative posix path matches a glob pattern."""
    return sorted(p for p in tracked_files() if p.relative_to(ROOT).match(pattern))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def split_frontmatter(path):
    """Return (frontmatter_text, body) for a file that starts with '---'."""
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    assert m, f"{rel(path)}: no YAML frontmatter block"
    return m.group(1), m.group(2)


def frontmatter(path):
    """Strictly parse frontmatter; a YAML error fails the calling test."""
    fm_text, _ = split_frontmatter(path)
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as err:
        raise AssertionError(
            f"{rel(path)}: frontmatter is not valid YAML "
            f"(quote values that contain ': '): {err}"
        ) from err
    assert isinstance(data, dict), f"{rel(path)}: frontmatter is not a mapping"
    return data


def skill_dirs():
    return sorted(p.parent.name for p in tracked("skills/*/SKILL.md"))


def agent_names():
    return sorted(p.stem for p in tracked("agents/*.md"))


def command_names():
    return sorted(p.stem for p in tracked("commands/*.md"))
