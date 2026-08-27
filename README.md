# Skill Index Template

This template makes a website for the agent skills of a repository.
The website shows each skill with its description and an install command.
Users can search the skills and copy the commands.

## Supported platforms

- The template works with a public repository on github.com or on GitLab
  (gitlab.com).
- On GitHub, GitHub Actions builds the website and GitHub Pages serves it.
  On GitLab, the `pages` job in `.gitlab-ci.yml` does the same with GitLab
  Pages.
- The install commands use [APM](https://microsoft.github.io/apm/).

## Environment variables

The CI platform sets the repository variables. For a local build, you must
set them yourself.

| Variable | Function | Default |
| --- | --- | --- |
| `GITHUB_REPOSITORY` | GitHub Actions sets it. |
| `CI_PROJECT_PATH` | GitLab CI sets it. |
| `CI_SERVER_HOST` | GitLab CI sets it. |

## Set up your index

1. Make a public repository from this template. Use "Use this template" on
   GitHub, or fork the repository on GitLab.
2. On GitHub: open the repository settings. In "Pages", set the source to
   "GitHub Actions". On GitLab: no configuration is necessary.
3. Put your skills in the `skills/` folder.
4. Push to `main`. The website then shows at
   `https://<owner>.github.io/<repo>/` or
   `https://<owner>.gitlab.io/<repo>/`.

## Add a skill

1. Make a folder for the skill, for example `skills/<skill-name>/`.
2. Make the file `SKILL.md` in the folder, and write a skill.
3. Merge the change to `main`. The website then shows the new skill.


## Run the build locally

```sh
GITHUB_REPOSITORY=<owner>/<repo> uv run scripts/build_site.py
python3 -m http.server -d _site 8000
```

Then open http://localhost:8000. For a GitLab preview, set `CI_PROJECT_PATH`
and `CI_SERVER_HOST` in place of `GITHUB_REPOSITORY`.

## Gotchas

- Currently works for `Github` and `Gitlab` repositories.
- Keep the name of the skills folder `skills`. APM finds
  the skills only in this folder when you install the full index.
- If you do not set the environment variables for a local build, the install
  commands show an `OWNER/REPO` placeholder.
- The build ignores a `SKILL.md` that is in a subfolder of a different
  skill. Such a file is an asset of that skill, not a skill.
- The website shows the `name` from the frontmatter. If the frontmatter has
  no `name`, the website shows the folder name.
