"""Deterministic checks for the castlist plugin repo.

Every check here exists because something real once slipped through review.
Run:  uv run --with pytest --with pyyaml pytest
"""

import json
import os
import re
import shutil
import subprocess

import pytest

from helpers import (
    ROOT,
    agent_names,
    command_names,
    frontmatter,
    rel,
    skill_dirs,
    split_frontmatter,
    tracked,
    tracked_files,
)

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
MODEL_TIERS = {"haiku", "sonnet", "opus", "inherit"}


# --- frontmatter ------------------------------------------------------------


@pytest.mark.parametrize("path", tracked("skills/*/SKILL.md"), ids=rel)
def test_skill_frontmatter(path):
    data = frontmatter(path)
    assert data.get("name") == path.parent.name, (
        f"{rel(path)}: name must equal its directory ({path.parent.name!r})"
    )
    assert str(data.get("description", "")).strip(), f"{rel(path)}: empty description"


@pytest.mark.parametrize("path", tracked("commands/*.md"), ids=rel)
def test_command_frontmatter(path):
    data = frontmatter(path)
    assert str(data.get("description", "")).strip(), f"{rel(path)}: empty description"


@pytest.mark.parametrize("path", tracked("agents/*.md"), ids=rel)
def test_agent_frontmatter(path):
    data = frontmatter(path)
    assert data.get("name") == path.stem, f"{rel(path)}: name must equal file stem"
    assert str(data.get("description", "")).strip(), f"{rel(path)}: empty description"
    assert data.get("model") in MODEL_TIERS, (
        f"{rel(path)}: model must be one of {sorted(MODEL_TIERS)}"
    )
    assert str(data.get("tools", "")).strip(), f"{rel(path)}: tools missing"


# --- manifests --------------------------------------------------------------


def _json(rel_path):
    return json.loads((ROOT / rel_path).read_text())


def test_manifests_agree():
    plugin = _json(".claude-plugin/plugin.json")
    market = _json(".claude-plugin/marketplace.json")
    release = _json(".release-please-manifest.json")
    entry = market["plugins"][0]

    assert plugin["name"] == entry["name"], "plugin.json and marketplace.json names differ"
    versions = {
        "plugin.json": plugin["version"],
        "marketplace.json plugins[0]": entry["version"],
        ".release-please-manifest.json": release["."],
    }
    for where, version in versions.items():
        assert SEMVER.match(version), f"{where}: {version!r} is not semver"
    assert len(set(versions.values())) == 1, f"versions disagree: {versions}"


# --- starter templates stay in sync with agents/ ----------------------------


def _archetype_to_agent():
    """Map archetype -> shipped agent name from archetypes.md's table."""
    text = (ROOT / "skills/prune/archetypes.md").read_text()
    mapping = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[3].startswith("`") and cells[3].endswith("`"):
            mapping[cells[0]] = cells[3].strip("`")
    return mapping


def _template_blocks():
    text = (ROOT / "skills/prune/archetypes.md").read_text()
    assert "## Starter templates" in text, "archetypes.md: '## Starter templates' missing"
    section = text.split("## Starter templates", 1)[1]
    blocks = {}
    for m in re.finditer(r"### (\w+)\n\n```markdown\n(.*?)\n```", section, re.S):
        blocks[m.group(1)] = m.group(2)
    return blocks


def _without_model_line(text):
    fm, body = split_frontmatter_text(text)
    kept = [l for l in fm.splitlines() if not l.startswith("model:")]
    return "---\n" + "\n".join(kept) + "\n---\n" + body


def split_frontmatter_text(text):
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    assert m, "no frontmatter block"
    return m.group(1), m.group(2)


def test_starter_templates_match_agents():
    mapping = _archetype_to_agent()
    blocks = _template_blocks()
    assert mapping, "archetypes.md: could not read the archetype table"
    assert set(blocks) == set(mapping), (
        f"template headings {sorted(blocks)} != archetypes {sorted(mapping)}"
    )
    for archetype, agent in mapping.items():
        expected = _without_model_line((ROOT / f"agents/{agent}.md").read_text()).strip()
        actual = blocks[archetype].strip()
        assert actual == expected, (
            f"skills/prune/archetypes.md '### {archetype}' drifted from "
            f"agents/{agent}.md (minus the model: line); update both together"
        )


# --- cross references -------------------------------------------------------


def _prose_files():
    return tracked("skills/*/*.md") + tracked("commands/*.md") + tracked("agents/*.md") + [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
    ]


def test_namespaced_references_resolve():
    valid = set(skill_dirs()) | set(agent_names()) | set(command_names())
    bad = []
    for path in _prose_files():
        for n, line in enumerate(path.read_text().splitlines(), 1):
            for name in re.findall(r"castlist:([a-z][a-z-]*)", line):
                if name not in valid:
                    bad.append(f"{rel(path)}:{n}: castlist:{name}")
    assert not bad, "references to names that don't exist:\n" + "\n".join(bad)


SECTION_REF = re.compile(
    r"[Ss]ections?[ -](\d+)[a-z]?(?:(?:,| and|, and) (\d+)[a-z]?)*"
)


def _headings(path):
    return {int(m.group(1)) for m in re.finditer(r"^## (\d+)\.", path.read_text(), re.M)}


def test_section_references_resolve():
    """A 'section N' mention must exist in this file, or in a skill the same
    paragraph names. Best-effort: catches stale numbers after a renumbering."""
    skills = {name: ROOT / f"skills/{name}/SKILL.md" for name in skill_dirs()}
    bad = []
    for name, path in skills.items():
        text = path.read_text()
        own = _headings(path)
        offset = 0
        for para in re.split(r"\n\s*\n", text):
            named = {
                other
                for other in skills
                if other != name and re.search(rf"(?<![\w-]){re.escape(other)}(?![\w-])", para)
            }
            allowed = set(own)
            for other in named:
                allowed |= _headings(skills[other])
            for m in SECTION_REF.finditer(para):
                numbers = {int(x) for x in re.findall(r"\d+", m.group(0))}
                missing = sorted(n for n in numbers if n not in allowed)
                if missing:
                    line = text[: text.index(para, offset)].count("\n") + 1
                    bad.append(f"{rel(path)}:{line}: '{m.group(0)}' -> no section {missing}")
            offset = text.index(para, offset) + len(para)
    assert not bad, "stale section references:\n" + "\n".join(bad)


# --- stale names ------------------------------------------------------------


def test_no_stale_plugin_name():
    """'right-model' may only appear in the README's rename note."""
    allowed_section = "### Renamed from right-model"
    offenders = []
    for path in tracked_files():
        if rel(path).startswith("tests/"):
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        in_note = False
        for n, line in enumerate(text.splitlines(), 1):
            if rel(path) == "README.md":
                if line.startswith(allowed_section):
                    in_note = True
                    continue
                if in_note and re.match(r"#{1,3} ", line):
                    in_note = False
            if "right-model" in line and not in_note:
                offenders.append(f"{rel(path)}:{n}")
    assert not offenders, "stale 'right-model' references:\n" + "\n".join(offenders)


# --- consumers --------------------------------------------------------------


@pytest.mark.network
@pytest.mark.skipif(shutil.which("npx") is None, reason="npx not installed")
def test_npx_skills_lists_every_skill():
    env = {**os.environ, "DISABLE_TELEMETRY": "1", "DO_NOT_TRACK": "1", "CI": "1"}
    out = subprocess.run(
        ["npx", "--yes", "skills", "add", str(ROOT), "--list"],
        capture_output=True, text=True, env=env, timeout=180,
    )
    text = out.stdout + out.stderr
    assert "SKILL_SKIPPED" not in text and "Skipped" not in text, (
        f"npx skills skipped a skill:\n{text}"
    )
    for name in skill_dirs():
        assert name in text, f"npx skills did not list {name!r}:\n{text}"


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
def test_plugin_validates():
    out = subprocess.run(
        ["claude", "plugin", "validate", str(ROOT)],
        capture_output=True, text=True, timeout=120,
    )
    assert out.returncode == 0, out.stdout + out.stderr
