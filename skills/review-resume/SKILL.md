---
name: review-resume
description: Evaluate a resume against a job description, score it across coverage/content quality/conciseness/formatting, and produce a prioritized list of specific fixes. Trigger when the user asks to review, audit, critique, or score a resume against a specific job — or to sanity-check a resume before submitting. Reviews against the full job description when available (falling back to a signal report or a generic industry check). Takes a resume plus the target job description.
---

# Review Resume

Audit a resume against a specific job and return a prioritized critique with line-level fixes.

## When to use

- User shares a resume and a job description and asks for feedback
- User wants a pre-submission check
- User wants to compare two resume drafts for the same role
- User wants the current draft of a tailored resume audited before continuing

## Inputs

- **Required:** The resume. Prefer the file path on disk (`.html` or `.md`) so the linter can run on it. Raw paste or DOCX content also works, but skips the deterministic lint step.
- **Required:** The target job description. Best as the **full JD** (a Markdown file on disk). If it isn't available, see "Establish the review target" below for the fallback order (link → pasted text → signal report → generic). The full JD is strongly preferred — see the rationale there.
- **Bundled linter:** `.claude/skills/resume-toolkit/scripts/lint_resume.py` — deterministic regex checks for AI-sounding patterns from the formatting guide, plus length checks
- **Reference:** `.claude/skills/resume-toolkit/reference/formatting-guide.md`
- **Reference:** `.claude/skills/resume-toolkit/reference/industry-signals.md`

**Judge against canonical sources, not prior tailored artifacts.** Formatting is correct when it matches the blank template (`.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html`) and `formatting-guide.md`; the stable baseline is the selected master under `Resume Masters/` (per `Work Experience/resume-masters.md`); content claims are correct when supported by the `Work Experience/` notes. Divergence from the master baseline (identity headline, chronology, grounded claims) needs justification in the review. Never frame a fix as "make it match a previous tailored resume" — prior resumes under `Job Applications/` are presumed stale (old layout, retired phrasing, outdated bullets, missing roles, and historically JD titles copied into the identity), so conforming toward one reintroduces the drift the build deliberately avoided. If the draft diverges from an older tailored resume, that is usually correct, not a defect. See "Canonical sources & precedence" in `.claude/skills/resume-toolkit/reference/application-protocol.md`.

## Process

Work top-down: the early steps surface the changes that need *your judgment* and can cascade into large rewrites; the deterministic linter runs last, once, after the content has settled. Running it earlier wastes effort — coverage and quality fixes routinely rewrite half the bullets, which would invalidate an early lint pass and force a re-run.

### Establish the review target

Review against the **full job description** whenever possible. The signal report (`extract-job-signals` output) is a deliberately lossy simplification produced *before* the resume was built; reviewing against it only re-checks the same reduced spec the resume was built from, so anything the signal extraction dropped or distorted stays invisible. The final review is the independent check against ground truth, so it should target the JD itself.

Pick the best available target, in order:

1. **Full JD as a Markdown file on disk** — use it directly. Best case (the job-application folder often already has one).
2. **No JD file?** Ask the user to provide one of these, best first:
   - **A link to the posting (recommended).** Convert it to Markdown before reviewing: a LinkedIn URL goes through the `linkedin-job-to-markdown` skill; any other URL, fetch with WebFetch. Review against the result.
   - **The JD text/Markdown pasted directly.**
   - **The extracted signal report.** Usable, but call out in the review that it's a simplification, so any requirement it dropped is something you could not verify.
   - **None of the above** → run a **generic review** against `.claude/skills/resume-toolkit/reference/industry-signals.md` only. State plainly that this checks industry-standard expectations for the role family, not this specific posting.

Note which target you used at the top of the review so the user knows the basis.

### Checklist severities

Each finding gets a severity tag:

- **Critical** — Parser failure or coverage gap that will make the resume "invisible" to recruiter search
- **Material** — Will not break the application but weakens the candidate's position
- **Minor** — Polish, would improve quality but isn't load-bearing

### Step 1 — Coverage (highest-leverage; resolve before polishing)

Coverage gaps are the most involved fixes — some are real candidate gaps that can't be edited away and may even change whether the user should apply at all — so settle what's in, out, or intentionally omitted before investing in prose. Derive the requirements from your review target: read the **JD directly** and identify the title, must-have skills/qualifications, preferred/nice-to-haves, implicit expectations, and required years; if you only have the signal report, use its structured fields (`Target Title`, `Role Family`, `Required Skills`, `Nice-to-Have Keywords`, `Action-Skill Pairs`, `Implicit Industry Expectations`) but treat them as lossy; if generic, judge against industry norms in `industry-signals.md`. When `Work Experience/resume-masters.md` and the matching master HTML are available, use them as the expected identity and chronology baseline.

- [ ] **Stable identity.** Does the `.role-line` / summary opener use a stable professional identity from the selected master (or `resume-masters.md`), **not** a verbatim copy of the JD's target title? → Critical if the JD title was pasted in as the candidate's identity (the exact failure mode that reads as mechanical / AI-tailored). When the manifest is available, the identity should match the chosen master's headline.
- [ ] **Target-title terminology.** Where the JD's `Target Title` / required phrasing maps accurately to real experience, does related terminology appear in skills or bullets (without changing the identity headline)? → Material if truthful mappings are missing; do **not** suggest rewriting the identity to match the JD title.
- [ ] **Required / must-have skills.** For each must-have skill or qualification in the JD, does it appear somewhere in the resume (Skills section or experience bullets)? → Critical for each missing one the user actually has. Reading the full JD here is the whole point: catch must-haves the signal report may have dropped or softened.
- [ ] **Preferred / nice-to-have.** For each preferred or nice-to-have item, does it appear? → Material per missing item.
- [ ] **Responsibility-to-bullet alignment.** For the JD's core responsibilities (or the signal report's `Action-Skill Pairs`), is there a recent-role bullet pairing the action with the skill, ideally with a metric? → Material per gap.
- [ ] **Implicit industry expectations.** Do the table-stakes expectations for this role family appear at least once? → Material per missing item.
- [ ] **YOE alignment (overall).** Does the resume make the required total years of experience easily computable from non-overlapping date ranges in a consistent date format? → Critical if the math doesn't add up, dates are missing/vague, or date styles are mixed across roles (mixed formats make the parser's duration math fail silently).
- [ ] **Per-skill minimum YOE.** For each minimum in the JD or the signal report's `Minimum Years of Experience` (e.g., "5+ years Python", "3+ years Kubernetes"), trace where that keyword appears in the **dated work-experience entries** and sum those roles' durations. ATS credit skill-specific experience only from dated roles where the keyword appears — a skill present only in the Skills section counts as **zero** years. → Critical for each required minimum the user can actually meet but whose keyword is missing from enough dated roles to sum to the minimum (e.g., the skill sits only in the Skills section, or only in too-recent roles). The fix is to back-port the genuinely-used keyword into the bullets of enough older roles to clear the math. If the user genuinely lacks the tenure, that's a candidate gap → `Gaps to Address`, not a resume fix.
- [ ] **Tenure-stack overclaim.** If the summary opens with a tenure claim attached to a specific stack or specialty (e.g., "over a decade building production Python and Java backend services", "10+ years of distributed systems work", "8 years of ML engineering"), do the work-history dates support that tenure *for that stack/specialty*, not just for the candidate's total career? Walk the role dates and add up where the named stack was actually primary. → Critical if the tenure claim and the role math diverge by more than ~1 year. The fix is almost always to decouple total career length from the specific stack: either broaden the stack list to cover the full tenure ("Python, Java, and C++"), or split the claim ("decade of software engineering experience and 4+ years of Python backend services"). Never narrow the tenure or invent stack history to close the gap.
- [ ] **Concurrent-role clarity.** If any two roles have overlapping date ranges, is the secondary engagement labeled as part-time / consulting (or otherwise clarified) so a human reader does not assume two simultaneous full-time jobs? → Material when overlap is present without a clarifier. See "Concurrent roles" in `application-protocol.md`.

Coverage gaps the user *doesn't* have go in `Gaps to Address`, not the fix list — surface them here, early, so the user can decide whether to apply, learn the skill, update their experience notes, or reposition before you spend effort on line edits.

### Step 2 — Content and bullet quality (human judgment)

With coverage settled, check that what's included is well-represented. **Skip anything the linter catches** (AI-sounding patterns, fluff words, outdated tech, em-dashes, semicolons, repeated acronym expansions, JD phrase echoes when `--jd` is passed — those are Step 4). Focus here on what regex can't judge:

- [ ] **Invented or unsupported claims.** Any metric, skill, scope, or outcome not backed by the user's input? → Critical. This is the most important manual check; the linter cannot do it.
- [ ] **Ungrounded exact-match skill.** Any Skills-section term that appears only because the JD asked for it, with no support in `Work Experience/` notes (or the master)? Adjacency is not grounding — related experience does not license inventing the JD's exact term. → Critical per ungrounded term.
- [ ] **JD phrase echo.** Do bullets or the summary copy multiple distinctive multi-word phrases or sentence structures from the JD (or from the signal report's `Distinctive JD Phrases` denylist)? Exact terms belong in Skills when grounded; bullets should match concepts with conventional terminology. → Material; escalate to Critical if pervasive enough that the resume looks mechanically reconstructed from the posting.
- [ ] **Missing terminology bridge.** Does the resume use an internal/canonical term for a JD-required concept without connecting it to the accurate industry/JD equivalent? Reviewers should not have to infer the mapping. → Material per missing bridge.
- [ ] **Over-rewriting drift.** Were canonical master bullets semantically rewritten where selecting or reordering existing bullets would have covered the requirement? Tailoring should prefer selection/ordering over rewriting accomplishments. → Material when drift is unnecessary.
- [ ] **Weak or awkward bullets.** Bullets missing the `verb + skill/context + quantified outcome` shape, vague ("Worked on the inference pipeline"), or clumsily phrased. → Material per weak bullet.
- [ ] **Overly broad terms where specifics are expected** ("Machine Learning" instead of "RAG"/"LoRA fine-tuning", "Cloud" instead of "AWS Bedrock"/"EKS"). → Material.
- [ ] **Consulting formatted per `.claude/skills/resume-toolkit/reference/application-protocol.md`.** → Material if consulting is present and mishandled.
- [ ] **Roles older than 10 years condensed** (no bullet detail). → Minor.

### Step 3 — Conciseness pass

More concise is almost always better — provided every ATS keyword survives. Re-read the experience bullets looking specifically for ways to tighten without losing meaning:

- Cut filler, hedges, and context the reader can infer; collapse two-line bullets toward a single line.
- **Preserve every JD/required keyword and every metric.** Concision must never undo the coverage established in Step 1 — if tightening would drop a keyword, keep the keyword and trim elsewhere.
- Favor cutting words over shrinking the resume's CSS (CSS tightening is `publish-resume`'s last resort, not a substitute for concise writing).

Surface the highest-impact tightenings as before/after edits.

### Step 4 — Linter and formatting check

Content has settled, so run the deterministic checks once.

If the resume is a file on disk (`.html` or `.md`), run the bundled linter. When reviewing against a JD file, pass it so the linter can flag shared long phrases:

```
python .claude/skills/resume-toolkit/scripts/lint_resume.py "<path-to-resume>" --jd "<path-to-jd.md>"
```

Without a JD file (generic review, paste-only JD, etc.), omit `--jd`:

```
python .claude/skills/resume-toolkit/scripts/lint_resume.py "<path-to-resume>"
```

It encodes the patterns from the "AI-sounding patterns to avoid" and "Words to avoid" sections of `.claude/skills/resume-toolkit/reference/formatting-guide.md` (em-dashes, "leveraged"/"utilized", grandiose adjectives, fast-paced-landscape framings, antithesis cadence, tricolons, symmetrical adjective stacks, puffery on known entities, fluff words, excessive colons, semicolons, outdated tech, repeated acronym expansions, and — with `--jd` — JD phrase echoes) plus length checks (over-long summary, over-long bullets). Each finding has a rule name, severity, line number, the matched substring, why it's flagged, and a concrete fix. Fold them in by severity:

- Every linter `critical` → Critical Issues; every `material` → Material Issues; every `minor` → Minor Issues.
- Dismiss only obvious false positives (e.g., the word "robust" survived HTML-stripping from a CSS class name), and note any you dismiss so the user knows you read them.
- Don't relax a rule because it matched once. One em-dash is still critical.

If the resume isn't a file on disk (raw paste, DOCX), do this pass manually against the "AI-sounding patterns to avoid" and "Words to avoid" sections of `.claude/skills/resume-toolkit/reference/formatting-guide.md`.

Then walk the formatting checklist (`formatting-guide.md`):

- [ ] Single-column layout (no multi-column) → Critical
- [ ] Standard section headers (Experience, Skills, Education) → Critical
- [ ] Dates in MM/YYYY or "Month YYYY" — no "Summer 2022" or "'21-'23" → Critical
- [ ] Contact info in body text, not document header space → Critical
- [ ] No text boxes, tables, progress bars, icons replacing words → Critical
- [ ] Standard fonts (Arial, Calibri, Times New Roman) → Material (only if known)
- [ ] Section order: Header → Summary → Skills → Experience → Education → Certs → Material if reordered
- [ ] Length: two pages for senior; one page for <3 years → Material
- [ ] Acronyms dual-formatted once somewhere (expanded + acronym, usually in Skills); no repeated expansions of the same acronym → Minor

## Output format

```markdown
# Resume Review: <Resume Owner> for <Job Title> at <Company>

## Summary
- Review basis: <full JD | signal report (lossy) | generic (industry-signals only)>
- Coverage score: <X> of <Y> required skills present
- Minimum-YOE coverage: <X> of <Y> required per-skill minimums backed by dated roles (note any backed only via the Skills section)
- Critical issues: <count>
- Material issues: <count>
- Minor issues: <count>
- Overall verdict: <one sentence>

## Critical Issues
For each: brief description, the specific location in the resume (section/line), and a concrete fix.

## Material Issues
Same structure.

## Minor Issues
Same structure.

## Suggested Edits
Concrete before/after rewrites for the highest-leverage bullets, summary, or skills entries. Aim for the top 5-8 highest-impact changes, not exhaustive.

## Gaps to Address (Not Resume Fixes)
Skills the JD requires that the user doesn't appear to have. These can't be fixed by editing the resume — flag them for the user to decide whether to apply at all, learn the skill, or reposition.
```

## Rules and constraints

- **Prioritize ruthlessly.** A 30-finding list is useless. Surface the 5-10 highest-leverage changes, then the rest in compact form.
- **Be specific.** "Bullet 3 of most recent role lacks a metric — currently 'Worked on inference pipeline.' Suggested: 'Reduced inference p95 latency by 40% on a 50M-query/day RAG pipeline.'"
- **Don't invent gaps.** If the resume doesn't list a skill and you can't tell whether the user has it, ask — don't assume absence means lacking.
- **Never silently rewrite.** Always present changes as suggested edits so the user can accept/reject. Don't produce a "fixed resume" — that's the Build skill's job.
- **Distinguish resume problems from candidate problems.** A skill the user doesn't have is not a resume bug. Surface it in the `Gaps to Address` section so the user can decide whether to apply.
