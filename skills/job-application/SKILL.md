---
name: job-application
description: Orchestrate the end-to-end resume tailoring workflow for a specific job. Parses the JD, ensures master resumes are current, drafts a tailored resume from the best-fit master, audits it, iterates with the user, and publishes the final PDF. Trigger when the user wants to apply for a specific posting, tailor a resume for a job, or run the full resume flow end-to-end. Composes fetch-job-description, extract-job-signals, generate-master-resumes, build-targeted-resume, review-resume, publish-resume, and update-application-tracker.
---

# Job Application

Orchestrate the full resume tailoring workflow for a specific job. This skill is glue: it sequences utility skills, keeps the application tracker in sync, and gates the whole thing on user review. It does not duplicate their logic — for each step, invoke the utility.

## When to use

- User shares a job description (URL, pasted text, file) and wants to apply
- User says things like "tailor my resume for this role", "let's apply to X", "run the full flow for this posting"
- User wants the whole sequence run, not just one step

If the user explicitly asks for a single step ("just extract signals", "just review this resume against the JD"), invoke that utility skill directly. This skill is for the full workflow only.

## Inputs

Accept **any one** of these JD intake forms:

1. **URL** — LinkedIn or ATS/company career page.
2. **Existing markdown file** or pasted JD text.
3. **Manual** — user already saved `JD - <Company> - <Role>.md` in the job folder.

Also required:

- Path to the user's experience notes (`Work Experience/`)
- Stable personal facts (`Work Experience/personal-details.md` — contact info and education). The downstream resume build reads this for the header and Education section, so these never need to be pulled from an old resume (see "Canonical sources" below).
- Master manifest and masters (`Work Experience/resume-masters.md` and `Resume Masters/Master Resume - <Name>.html`). If missing or stale, this skill invokes `generate-master-resumes` before building (see step 1.5).
- Company name and role title (required or inferable) for the output folder name

## Workflow

Run the steps in order. Each step delegates to a utility skill; stay inside the utility's contract rather than re-implementing the work here. Between steps, keep the tracker (`Job Applications/index.html`) in sync via `update-application-tracker` — see the "Tracker maintenance" section below.

### 0. Materialize the JD and ensure a tracker row

**0a. Resolve JD markdown into the job folder** (`Job Applications/<Company>/<Role>/JD - <Company> - <Role>.md`):

| Intake | Action |
|--------|--------|
| Existing file / paste | Save into the job folder if not already there. |
| LinkedIn URL | Invoke `linkedin-job-to-markdown`; save into the job folder. |
| Any other URL | Invoke `fetch-job-description` (`scripts/fetch_jd.py`). **Do not use WebFetch** to obtain JD text — it paraphrases. |

Create the `Job Applications/<Company>/<Role>/` directory if needed.

**0b. Tracker row.** Invoke `update-application-tracker` to confirm a row exists for this posting. If not, add one as `not-started` with whatever metadata is available (company, title, location, salary, posted date, JD URL). The tracker is the canonical record; everything downstream assumes the row exists.

### 1. Extract signals
Invoke `extract-job-signals` on the JD markdown from step 0. Save the resulting signal report into the job-application folder as `Signal Report - <Company> - <Role>.md`. The JD file must already be in the folder from step 0 — do not re-fetch here. Then bump tracker status to `drafting`.

### 1.5. Ensure masters exist and are current
Before building, verify the master baseline:

1. Confirm `Work Experience/resume-masters.md` exists and every entry has a matching `Resume Masters/Master Resume - <Name>.html`.
2. Freshness check: if any file under `Work Experience/` (notes, skills, personal-details, or the manifest itself) is newer than the selected/available master HTML files, treat the masters as **stale**.
3. If masters or the manifest are **missing** or **stale**, tell the user and invoke `generate-master-resumes` (with confirmation when regenerating stale masters that the user may have been using). Do not silently skip this gate.
4. If the user explicitly declines to create/update masters, proceed only with their acknowledgment that `build-targeted-resume` will fall back to the blank template — and note that credibility/consistency benefits of the master flow will be missing.

### 2. Build the tailored resume
Invoke `build-targeted-resume`, passing the JD, the signal report, the master manifest (`Work Experience/resume-masters.md`), the `Resume Masters/` HTML files, the user's experience notes (`Work Experience/`), and the stable personal facts (`Work Experience/personal-details.md`). The utility selects the best-fit master, copies it into the job folder, and tunes it — producing `Resume - <Company> - <Role>.html`.

### 3. Audit the draft
Invoke `review-resume` on the generated HTML against the **full JD** (`JD - <Company> - <Role>.md` from step 0) — not the signal report. The signal report was the input that built the resume, so auditing against it would only re-check the same reduced spec; the review must hit ground truth to catch anything the signal extraction dropped. (If the JD markdown somehow isn't available, fall back per `review-resume`'s own target order.) Surface the prioritized critique (Critical / Material / Minor) to the user. Do not silently apply the suggested fixes — that's the iteration step's job.

### 4. Iterate with the user
This is the human-review gate.

- Present the review findings and ask which fixes to apply
- For each batch of accepted changes, re-invoke `build-targeted-resume` (full HTML output, not a diff) with the additional instructions — still starting from the selected master baseline plus the accepted edits, not from a blank template
- Optionally re-run `review-resume` after a substantive edit pass
- Continue until the user explicitly signs off on the current draft

Do not advance to step 5 without explicit user approval, even if the review reports zero critical issues.

### 5. Publish
Invoke `publish-resume` on the approved HTML. The utility renders the PDF, verifies page count, and runs the Notepad parseability check. Report the PDF path and parseability result back to the user. Then bump tracker status to `ready-to-submit` and record `resumeHtml` + `resumePdf` filenames on the row.

### 6. Hand off to the user
Tell the user the resume is ready and the next move is theirs: review the PDF one last time, submit the application, and report back. When they confirm submission, run `update-application-tracker` to flip status to `submitted` and capture the `dateSubmitted` they give you. The HTML tracker is the **only** canonical status record (interview/offer/etc. live only there).

## Output folder layout

```
Job Applications/
  index.html                                  # tracker; updated via update-application-tracker
  <Company>/
    <Role>/
      JD - <Company> - <Role>.md
      Signal Report - <Company> - <Role>.md
      Resume - <Company> - <Role>.html
      Resume - <Company> - <Role>.pdf
```

Masters (shared across applications, not per posting):

```
Work Experience/resume-masters.md
Resume Masters/
  Master Resume - <Name>.html
```

If the user wants the review audit persisted, add `Review - <Company> - <Role>.md` alongside the others.

## Tracker maintenance

`Job Applications/index.html` is the authoritative tracker. Keep it in sync at every status transition by invoking `update-application-tracker`:

| Workflow point                                    | Tracker change                                            |
|---------------------------------------------------|-----------------------------------------------------------|
| Step 0 — posting not yet tracked                  | Add row as `not-started` with available metadata          |
| After step 1 — signal report saved                | Status → `drafting`                                       |
| After step 5 — PDF rendered, page count verified  | Status → `ready-to-submit`; set `resumeHtml`, `resumePdf` |
| User confirms they submitted the application      | Status → `submitted`; set `dateSubmitted`                 |
| User reports interview / offer / rejection / skip | Status → matching value; capture context in `notes`       |

Tracker edits never advance status on assumption — only on user confirmation. Reach for the tracker skill's full status table (`update-application-tracker`) when the transition is unclear.

## Rules and constraints

- **Tailor from masters, not from a previous tailored resume.** Formatting/layout originates in the blank template and is carried by the masters; experience content comes from the `Work Experience/` notes; personal facts come from `Work Experience/personal-details.md`; the per-posting draft starts from the selected master. Previous tailored resumes under `Job Applications/<Company>/<Role>/` are **presumed stale** — consult them only as a last resort when a canonical source is genuinely missing something, verify against canonical, and prefer back-filling the notes (then regenerating masters) over copying a tailored artifact forward. Full rule: "Canonical sources & precedence" in `.claude/skills/resume-toolkit/reference/application-protocol.md`.
- **Don't skip the masters gate.** Missing or stale masters go through `generate-master-resumes` (with user confirmation) before step 2.
- **Don't duplicate utility logic.** Each utility owns its piece — JD fetch, signal extraction, master generation, drafting, auditing, rendering, tracking. This skill calls them; it does not reinvent them.
- **`fetch-job-description` for JD URLs.** Prefer it over WebFetch, which paraphrases. LinkedIn uses `linkedin-job-to-markdown`. Manual paste/file still works.
- **The iteration gate is non-negotiable.** Never auto-publish. The user must approve the current draft before step 5.
- **All application artifacts go in the job folder.** Single `Job Applications/<Company>/<Role>/` location for the full record of the application. Masters stay under `Resume Masters/`.
- **The tracker is canonical.** Every status change goes through `update-application-tracker`. Don't edit `index.html` by hand from this skill.
- **Single-step invocations bypass this skill.** A user asking for signals alone, a review alone, master regeneration alone, or a tracker update alone should hit the utility directly.

## Self-check before declaring done

- [ ] JD markdown and signal report both saved to the job folder
- [ ] Masters + manifest existed (or were generated/updated with user confirmation) before the build
- [ ] Tailored HTML saved to the job folder (started from the selected master)
- [ ] Review ran against the full JD (not the signal report) and was surfaced to the user
- [ ] User confirmed sign-off before publishing
- [ ] PDF rendered and Notepad test result reported
- [ ] All application artifacts under `Job Applications/<Company>/<Role>/`
- [ ] Tracker row exists in `Job Applications/index.html` and reflects the current status (`ready-to-submit` after publish; `submitted` once the user confirms they've sent it)
