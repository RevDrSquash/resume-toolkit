# resume-toolkit

A [Claude Code](https://code.claude.com) **skills-directory plugin** for end-to-end resume
tailoring and job-application tracking. It maintains one or more master resumes, parses a
job description into a signal report, tailors the best-fit master for the posting, reviews
the draft against the JD, renders an ATS-parseable PDF, and keeps a job-applications
tracker in sync.

> ⚠️ **Heads-up: this is currently coupled to its author's workspace.** Several skills read
> from `Work Experience/`, `Resume Masters/`, and `Job Applications/` directories at the
> project root, and the script-backed steps (PDF rendering, linting, JD fetch) use hardcoded
> `.claude/skills/resume-toolkit/scripts/…` paths — so those assume a manual install at that
> exact location. It works out of the box only if you mirror that layout. Making it portable
> is on the roadmap — for now, treat it as a reference you'll adapt. PRs welcome.

## Skills

Once loaded, the skills are namespaced under `resume-toolkit:`.

| Skill | What it does |
|---|---|
| `resume-toolkit:job-application` | Orchestrates the full workflow end-to-end for one posting. |
| `resume-toolkit:fetch-job-description` | Fetches exact JD markdown (HTTP extraction; LinkedIn routed to its own skill). |
| `resume-toolkit:extract-job-signals` | Parses a JD into a structured signal report (required/nice-to-have skills, target title, role family, knockout questions). |
| `resume-toolkit:generate-master-resumes` | Creates or updates maintained master resumes from `Work Experience/` notes and the resume-masters manifest. |
| `resume-toolkit:build-targeted-resume` | Copies the best-fit master and tunes it into a tailored, ATS-optimized resume HTML. |
| `resume-toolkit:review-resume` | Scores a resume against a JD and produces a prioritized list of fixes. |
| `resume-toolkit:publish-resume` | Renders the resume HTML to an ATS-parseable PDF and verifies it. |
| `resume-toolkit:update-application-tracker` | Reads/updates the job-applications tracker dashboard. |

## User data (host project)

Expected at the project root when the plugin is installed:

| Path | Role |
|---|---|
| `Work Experience/` | Canonical experience notes, `personal-details.md`, and `resume-masters.md` (manifest declaring each master's purpose and stable identity). |
| `Resume Masters/` | Generated master HTML files (`Master Resume - <Name>.html`), built from the blank template. |
| `Job Applications/` | Per-posting JD, signal report, tailored resume HTML/PDF, and `index.html` tracker. |

The blank template at `skills/build-targeted-resume/resume-template.html` remains the sole layout/CSS source. Masters are filled from the notes; tailored resumes start from the selected master and keep that master's stable professional identity (they do not paste the JD title into the headline). Exact JD matching is confined to the Skills section when grounded; bullets stay in the candidate's own voice — selection and ordering over semantic rewrites — so the resume stays ATS-aware without looking mechanically reconstructed from the posting.

## Install

### Via marketplace (recommended)

The easiest way in. From Claude Code:

```
/plugin marketplace add RevDrSquash/personal-marketplace
/plugin install resume-toolkit@personal-marketplace
```

The plugin loads with its skills namespaced `resume-toolkit:*`. Run `/reload-plugins` if
they don't appear immediately.

### Manually (git)

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

> The script-backed skills (`publish-resume`, the linter, `fetch-job-description`) currently resolve their helper
> scripts at `.claude/skills/resume-toolkit/scripts/…` relative to the project root, so they
> only work with the manual install at that path. The reasoning-only skills work either way.

## Python dependencies

The `publish-resume` / linter / `fetch-job-description` scripts under `scripts/` need a few packages:

```bash
pip install -r .claude/skills/resume-toolkit/scripts/requirements.txt
```

## License

[MIT](LICENSE)
