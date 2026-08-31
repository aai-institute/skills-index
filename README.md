# Skill Index

Builds a website for the agent skills of a repository. The website shows 
each skill with its description and an install command. Users can search the skills 
and copy the installation command. The install commands use [APM](https://microsoft.github.io/apm/).

## Add a skill

1. Make a folder for the skill, under the skills folder. For example `skills/<skill-name>/`.
2. Add the file `SKILL.md` in the folder, and write a skill.
3. When the change is merged to `main`, the website shows the new skill.

## Notes

- Keep the name of the skills folder `skills`. APM finds
  the skills only in this folder when you install the full index.
- `SKILL.md` that is in a subfolder of a different skill is skipped.
- The skill must have a `name` and a `description`.

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the local build, the environment
variables, and the release process.
