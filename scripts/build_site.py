#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6"]
# ///
"""Builds the static site into _site/: copies site/ and generates skills.json
from the SKILL.md files in the skills folder.

Run with `uv run scripts/build_site.py`; uv installs the dependencies
declared above automatically.

Configuration, read from the environment:
  Repository location, taken from what the CI platform provides:
    GITHUB_REPOSITORY (owner/repo)   on GitHub Actions
  Set it manually for a local preview.
"""

import json
import os
import re
import shutil
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import yaml

ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "_site"
SKILLS_ROOT = ROOT / "skills"


@dataclass
class Skill:
    name: str
    description: str
    path: str
    install: str
    source: str


@dataclass
class Site:
    """Top-level shape of skills.json, consumed by site/index.html."""

    repoUrl: str
    installAll: str
    skills: List[Skill]


@dataclass
class Repo:
    """Where this repository lives remotely."""

    host: str
    slug: str

    @property
    def url(self) -> str:
        return f"https://{self.host}/{self.slug}"

    @property
    def tree_base(self) -> str:
        return f"{self.url}/tree/main"


def resolve_repo() -> Repo:
    if os.environ.get("GITHUB_REPOSITORY"):
        return Repo(host="github.com", slug=os.environ["GITHUB_REPOSITORY"])
    warnings.warn(
        "No repository configured: set GITHUB_REPOSITORY (owner/repo). "
        "Building with the OWNER/REPO placeholder, so the install commands "
        "and source links will not work.",
        stacklevel=2,
    )
    return Repo("github.com", "OWNER/REPO")


def find_skill_dirs(skills_root: Path) -> List[Path]:
    """Every directory under `skills_root` that holds a SKILL.md, except
    nested ones: a SKILL.md below another skill's directory is a supporting
    asset (e.g. a shipped template), not a skill of its own."""
    dirs = {f.parent for f in skills_root.rglob("SKILL.md")}
    dirs.discard(skills_root)
    return sorted(d for d in dirs if not any(p in dirs for p in d.parents))


def parse_frontmatter(text: str) -> dict:
    """Parses the leading --- delimited frontmatter block of `text` as YAML."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    attrs = yaml.safe_load(m.group(1)) if m else None
    return attrs if isinstance(attrs, dict) else {}


def load_skill(skill_dir: Path, repo: Repo) -> Skill:
    """One skills.json entry, built from a skill directory's SKILL.md."""
    attrs = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    rel_path = skill_dir.relative_to(ROOT).as_posix()

    return Skill(
        name=str(attrs.get("name") or skill_dir.name),
        description=str(attrs.get("description") or ""),
        path=rel_path,
        install=f"apm install {repo.slug} --skill {skill_dir.name}",
        source=f"{repo.tree_base}/{rel_path}",
    )


def build_site_data(repo: Repo) -> Site:
    skill_dirs = find_skill_dirs(SKILLS_ROOT)
    skills = sorted((load_skill(d, repo) for d in skill_dirs), key=lambda s: s.name)

    return Site(
        repoUrl=repo.url,
        installAll=f"apm install {repo.slug}",
        skills=skills,
    )


def write_output(site: Site) -> None:
    shutil.copytree(ROOT / "site", BUILD_DIR, dirs_exist_ok=True)
    (BUILD_DIR / "skills.json").write_text(
        json.dumps(asdict(site), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    repo = resolve_repo()
    site = build_site_data(repo)
    write_output(site)
    print(f"Built _site with {len(site.skills)} skill(s) for {repo.url}")


if __name__ == "__main__":
    main()
