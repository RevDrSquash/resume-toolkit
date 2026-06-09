---
name: update-application-tracker
description: Read or update the job-applications tracker dashboard at Job Applications/index.html. Trigger when adding a new posting to the tracker, changing a job's status (drafting, ready-to-submit, submitted, interview, offer, rejected, closed), recording a submission date, filling in missing metadata (salary, location, posted date), or looking up the current state of an application. Operates on the inline JSON block inside index.html — the source-of-truth tracker after the CSV was retired.
---

# Update Application Tracker

The dashboard at `Job Applications/index.html` is the authoritative tracker for
every posting. It is a static HTML file with an inline JSON block that the page
renders into a table and a 30-day submissions chart. All edits happen on that
JSON block. There is no CSV — it was retired.

## When to use

- Adding a new posting after its folder is created under `Job Applications/<Company>/<Role>/`
- Updating a job's status as it moves through the pipeline (e.g. resume built, application submitted, interview scheduled, rejection received)
- Recording a submission date when the user confirms they submitted an application
- Filling in missing metadata the user provides later (salary, location, posted date)
- Marking a posting `closed` when the user decides to skip it
- Reading current state — answering "what jobs are in `submitted`?", "what did I submit this week?", "is the Acme resume done yet?"

## Inputs

- **Required:** `Job Applications/index.html`
- **For new entries:** The job folder (slug = `<Company>/<Role>` under `Job Applications/`) should already exist on disk
- **Schema source of truth:** The HOW-THIS-PAGE-WORKS comment block at the top of `index.html`. Read it before any non-trivial edit.

## The data model

All data lives in `<script type="application/json" id="job-data">` near the
bottom of `index.html`. Each posting is one object in the `jobs` array. The
schema (copied here for quick reference, but the comment in `index.html` wins
in case of drift):

```json
{
  "slug":          "<Company>/<Role folder>",
  "company":       "<Company display name>",
  "title":         "<Full job title>" | null,
  "location":      "<City, Region, Country (Mode)>" | null,
  "salaryMin":     <number> | null,
  "salaryMax":     <number> | null,
  "currency":      "USD" | "CAD" | "",
  "datePosted":    "YYYY-MM-DD" | null,
  "dateSubmitted": "YYYY-MM-DD" | null,
  "status":        "not-started" | "drafting" | "ready-to-submit" | "submitted" | "interview" | "offer" | "rejected" | "closed",
  "jdUrl":         "<URL>" | null,
  "jdFile":        "<filename inside slug folder>" | null,
  "resumeHtml":    "<filename inside slug folder>" | null,
  "resumePdf":     "<filename inside slug folder>" | null,
  "notes":         "<short free text>"
}
```

## Process

### 1. Read the comment block
Open `index.html` and read the HOW-THIS-PAGE-WORKS comment in the `<head>`. It owns the schema and the status rules. The page won't load if the JSON is malformed, so confirm structure before editing.

### 2. Locate the row
For an existing posting, find the entry by matching `slug` exactly. For a new posting, append a new object to the end of the `jobs` array — the render script sorts by status priority and date, so insert order has no visual effect.

### 3. Edit the fields
- Use `null` for unknown values, not empty strings (except `currency` and `notes`, which use `""`).
- Preserve the field order from the schema so the file stays diffable.
- Don't reorder rows manually — sorting is the render script's job.
- Don't touch the HTML markup, CSS, or render JavaScript. This skill is JSON-only.

### 4. Update related fields together
When changing `status`, set the dependent fields in the same edit:

| New status         | Also set                                              |
|--------------------|-------------------------------------------------------|
| `drafting`         | (nothing required)                                    |
| `ready-to-submit`  | `resumeHtml` and `resumePdf` (filenames in slug folder) |
| `submitted`        | `dateSubmitted` to the YYYY-MM-DD the user confirms   |
| `interview`        | `notes` may capture the stage (phone screen, on-site, take-home) |
| `offer`            | `notes` may capture the offer details                 |
| `rejected`         | `notes` may capture the rejection reason / date       |
| `closed`           | `notes` must capture the reason (withdrew, qualifications gap, predates pipeline) |

### 5. Confirm validity
The render script silently swallows malformed entries into an error message, so the page should still load after your edit. If the user can see the table on refresh, the JSON parsed.

## Status semantics and transitions

| Status            | Meaning                                                                 |
|-------------------|-------------------------------------------------------------------------|
| `not-started`     | Folder exists, JD is saved, no resume work yet.                         |
| `drafting`        | Signal report extracted, resume in progress, not yet built.             |
| `ready-to-submit` | Resume HTML + PDF built and reviewed, but not yet sent.                 |
| `submitted`       | Application sent; awaiting recruiter response. Requires `dateSubmitted`.|
| `interview`       | Phone screen / on-site / take-home scheduled or in flight.              |
| `offer`           | Offer extended; under negotiation or accepted.                          |
| `rejected`        | Application closed by employer (rejected / position filled).            |
| `closed`          | User withdrew, skipped, or the row predates the pipeline.               |

Rules of thumb for inferring a new status from the user's message:

- "I built the resume" / "ready" → `ready-to-submit`
- "I submitted" / "I applied to X" → `submitted` (ask for the date if not given)
- "Got a phone screen" / "they scheduled an interview" → `interview`
- "Got an offer" → `offer`
- "Got rejected" / "ghosted" / "they closed the role" → `rejected`
- "Skip this one" / "not interested" / "I don't qualify" → `closed`

## Rules and constraints

- **Never invent metadata.** Posted date, salary, location come from the JD or the user. If unknown, use `null`.
- **Never advance status without confirmation.** Don't flip `ready-to-submit` → `submitted` just because the user is discussing the role. Wait for explicit confirmation, and capture the date they give you.
- **`dateSubmitted` is mandatory when `status` = `submitted`.** Without it the row drops out of the 30-day chart. Ask the user for the date if they don't volunteer it.
- **The CSV is retired.** `job-applications.csv` no longer exists. The HTML is the only tracker.
- **Pre-pipeline entries stay `closed`.** Some early entries predate the pipeline and carry minimal metadata by design — don't try to backfill them.
- **Don't edit the markup, styles, or render script.** Anything beyond the JSON block is out of scope for this skill. Structural changes (new column, new status) are a deliberate, larger edit handled separately.

## Self-check

- [ ] JSON is still valid (no trailing commas, all keys quoted, all strings closed)
- [ ] The new/modified row has every schema field (use `null` for unknown)
- [ ] Status reflects the user's most recent confirmed signal
- [ ] If status is `submitted`, `dateSubmitted` is set
- [ ] If status is `closed`, `notes` captures the reason
- [ ] Did not touch HTML markup, CSS, or the render `<script>` block
