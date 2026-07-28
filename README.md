# resume-toolkit

A [Claude Code](https://code.claude.com) **skills-directory plugin** for end-to-end resume
tailoring and job-application tracking. It can discover matching postings via a local
OpenPostings backend, parse a job description into a signal report,
draft an ATS-optimized resume, review it against the JD, render an ATS-parseable PDF,
and keep a job-applications tracker in sync.

> ⚠️ **Heads-up: this is currently coupled to its author's workspace.** Several skills read
> from `Work Experience/` and `Job Applications/` directories at the project root, and the
> script-backed steps (PDF rendering, linting, JD fetch) use hardcoded `.claude/skills/resume-toolkit/scripts/…`
> paths — so those assume a manual install at that exact location. It works out of the box
> only if you mirror that layout. Making it portable is on the roadmap — for now, treat it as
> a reference you'll adapt. PRs welcome.

## Skills

Once loaded, the skills are namespaced under `resume-toolkit:`.

| Skill | What it does |
|---|---|
| `resume-toolkit:job-application` | Orchestrates the full workflow end-to-end for one posting (including shortlist handoff). |
| `resume-toolkit:job-scout` | Discovers new postings via OpenPostings saved searches; writes a ranked shortlist. Prefer the `job-scout` subagent. |
| `resume-toolkit:fetch-job-description` | Fetches exact JD markdown (OpenPostings CLI first; raw-HTML / LinkedIn fallbacks). |
| `resume-toolkit:generate-match-profile` | Builds `Work Experience/match-profile.md` + `Job Applications/scout-searches.json` for discovery. |
| `resume-toolkit:extract-job-signals` | Parses a JD into a structured signal report (required/nice-to-have skills, title to mirror, knockout questions). |
| `resume-toolkit:build-targeted-resume` | Builds a tailored, ATS-optimized resume as styled HTML. |
| `resume-toolkit:review-resume` | Scores a resume against a JD and produces a prioritized list of fixes. |
| `resume-toolkit:publish-resume` | Renders the resume HTML to an ATS-parseable PDF and verifies it. |
| `resume-toolkit:update-application-tracker` | Reads/updates the job-applications tracker dashboard. |

## Job discovery (OpenPostings)

Discovery is **optional** and additive. Manual JD paste/file/URL still works.

1. Install and run a local OpenPostings backend; put the CLI on PATH (`npm link` from your CLI fork).
2. From the Career workspace root: `openpostings skills install --claude` (installs `openpostings-cli`, `-search`, `-jd`, `-track` — do not duplicate those docs inside this plugin).
3. Run `generate-match-profile` once (seeds `match-profile.md` + `scout-searches.json`).
4. Run `job-scout` (subagent) to produce `Job Applications/Shortlist - <date>.md`.
5. Pick a shortlist entry and run `job-application` — it reuses the cached JD under `Job Applications/_Scout/` and continues through signals → resume → publish as before.

On confirmed submission, `job-application` also runs `openpostings applied <url>` so future scouts skip that posting. `Job Applications/index.html` remains the only canonical status tracker.

If the CLI or backend is down, discovery and applied/ignore write-backs degrade with a clear message; URL fetch falls back to HTTP / LinkedIn where possible.

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
