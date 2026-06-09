---
name: job-application
description: Orchestrate the end-to-end resume tailoring workflow for a specific job. Parses the JD, drafts a tailored resume, audits it, iterates with the user, and publishes the final PDF. Trigger when the user wants to apply for a specific posting, tailor a resume for a job, or run the full resume flow end-to-end. Composes extract-job-signals, build-targeted-resume, review-resume, publish-resume, and update-application-tracker.
---

# Job Application

Orchestrate the full resume tailoring workflow for a specific job. This skill is glue: it sequences four utility skills, keeps the application tracker in sync via a fifth, and gates the whole thing on user review. It does not duplicate their logic — for each step, invoke the utility.

## When to use

- User shares a job description (URL, pasted text, file) and wants to apply
- User says things like "tailor my resume for this role", "let's apply to X", "run the full flow for this posting"
- User wants the whole sequence run, not just one step

If the user explicitly asks for a single step ("just extract signals", "just review this resume against the JD"), invoke that utility skill directly. This skill is for the full workflow only.

## Inputs

- **Required:** Job description (URL, pasted text, or file path)
- **Required:** Path to the user's experience notes (the `Work Experience/` directory)
- **Required:** Stable personal facts (`Work Experience/personal-details.md` — contact info and education). The downstream resume build reads this for the header and Education section, so these never need to be pulled from an old resume (see "Canonical sources" below).
- **Required (or inferable):** Company name and role title, used for the output folder name

## Workflow

Run the steps in order. Each step delegates to a utility skill; stay inside the utility's contract rather than re-implementing the work here. Between steps, keep the tracker (`Job Applications/index.html`) in sync via `update-application-tracker` — see the "Tracker maintenance" section below.

### 0. Ensure the tracker has a row
Before doing any work, invoke `update-application-tracker` to confirm a row exists for this posting. If not, add one as `not-started` with whatever metadata is available (company, title, location, salary, posted date, JD URL). The tracker is the canonical record; everything downstream assumes the row exists.

### 1. Extract signals
Invoke `extract-job-signals` on the JD. Save the resulting signal report into the job-application folder as `Signal Report - <Company> - <Role>.md`. Also save the JD itself to the folder as `JD - <Company> - <Role>.md` — convert a URL to Markdown first (LinkedIn via `linkedin-job-to-markdown`, any other URL via WebFetch) — so the audit step can review against the full description, not just the lossy signal report. Then bump tracker status to `drafting`.

### 2. Build the tailored resume
Invoke `build-targeted-resume`, passing the JD, the signal report, the user's experience notes (`Work Experience/`), and the stable personal facts (`Work Experience/personal-details.md`, for contact info and education). The utility produces a styled HTML file at `Resume - <Company> - <Role>.html` in the same folder.

### 3. Audit the draft
Invoke `review-resume` on the generated HTML against the **full JD** (`JD - <Company> - <Role>.md` from step 1) — not the signal report. The signal report was the input that built the resume, so auditing against it would only re-check the same reduced spec; the review must hit ground truth to catch anything the signal extraction dropped. (If the JD markdown somehow isn't available, fall back per `review-resume`'s own target order.) Surface the prioritized critique (Critical / Material / Minor) to the user. Do not silently apply the suggested fixes — that's the iteration step's job.

### 4. Iterate with the user
This is the human-review gate.

- Present the review findings and ask which fixes to apply
- For each batch of accepted changes, re-invoke `build-targeted-resume` (full HTML output, not a diff) with the additional instructions
- Optionally re-run `review-resume` after a substantive edit pass
- Continue until the user explicitly signs off on the current draft

Do not advance to step 5 without explicit user approval, even if the review reports zero critical issues.

### 5. Publish
Invoke `publish-resume` on the approved HTML. The utility renders the PDF, verifies page count, and runs the Notepad parseability check. Report the PDF path and parseability result back to the user. Then bump tracker status to `ready-to-submit` and record `resumeHtml` + `resumePdf` filenames on the row.

### 6. Hand off to the user
Tell the user the resume is ready and the next move is theirs: review the PDF one last time, submit the application, and report back. When they confirm submission, run `update-application-tracker` to flip status to `submitted` and capture the `dateSubmitted` they give you.

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

- **Build from canonical sources, never from a previous resume.** Formatting/layout comes from `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` (+ `.claude/skills/resume-toolkit/reference/formatting-guide.md`); experience content comes from the `Work Experience/` notes; personal facts come from `Work Experience/personal-details.md`. Previous resumes and artifacts under `Job Applications/<Company>/<Role>/` are **presumed stale** — consult them only as a last resort when a canonical source is genuinely missing something, verify against canonical, and prefer back-filling the canonical source over copying the artifact forward. This is what lets the user change layout or experience **once** and have every future resume reflect it. Full rule: "Canonical sources & precedence" in `.claude/skills/resume-toolkit/reference/application-protocol.md`.
- **Don't duplicate utility logic.** Each utility owns its piece — signal extraction, drafting, auditing, rendering, tracking. This skill calls them; it does not reinvent them.
- **The iteration gate is non-negotiable.** Never auto-publish. The user must approve the current draft before step 5.
- **All artifacts go in the job folder.** Single `Job Applications/<Company>/<Role>/` location for the full record of the application.
- **The tracker is canonical.** Every status change goes through `update-application-tracker`. Don't edit `index.html` by hand from this skill.
- **Single-step invocations bypass this skill.** A user asking for signals alone, a review alone, or a tracker update alone should hit the utility directly.

## Self-check before declaring done

- [ ] JD markdown and signal report both saved to the job folder
- [ ] Tailored HTML saved to the job folder
- [ ] Review ran against the full JD (not the signal report) and was surfaced to the user
- [ ] User confirmed sign-off before publishing
- [ ] PDF rendered and Notepad test result reported
- [ ] All artifacts under `Job Applications/<Company>/<Role>/`
- [ ] Tracker row exists in `Job Applications/index.html` and reflects the current status (`ready-to-submit` after publish; `submitted` once the user confirms they've sent it)
