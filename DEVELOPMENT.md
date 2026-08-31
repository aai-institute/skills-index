# Development

## Enable the website

The site is built on every push to `main`, but publishing is off by
default. Enable one or both options with repository variables
(Settings > Secrets and variables > Actions > Variables):

1. GitHub Pages: set the variable `DEPLOY_PAGES` to `true`, and set the
   Pages source to GitHub Actions (Settings > Pages). The site deploys
   on the next push to `main`.
2. Release artifact: set the variable `CREATE_RELEASES` to `true`. Each
   push to `main` then publishes a GitHub Release with `index.html` and
   `skills.json` attached, so you can host the site elsewhere.

## Environment variables

The CI platform sets the repository variables. For a local build, you must
set them yourself.

| Variable | Function | Default |
| --- | --- | --- |
| `GITHUB_REPOSITORY` | GitHub Actions sets it. |
| `CI_PROJECT_PATH` and `CI_SERVER_HOST` | GitLab CI sets it. |

## Run the build locally

```sh
GITHUB_REPOSITORY=<owner>/<repo> uv run scripts/build_site.py
python3 -m http.server -d _site 8000
```

Then open http://localhost:8000. For a GitLab preview, set `CI_PROJECT_PATH`
and `CI_SERVER_HOST` in place of `GITHUB_REPOSITORY`.

## Releases

On GitHub, every push to `main` triggers `.github/workflows/release.yml`,
which builds the site and publishes a GitHub Release tagged
`main-<short-sha>` with `skills.json` and `index.html` attached as assets.
If the build step fails, no release is created.

To fetch a release's assets from another machine:

```sh
gh release download main-<short-sha> --repo <owner>/<repo> \
  --pattern '*' --dir /path/to/dest
```

Omit the tag to download the latest release instead.

## Notes

- If you do not set the environment variables for a local build, the install
  commands show an `OWNER/REPO` placeholder.
- If the repository is private, `gh release download` needs an authenticated
  token with at least read access to the repo's contents.
