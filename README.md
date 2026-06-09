# resume-toolkit

A [Claude Code](https://code.claude.com) **skills-directory plugin** for end-to-end resume
tailoring and job-application tracking. It parses a job description into a signal report,
drafts an ATS-optimized resume, reviews it against the JD, renders an ATS-parseable PDF,
and keeps a job-applications tracker in sync.

> ⚠️ **Heads-up: this is currently coupled to its author's workspace.** Paths are hardcoded
> (the plugin expects to live at `.claude/skills/resume-toolkit/`, and several skills read
> from `Work Experience/` and `Job Applications/` directories at the project root). It works
> out of the box only if you mirror that layout. Making it portable is on the roadmap — for
> now, treat it as a reference you'll adapt. PRs welcome.

## Skills

Once loaded, the skills are namespaced under `resume-toolkit:`.

| Skill | What it does |
|---|---|
| `resume-toolkit:job-application` | Orchestrates the full workflow end-to-end for one posting. |
| `resume-toolkit:extract-job-signals` | Parses a JD into a structured signal report (required/nice-to-have skills, title to mirror, knockout questions). |
| `resume-toolkit:build-targeted-resume` | Builds a tailored, ATS-optimized resume as styled HTML. |
| `resume-toolkit:review-resume` | Scores a resume against a JD and produces a prioritized list of fixes. |
| `resume-toolkit:publish-resume` | Renders the resume HTML to an ATS-parseable PDF and verifies it. |
| `resume-toolkit:update-application-tracker` | Reads/updates the job-applications tracker dashboard. |

## Install

This is a skills-directory plugin — no build step. Drop the repo into one of Claude Code's
skills directories so the `.claude-plugin/plugin.json` manifest is discovered:

```bash
# from your project root
git clone https://github.com/RevDrSquash/resume-toolkit.git .claude/skills/resume-toolkit
```

Or add it as a submodule of your own repo:

```bash
git submodule add https://github.com/RevDrSquash/resume-toolkit.git .claude/skills/resume-toolkit
```

Then run `/reload-plugins` (or restart Claude Code) and accept the workspace trust prompt.
The plugin loads as `resume-toolkit@skills-dir`.

## Python dependencies

The `publish-resume` / linter scripts under `scripts/` need a few packages:

```bash
pip install -r .claude/skills/resume-toolkit/scripts/requirements.txt
```

## License

[MIT](LICENSE)
