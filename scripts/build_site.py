#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6"]
# ///
"""Generates skills.json from the SKILL.md files in the skills folder.

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
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Literal

import yaml


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
    skills: List[Skill]


@dataclass
class Repo:
    """Where this repository lives remotely."""

    host: str
    slug: str
    platform: Literal["github"]

    @property
    def url(self) -> str:
        return f"https://{self.host}/{self.slug}"

    @property
    def tree_base(self) -> str:
        return f"{self.url}/tree/main"


def resolve_repo() -> Repo:
    if os.environ.get("GITHUB_REPOSITORY"):
        return Repo(
            host="github.com", slug=os.environ["GITHUB_REPOSITORY"], platform="github"
        )
    warnings.warn(
        "No repository configured: set GITHUB_REPOSITORY (owner/repo). "
        "Building with the OWNER/REPO placeholder, so the install commands "
        "and source links will not work.",
        stacklevel=2,
    )
    return Repo("github.com", "OWNER/REPO", "github")


def find_skill_dirs(skills_root: Path) -> List[Path]:
    """Every directory under `skills_root` that holds a SKILL.md, except
    nested ones: a SKILL.md below another skill's directory is a supporting
    asset (e.g. a shipped template), not a skill of its own."""
    dirs = {f.parent for f in skills_root.rglob("SKILL.md")}
    dirs.discard(skills_root)
    return sorted(d for d in dirs if not any(p in dirs for p in d.parents))


def parse_frontmatter(text: str) -> dict:
    """Parses the leading --- delimited frontmatter block of `text` as YAML.

    Raises ValueError when the block is not valid YAML."""
    text = text.lstrip("\ufeff")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if not match:
        return {}
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as err:
        raise ValueError(
            f"invalid YAML in frontmatter: {err}\n"
            "Hint: wrap the value in double quotes if it contains ': ' or "
            "starts with a character such as [ { * ` @ | > - or a quote."
        ) from err
    return frontmatter if isinstance(frontmatter, dict) else {}


def load_skill(root: Path, skill_dir: Path, repo: Repo) -> Skill:
    """One skills.json entry, built from a skill directory's SKILL.md.

    The Agent Skills specification requires `name` and `description` in the
    frontmatter and requires `name` to match the skill directory name, so a
    SKILL.md that breaks either rule fails the build."""

    skill_md = skill_dir / "SKILL.md"
    try:
        frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as err:
        raise ValueError(f"{skill_md.relative_to(root)}: {err}") from err
    missing = [field for field in ("name", "description") if not frontmatter.get(field)]
    if missing:
        raise ValueError(
            f"{skill_md.relative_to(root)}: skill is missing {' and '.join(missing)}"
        )
    name = str(frontmatter["name"])
    if name != skill_dir.name:
        raise ValueError(
            f"{skill_md.relative_to(root)}: name '{name}' must match the "
            f"directory name '{skill_dir.name}'"
        )
    rel_path = skill_dir.relative_to(root).as_posix()

    install_command = f"apm install {repo.host}/{repo.slug}/{rel_path}"

    return Skill(
        name=name,
        description=str(frontmatter["description"]),
        path=rel_path,
        install=install_command,
        source=f"{repo.tree_base}/{rel_path}",
    )


def build_site_data(root: Path, repo: Repo, skills_root: Path) -> Site:
    skill_dirs = find_skill_dirs(skills_root)
    skills = sorted(
        (load_skill(root, d, repo) for d in skill_dirs), key=lambda s: s.name
    )

    return Site(
        repoUrl=repo.url,
        skills=skills,
    )


def write_skills_json(site: Site, out_file: Path) -> None:
    out_file.write_text(
        json.dumps(asdict(site), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    skills_root = root / "skills"
    out_file = root / "site" / "skills.json"
    repo = resolve_repo()
    try:
        site = build_site_data(root, repo, skills_root)
    except ValueError as err:
        raise SystemExit(str(err)) from err
    write_skills_json(site, out_file)
    print(f"Wrote {out_file.name} with {len(site.skills)} skill(s) for {repo.url}")


if __name__ == "__main__":
    main()
