---
name: generate-master-resumes
description: Create or update the user's maintained master resumes from Work Experience notes and the resume-masters manifest. Trigger when masters are missing, stale, or the user wants to define/regenerate their master set. No JD involved — each master represents a role family, not a posting.
---

# Generate Master Resumes

Create or update the user's maintained **master resumes** — the stable baselines that `build-targeted-resume` copies and tunes per job. Masters are derived from the `Work Experience/` notes and shaped by the user-owned manifest at `Work Experience/resume-masters.md`. No job description is involved: a master represents a role family and a stable professional identity, not a posting.

Layout and CSS always come from the blank template (`.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html`). Masters are filled HTML, kept at the host project root under `Resume Masters/`.

Full contract (manifest format, regeneration triggers, canonical precedence): "Resume masters" and "Canonical sources & precedence" in `.claude/skills/resume-toolkit/reference/application-protocol.md`.

## When to use

- User has no masters yet, or `Work Experience/resume-masters.md` is missing
- User added/changed a role, skill, metric, or identity and wants masters refreshed
- The blank template or formatting guide changed and masters need a layout refresh
- `job-application` or `build-targeted-resume` found masters missing or stale and asked to regenerate

## Inputs

- **Required:** User's experience notes — `Work Experience/` (`work history.md`, `experience - <Company> - <Position>.md`, `skills - technical.md` / `skills - soft.md`, `projects.md`)
- **Required:** Stable personal facts — `Work Experience/personal-details.md`
- **Required (or bootstrap):** Master manifest — `Work Experience/resume-masters.md`. If missing, create it with the user first (see Process step 0).
- **Bundled template:** `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html`
- **Reference:** `.claude/skills/resume-toolkit/reference/formatting-guide.md`
- **Reference:** `.claude/skills/resume-toolkit/reference/application-protocol.md` (resume masters, consulting / concurrent roles, 80/20)

## Process

### 0. Ensure the manifest exists

If `Work Experience/resume-masters.md` is missing, **do not invent a split**. Work with the user to define:

1. How many masters (typically 1–3; more dilutes maintenance)
2. For each: a short **name**, a **purpose** (what role family it targets), a **stable identity headline** (the string that will appear under the name and open the summary), and **role-family / classification cues** (keywords and signals used later to pick the best-fit master for a JD)

Write the manifest in the format specified in "Resume masters" in `application-protocol.md`. Confirm the draft with the user before generating HTML.

Example split (illustrative only — every user's split is different):

- AI / Platform — `Senior Software Engineer | AI Platforms & Distributed Systems`
- Backend — `Senior Software Engineer | Backend & Distributed Systems`

### 1. Decide create vs update

For each entry in the manifest:

- If `Resume Masters/Master Resume - <Name>.html` is missing → create it.
- If it exists → update it in place (regenerate content from canonical notes; keep the same filename). Prefer a full rewrite of the master HTML over patching stale bullets ad hoc — the notes and template are the source of truth, not the previous master file.

When the user asked to regenerate only one master, still check that every other manifest entry has a corresponding file; flag gaps.

### 2. Build each master from canonical sources

For each master:

1. Copy `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` to `Resume Masters/Master Resume - <Name>.html`.
2. Fill from `Work Experience/` notes and `personal-details.md` only — never from a prior tailored resume under `Job Applications/`.
3. Set the `.role-line` and the summary's opening identity to the manifest's **stable identity headline** verbatim. Do not invent a different identity per master beyond what the manifest specifies.
4. Shape emphasis to the master's **purpose**: summary focus, skills ordering, which bullets lead each recent role, which projects surface. Chronology, employers, dates, titles, and grounded claims stay shared and truthful across masters; only emphasis and selection differ.
5. Leave the template's `Relevant Highlights` block **commented out** — that section is filled only during per-JD tailoring by `build-targeted-resume`.
6. Apply the consulting and **concurrent roles** rules from `application-protocol.md`. Overlapping date ranges must be unambiguous (e.g. part-time consulting alongside a full-time role) — label and clarify on the resume without adding consent/background-check detail.
7. Apply formatting-guide rules (audience tone, metrics as numerals, AI-sounding patterns, length). Target two pages for senior candidates; write for concision up front.

No JD, no signal report, no title mirroring. Masters deliberately omit per-posting keyword swaps.

### 3. Lint and self-check

For each generated/updated master, run:

```
python .claude/skills/resume-toolkit/scripts/lint_resume.py "Resume Masters/Master Resume - <Name>.html"
```

Resolve lint findings before returning. Then complete the self-check below.

### 4. Report back

Tell the user which masters were created or updated, the paths, the identity headlines, and any gaps found in the notes (missing metrics, unclear concurrent-role presentation, skills without role attribution). Do not render PDFs here — that is `publish-resume`'s job if the user wants downloadable masters later.

## Output

```
Work Experience/resume-masters.md          # manifest (created or left as-is)
Resume Masters/
  Master Resume - <Name>.html              # one file per manifest entry
```

## Rules and constraints

- **No JD.** Masters are role-family baselines, not tailored applications.
- **Never invent skills, projects, or metrics.** Flag gaps; leave them out of the master.
- **Identity comes from the manifest.** The headline and summary opener match the entry's stable identity string exactly.
- **Blank template owns layout.** Do not invent alternate CSS or section order in a master.
- **Propagate via notes + regenerate.** If a bullet or claim is wrong, fix the `Work Experience/` note (or the template), then regenerate the master — do not treat a master as an editable source of truth for experience content.
- **Concurrent roles must be clear.** Apply the concurrent-roles rule in `application-protocol.md` whenever dates overlap.
- **Apply AI-sounding pattern rules** from `formatting-guide.md`.

## Self-check before returning

- [ ] `Work Experience/resume-masters.md` exists and every entry has name, purpose, identity headline, and role-family cues
- [ ] Every manifest entry has a matching `Resume Masters/Master Resume - <Name>.html`
- [ ] Each master's `.role-line` and summary opener match that entry's identity headline verbatim
- [ ] Relevant Highlights block remains commented out (filled only during per-JD tailoring)
- [ ] No placeholder tokens (`[FULL NAME]`, etc.) remain from the template
- [ ] Dates use one consistent `Mon YYYY` style across every role
- [ ] Overlapping roles carry a part-time / consulting clarifier per `application-protocol.md`
- [ ] `lint_resume.py` reports zero findings (or only dismissed false positives, noted to the user)
- [ ] Content is grounded in `Work Experience/` notes — nothing invented
