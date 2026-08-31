# Development

## Enable the website

The site is built on every push to `main`, but publishing is off by
default. Enable one or both options with repository variables
(Settings > Secrets and variables > Actions > Variables):

1. GitHub Pages: set the variable `DEPLOY_PAGES` to `true`, and set the
   Pages source to GitHub Actions (Settings > Pages). The site deploys
   on the next push to `main`.
2. Release artifact: set the variable `CREATE_RELEASES` to `true`. Each
   push to `main` then publishes a GitHub Release with the complete site
   attached as `site.tar.gz`, so you can host the site elsewhere.

## Environment variables

The CI platform sets the repository variables. For a local build, you must
set them yourself.

| Variable | Function | Default |
| --- | --- | --- |
| `GITHUB_REPOSITORY` | GitHub Actions sets it. |

## Run the build locally

The script generates `skills.json` into `site/`, which makes `site/` the
complete deployable directory:

```sh
GITHUB_REPOSITORY=<owner>/<repo> uv run scripts/build_site.py
python3 -m http.server -d site 8000
```

## Releases

On GitHub, every push to `main` triggers `.github/workflows/release.yml`,
which builds the site and publishes a GitHub Release tagged
`main-<short-sha>` with `site.tar.gz`, an archive of the complete site
directory, attached as its only asset. If the build step fails, no
release is created.

To fetch and unpack the site from another machine:

```sh
gh release download main-<short-sha> --repo <owner>/<repo> \
  --pattern 'site.tar.gz' --dir /path/to/dest
tar -xzf /path/to/dest/site.tar.gz -C /path/to/dest
```

Omit the tag to download the latest release instead.

## Notes

- If you do not set the environment variables for a local build, the install
  commands show an `OWNER/REPO` placeholder.
- If the repository is private, `gh release download` needs an authenticated
  token with at least read access to the repo's contents.
