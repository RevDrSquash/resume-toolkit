# Handoff: resume-toolkit — job discovery integration

Handoff for a coding agent working in the resume-toolkit repo (cloned at `C:\Users\trist\OneDrive\Documents\Career\.claude\skills\resume-toolkit`, a Claude Code skills-directory plugin). Goal: integrate the toolkit with a locally running OpenPostings backend so jobs are automatically discovered, filtered against the user's experience, and handed into the existing resume-tailoring workflow.

## Context

### What exists today

**resume-toolkit** (this repo) handles everything *after* a job is chosen: `extract-job-signals` parses a JD into a signal report, `build-targeted-resume` drafts a tailored ATS-optimized resume, `review-resume` audits it, `publish-resume` renders the PDF, `update-application-tracker` maintains the canonical tracker at `Job Applications/index.html` (inline JSON block, statuses not-started → drafting → ready-to-submit → submitted → interview/offer/rejected/closed). `job-application` orchestrates the sequence. Experience content lives in `Work Experience/` at the project root; `Work Experience/personal-details.md` holds stable personal facts. Skills currently assume this workspace layout.

**OpenPostings** is a local-first job aggregator: an Express backend on `http://localhost:8787` syncs postings from ATS providers into a local SQLite DB (~757k postings, ~61k companies as of this writing). The companion CLI is **implemented and verified** in the fork at `E:\dev\openpostings-fork` (`cli/index.js`; put it on PATH via `npm link` from that repo). Commands: `search`, `jd <url>`, `ignore <url>`, `applied <url>`, `stats`, `skills`.

**The CLI ships its own agent skills.** `openpostings skills install --claude` copies four SKILL.md files (`openpostings-cli`, `openpostings-search`, `openpostings-jd`, `openpostings-track`) into `.claude/skills/`. Install these into the Career workspace and **reference them — do not duplicate CLI usage documentation inside resume-toolkit skills**. Toolkit skills should cover only what the bundled skills don't: the toolkit-side pipeline (extraction, flagging, formatting, scout procedure, tracker bridging).

The OpenPostings search matches only company/title/location substrings — never description text.

**Division of JD-fetching labor (firm decision, implemented):** the CLI's `jd` command owns *acquisition and deterministic normalization* — stored-description lookup, per-ATS JSON-API live fetchers (currently Ashby, Greenhouse, Workday; more can be added per `cli/AGENTS.md` in the fork), HTML→plain-text conversion including invisible-content stripping (comments, hidden/`display:none`/`visibility:hidden` elements). Contract (verified):

- Exit `0` = normalized text (source `db` or `ats-api`), exit `2` = raw HTML fallback (no parser for that ATS), exit `1` = error.
- **Always call it with `--json`**: successes, raw fallbacks, and errors all arrive as one JSON object on stdout — `{ ok, raw, source, job_posting_url, text }` or `{ ok:false, raw:false, source:null, error, error_kind }` with `error_kind` ∈ `not_found | empty_description | server_down | network | error` (`not_found` = posting dead, don't retry; `network` = may be transient).
- Live-fetch tiers work even when the backend server is down; only the `db` tier needs it.

This toolkit owns everything *after* acquisition: extraction from raw HTML when the CLI returns `raw: true`, injection flagging, output formatting, and the agent cleanup fallback.

### The integration seam

The two systems meet at the JD file: discovery produces `JD - <Company> - <Role>.md`, and the existing `job-application` workflow consumes it unchanged. The user applies manually — **no auto-apply anywhere in scope**.

### Division of tracking (firm decision)

`Job Applications/index.html` remains the **only canonical tracker**. OpenPostings' applied/ignored state is used purely as a discovery-side dedupe ledger: `ignore` on jobs dropped from a shortlist, `applied` when the user confirms submission, so future searches self-clean. No bidirectional status sync — statuses like interview/offer live only in the tracker.

## Components to build

### 1. `fetch-job-description` skill + script

A deterministic JD fetcher producing exact text. Motivation: built-in web/search tools paraphrase and misquote JDs; the toolkit depends on literal phrasing (`extract-job-signals` mandates exact JD wording, per-skill year minimums, knockout detection).

Acquisition is delegated to the OpenPostings CLI; this skill handles what comes back:

- **Primary path** — run `openpostings jd <url> --json` and branch on the envelope. `ok: true`: normalized exact text (`source` is `db` or `ats-api`), proceed straight to flagging + formatting. `raw: true`: unparsed page HTML in `text` — run local extraction (below). Error envelope or CLI not installed: `not_found` → treat the posting as dead; `server_down`/`network` → retry once or fall back to fetching the URL directly (plain HTTP GET, no paraphrasing web tools) and treat as raw HTML.
- **Raw-HTML extraction** — readability-style main-content extraction, HTML → markdown, plus invisible-content stripping (HTML comments, hidden elements, zero-width characters) since raw HTML hasn't been normalized by the CLI. Note: parsers for frequently-hit domains should be contributed to the CLI (its docs explain how to add one) rather than accumulating extraction special-cases here.
- **Agent-review fallback** — (see §"Agent cleanup pass" below), triggered only when extraction output fails sanity checks (implausibly short, navigation boilerplate, no sentence structure).
- **Non-ATS URLs** — LinkedIn URLs route to the existing `linkedin-job-to-markdown` skill; other company career pages go through the raw-HTML path.

Script goes in `scripts/` (Python, consistent with the repo's existing scripts; add deps to `scripts/requirements.txt`). The skill documents invocation and the fallback contract.

**Output format** — YAML frontmatter + faithful markdown body:

```markdown
---
company: <name or null>
title: <title or null>
url: <source url>
ats: <detected ats or "unknown">
fetched: <ISO date>
source: <cli-db | cli-ats-api | raw-extract | agent-cleanup>
warnings: []        # injection/suspicion flags, see below
---
<exact JD text as markdown>
```

**Sanitization policy (important — deliberate decisions):**

- **Strip invisible content deterministically**: HTML comments, `display:none`/`visibility:hidden`/`hidden` elements, zero-width characters, white-on-white text. This is the classic prompt-injection channel, and removing it does not diverge from "exact text as a human sees it" — a human never sees it rendered. (The CLI already does the HTML-level stripping on its parsed tiers; this toolkit must do it on the raw-HTML path, and should always do the zero-width-character pass regardless of source.)
- **Never strip visible text on keyword matches.** Words like "credentials", "password", "env" appear legitimately in JDs constantly; stripping would corrupt the exact text this tool exists to preserve, and keyword filters don't stop real attacks anyway.
- **Flag, don't strip**: a deterministic scan appends to `warnings` (and the skill surfaces them to the user) on: imperative instructions addressed to an AI/assistant ("ignore previous instructions" and variants), requests to send/upload data paired with a URL, large base64 blobs, credential/secret mentions adjacent to a URL. Ground truth stays intact.
- **Capability containment is the real defense** (document this in the skill): JD text is untrusted input. Steps that read JDs (signal extraction, resume drafting, scout scoring) should run in contexts without shell or network access — they only need to read the JD + experience notes and write markdown/HTML. Wrap JD content in clear delimiters marking it as untrusted data when embedding in prompts.

**Agent cleanup pass**: a subagent may reformat poorly-extracted output, but with a mechanical integrity guarantee — after cleanup, verify every output sentence is a substring of the fetched source text (after whitespace normalization). If verification fails, the agent rewrote content: discard the cleanup, return the deterministic extraction with a warning instead.

### 2. `match-profile` generation skill

Derive a compact `Work Experience/match-profile.md` (~1 page) from the `Work Experience/` notes: target titles, hard skills with approximate years, seniority band, and dealbreakers (location/remote constraints, salary floor, visa/clearance). This is the discovery-side mirror of a signal report, and it's what keeps scout scoring calls cheap — the full experience notes are never passed into filtering. Regenerated on demand when experience notes change. It also drives the saved-search definitions (below).

### 3. `job-scout` subagent + skill

The discovery orchestrator. The **procedure lives in a skill file** (versionable, tunable); **execution happens in a subagent** (e.g. a custom agent definition referencing the skill) because the working set — hundreds of search rows, a dozen full JDs — must not pollute the main conversation's context. The contract back to the main thread is small: the shortlist file path plus a ~3-line summary.

Flow per run:

1. **Saved searches**: run several narrow `openpostings search` queries (one per target-title/skill cluster from the match profile) and union results, rather than one broad query. Use `--new-since <last run>` and default applied/ignored exclusion. Searches are defined in a small config file (e.g. `Job Applications/scout-searches.md` or `.json`) the user tunes over time. Two verified behaviors to design around: (a) `--new-since` filters **client-side after** the server applies `--limit`, so always pair it with a generous `--limit` (e.g. 2000) or recent postings will be silently missed; (b) each search takes ~15–20 seconds against the full database (the server filters in memory), so a handful of saved searches costs a couple of minutes per scout run — fine for a daily run, but don't fan out dozens of queries.
2. **Skim** the union: skip obvious mismatches (wrong seniority, clearly unrelated roles, dealbreaker locations) using judgment on title/company/location/pay. This is deliberately NOT a separate batched LLM-triage pipeline stage — with narrow searches, volumes should be tens of rows. (If searches must ever be broadened and volumes reach many hundreds, a batched cheap-model triage stage is the known fallback — deferred, do not build now.)
3. **Fetch JDs** for plausible rows via `fetch-job-description`.
4. **Score fit** against `match-profile.md`; flag knockouts (year minimums, clearance, onsite requirements — same categories `extract-job-signals` defines).
5. **Write a ranked shortlist report** (file, e.g. `Job Applications/Shortlist - <date>.md`): per job one line of "why", fit score, knockout flags, pay/location, URL, and any injection warnings from the fetcher.
6. **Write back drops**: `openpostings ignore <url>` for scored-out jobs so they never resurface. Do NOT mark anything applied at this stage.

### 4. Handoff into the existing workflow

When the user picks a job from the shortlist (main thread, not the scout):

1. Create `Job Applications/<Company>/<Role>/` and save the already-fetched JD markdown there (no re-fetch).
2. Add the tracker row as `not-started` via `update-application-tracker`, with metadata from the posting (salary, location, posted date, JD URL).
3. Invoke `job-application` unchanged — it proceeds from its step 1 (signals) since the JD file exists.
4. When the user confirms submission (existing step 6), additionally run `openpostings applied <url>` so discovery excludes the job going forward. (Company/title are auto-resolved from the local DB; pass `--title`/`--company` only for postings that aren't in it, e.g. manually-found jobs. Recording an application clears any ignored state on the posting.)

Implement this as a thin extension to the `job-application` skill's intake (accept "a shortlist entry" as an input form) or as a small bridging section in the scout skill — whichever is less invasive to existing skills.

## Explicitly deferred / out of scope

- Batched LLM title-triage stage (only if search volumes force it)
- Embeddings / rerankers / local models for matching (revisit only with empirical evidence the funnel misses jobs)
- Auto-apply / any form submission (user applies manually)
- Bidirectional tracker sync with OpenPostings
- Storing fetched JDs back into the OpenPostings database

## Constraints

- Windows environment; scripts must run under Windows Python and handle UTF-8 explicitly (`encoding="utf-8"` on file I/O — Windows Python defaults to cp1252, which chokes on JD text). Follow the repo's existing conventions (skills as `skills/<name>/SKILL.md` with frontmatter; scripts in `scripts/`; deps in `scripts/requirements.txt`).
- Prerequisite setup (verify before building): `openpostings` on PATH (`npm link` in `E:\dev\openpostings-fork`), backend running, and the CLI's bundled skills installed via `openpostings skills install --claude` in the Career workspace.
- The toolkit currently hardcodes workspace-relative paths (`Work Experience/`, `Job Applications/`, `.claude/skills/resume-toolkit/scripts/…`) — match that convention rather than fixing portability here.
- OpenPostings backend may not be running: every OpenPostings-dependent step must degrade with a clear message rather than fail cryptically.
- Do not modify the five existing utility skills' contracts; extend around them.
