#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pytest>=8", "pyyaml>=6"]
# ///
"""Tests for build_site.py.

Run with `uv run scripts/test_build_site.py`.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_site
from build_site import (
    Repo,
    find_skill_dirs,
    load_skill,
    parse_frontmatter,
    resolve_repo,
)

REPO = Repo(host="github.com", slug="owner/repo", platform="github")


@pytest.fixture
def fake_root(tmp_path):
    """A temporary repository root with an empty skills folder."""
    (tmp_path / "skills").mkdir()
    return tmp_path


def create_skill(root: Path, name: str, frontmatter: str) -> Path:
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\n{frontmatter}\n---\nBody.\n", encoding="utf-8"
    )
    return skill_dir


def test_repo_discovery(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    assert resolve_repo() == REPO


def test_skill_discovery(fake_root):
    skill1 = create_skill(fake_root, "skill1", "name: skill1")
    skill2 = create_skill(fake_root, "skill2", "name: skill2")
    assert find_skill_dirs(fake_root / "skills") == [skill1, skill2]


def test_parse_frontmatter_reads_name_and_description():
    attrs = parse_frontmatter("---\nname: demo\ndescription: A demo.\n---\nBody.\n")
    assert attrs == {"name": "demo", "description": "A demo."}


@pytest.mark.parametrize(
    "frontmatter, expected_error",
    [
        ("description: A demo.", "missing name"),
        ("name: demo", "missing description"),
        ("license: MIT", "missing name and description"),
    ],
)
def test_load_skill_missing_fields_raise(fake_root, frontmatter, expected_error):
    skill_dir = create_skill(fake_root, "demo", frontmatter)
    with pytest.raises(ValueError, match=expected_error):
        load_skill(fake_root, skill_dir, REPO)


def test_load_skill_builds_skill_dataclass(fake_root):
    skill_dir = create_skill(fake_root, "demo", "name: demo\ndescription: A demo.")
    skill = load_skill(fake_root, skill_dir, REPO)
    assert skill.name == "demo"
    assert skill.description == "A demo."
    assert skill.path == "skills/demo"
    assert skill.install == "apm install github.com/owner/repo/skills/demo"
    assert skill.source == "https://github.com/owner/repo/tree/main/skills/demo"


def test_build_site_data_builds_site_dataclass(fake_root):
    create_skill(fake_root, "demo1", "name: demo1\ndescription: Last.")
    create_skill(fake_root, "demo2", "name: demo2\ndescription: First.")
    site = build_site.build_site_data(fake_root, REPO, fake_root / "skills")
    assert site.repoUrl == "https://github.com/owner/repo"
    assert [s.name for s in site.skills] == ["demo1", "demo2"]


def test_build_pipeline_writes_skills_json(fake_root, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    create_skill(fake_root, "demo", "name: demo\ndescription: A demo.")
    out_file = fake_root / "skills.json"

    repo = resolve_repo()
    site = build_site.build_site_data(fake_root, repo, fake_root / "skills")
    build_site.write_skills_json(site, out_file)

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data == {
        "repoUrl": "https://github.com/owner/repo",
        "skills": [
            {
                "name": "demo",
                "description": "A demo.",
                "path": "skills/demo",
                "install": "apm install github.com/owner/repo/skills/demo",
                "source": "https://github.com/owner/repo/tree/main/skills/demo",
            }
        ],
    }


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
