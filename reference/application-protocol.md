# Application Protocol

How to actually submit applications — channel choice, knockout questions, experience-notes hygiene, resume masters, and consulting representation. Used by `generate-master-resumes` and `build-targeted-resume` (for masters, consulting formatting, and concurrent roles), `job-application` (for channel choice and knockout questions when assembling an application), and as a standalone reference when deciding how to apply.

## Channel choice

**Prefer direct application via the company's career page over LinkedIn Easy Apply.**

- Easy Apply routes the application through LinkedIn's proprietary parser, which strips technical nuance (e.g., "Tableau dashboards" → "Tableau"), often reformats dates by dropping months (breaking tenure calculations), and maps niche skills to generic taxonomies before transmitting to the destination ATS.
- Combined with the much higher applicant volume Easy Apply attracts, callback rates are consistently lower than direct submissions.
- Multiple independent sources confirm the directional gap; the specific magnitude varies, but every credible source agrees that direct beats Easy Apply.

**Practical rule:** For any role you actually want, apply through the company's own career portal. Reserve Easy Apply for low-priority/exploratory applications and as a way to track what you've applied to in LinkedIn's UI.

**Job board aggregators (Indeed, Glassdoor, etc.):** Same logic. If the listing has an "apply on company site" option, take it. Avoid the in-aggregator apply flow when possible.

## Knockout questions

Knockout questions are the yes/no form fields on the application — these, not the resume, are what cause immediate auto-rejection. A wrong answer here will archive your application before the resume is parsed.

Common knockouts:

- **Visa / sponsorship requirement** ("Do you require sponsorship now or in the future?")
- **Work authorization** ("Are you authorized to work in [country] without sponsorship?")
- **Location / on-site** ("Are you willing to work on-site in [city]?", "Are you willing to relocate?")
- **Years of experience** ("Do you have 5+ years of [specific skill]?")
- **Degree** ("Do you hold a Bachelor's degree or equivalent?")
- **Security clearance** ("Do you have or can you obtain a [clearance level]?")
- **On-call willingness** ("Are you willing to participate in on-call rotations?")
- **Compensation expectations** (often used as a soft knockout)

### How to answer YOE questions

ATS systems will verify YOE form answers against parsed date ranges from your resume. The system sums non-overlapping date ranges to calculate aggregate experience.

- **Work from the signal report's `Minimum Years of Experience` section.** That section (produced by `extract-job-signals`) itemizes every minimum the posting asks for — overall and per skill. The form's knockout questions are usually the same minimums restated as yes/no fields, so answer them from that list and make sure each answer is consistent with what the resume's dated bullets actually support.
- **Aggregate, don't subtract.** If the question asks "How many years of [Python / cloud / engineering]?" — count every role where you used the skill substantively, even partially. A senior engineer with 12 total years and Python use in most roles has "12 years Python", not "3 years Python because I was titled differently."
- **Round honestly down to the nearest year**, but round at the upper bound: 4 years and 11 months = 4 years.
- **Make the math add up — and keep the form, the resume, and the parser in agreement.** If you claim 12 years on the form, your resume's date ranges must sum to at least 12 years of non-overlapping employment. For a *per-skill* answer ("5+ years Python"), the keyword must also appear in dated roles summing to that figure — the same skill-duration math `build-targeted-resume` applies and `review-resume` checks. If the form answer, the resume bullets, and the parser's sum disagree, the application flags as inconsistent.

### How to handle salary / compensation questions

- If a number is required: use a range, anchored at or slightly above your true target. Single numbers create unnecessary leverage problems.
- "Negotiable" is usually rejected by the form — provide a range.
- If the question is optional, leave it blank and discuss with the recruiter.

## Canonical sources & precedence

Every targeted resume is assembled from **canonical sources**, never from a previous *tailored* resume. The layers:

1. **Formatting & layout** comes from `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` (the fill-in skeleton — section order, CSS, accent colors, date format) and the rules in `.claude/skills/resume-toolkit/reference/formatting-guide.md`. The blank template is the sole layout source; masters are built by copying it.
2. **Experience content** (ground truth) comes from the **`Work Experience/` notes** — `work history.md` (dates/titles), `experience - <Company> - <Position>.md` (scope, accomplishments, draft bullets), `skills - technical.md` / `skills - soft.md` (skill catalogue + role attribution), and `projects.md`. See "Experience notes hygiene" below.
3. **Personal facts** (name, location, phone, email, LinkedIn, education) come from `Work Experience/personal-details.md`.
4. **Maintained masters** under `Resume Masters/` (declared in `Work Experience/resume-masters.md`) are the **derived baseline** that each tailored resume starts from. They are not a second source of experience facts — they are a maintained rendering of (1)+(2)+(3) shaped for a role family. See "Resume masters" below.

**Precedence / fallback rule.** Previous *tailored* resumes and cover letters — anything under `Job Applications/<Company>/<Role>/` — are **not canonical**. They are point-in-time snapshots and are presumed **stale**. Do not pattern-match a new resume off a prior tailored artifact for either layout or content. The selected master **is** the sanctioned starting point for a new application. Consult a prior tailored artifact only as a **last resort**, when a canonical source genuinely lacks something you need; when you do, verify it against the notes / personal-details / template, and prefer **back-filling the canonical source** (the notes or the template, then regenerating masters) over copying the tailored artifact forward.

**Why this matters.** Canonical notes and the template are edited **once** and propagate by regenerating masters — then every future tailored resume starts from the refreshed baseline. A prior tailored artifact does the opposite: anchoring on it silently inherits its drift (retired accent colors and phrasing, outdated section ordering, stale bullets, roles that have since been added or changed, and historically JD titles copied into the identity), reproducing an old state instead of the intended current one.

**How edits propagate.** Fix the `Work Experience/` note or the blank template, then run `generate-master-resumes`. Do not treat a master HTML file as an ad-hoc editable source of truth for experience content, and do not permanently fork experience only inside one job folder.

## Experience notes hygiene

The source of truth for experience *facts* is the **`Work Experience/` notes** (per "Canonical sources & precedence" above), not a prior tailored resume. Maintained masters under `Resume Masters/` are derived from these notes; they are the starting point for tailoring, not a replacement for the evidence database. That directory holds:

- **`work history.md`** — the authoritative record of employers, titles, locations, and dates. Resume date ranges come from here.
- **`experience - <Company> - <Position>.md`** — one file per role: scope, responsibilities, accomplishments, and draft bullets.
- **`skills - technical.md` / `skills - soft.md`** — the skill catalogue (see the skill-to-role mapping note below).
- **`projects.md`** — side projects and open-source work not tied to an employer.
- **`personal-details.md`** — contact info and education.
- **`resume-masters.md`** — the user-owned manifest declaring each master (see "Resume masters" below).

Keep these healthy:

- **Capture everything, trim nothing.** Every project, technology, metric, role, and quantified outcome belongs in the notes even if no single resume uses it all. These files are for you, not for submission.
- **Update cadence:** every time you finish something worth mentioning, or quarterly at minimum. The hardest part of tailoring is reconstructing forgotten metrics — capture them while fresh.

### Record which skills map to which roles

`skills - technical.md` catalogues each technology with the roles (and, where known, the duration) it was used in — e.g., "C++ — ACD Systems (7 years), MDA Space". Maintain that role attribution deliberately, because two parts of the tailoring process depend on it:

- **Truthful back-porting for YOE minimums.** When a JD sets a hard per-skill minimum ("5+ years C++"), `build-targeted-resume` weaves that keyword into the bullets of older dated roles so the parser's duration sum clears the bar. It may only do this for roles where the skill was genuinely used — the per-role mapping is what tells it which roles those are. Without it, the builder has to stop and ask.
- **Bullet optimization.** When a nice-to-have skill was used in several roles, the mapping lets the builder place it once — in whichever role has the fewest other bullets or the weakest coverage — instead of redundantly across all of them, keeping each role's bullets dense and distinct.

When a skill's role attribution or rough duration is missing from the notes, fill it in rather than guessing at draft time.

### The 80/20 targeting rule

Each targeted resume is ~80% stable core and ~20% swappable per application. **The 80% baseline is literally the selected master resume** (see "Resume masters").

- **80% baseline (the master):** Header, education, certifications, foundational skills, recent roles' core bullets, employment chronology, grounded claims, canonical accomplishment wording, and the **stable professional identity** for that role family.
- **20% swappable per JD:** Summary emphasis after the identity opener; **Relevant Highlights** (2–3 compressed JD-fit accomplishments selected from the master); skills ordering and exact JD phrasing in the Skills section (grounded terms only); bullet *selection* and *ordering*; project choice; conventional terminology and explicit bridges in bullets where the JD's concepts map to real experience. Minimize unnecessary semantic rewrites of canonical accomplishments.

Swap zones, ordered by leverage:

1. The professional summary's emphasis sentences (keep the stable identity opener; do **not** paste the JD's target title into the identity)
2. Relevant Highlights — 2–3 compressed accomplishments from the master that most directly prove fit (employer/project + measurable outcome; fuller non-verbatim counterpart stays in chronology)
3. The Skills section's ordering and exact JD phrasing for skills the user already has (exact-match ATS layer; dual-format each acronym once here)
4. Bullet selection and reordering to surface the most relevant evidence; top bullet of the most recent role
5. Project / secondary emphasis choice
6. Implicit-industry-expectation keywords and terminology bridges woven into existing bullets — without echoing distinctive JD phrases

Don't touch:

- The stable identity headline (it comes from the master / manifest, not the JD)
- Job titles on past roles (unless the title was genuinely different — never inflate)
- Employer names, dates, location
- Education
- Canonical accomplishment wording where selection/reordering already covers the requirement
- Bullets from older roles — **with one exception:** when a JD sets a hard per-skill minimum-years requirement (e.g., "5+ years C++"), back-port that genuinely-used keyword into older roles so the dated work history sums to the minimum. ATS credit skill-specific experience only from dated roles where the keyword appears, so a skill confined to recent roles or the Skills section is under-counted. Only ever back-port a skill the user actually used in that role; never invent usage to pad tenure. See the skill-duration math in `build-targeted-resume`.

### Layered ATS optimization

Exact-match optimization is useful for ATS and lowers human inference cost, but applying it across every resume surface at once makes the application look over-tuned or AI-generated. Optimize in layers so the matching stays high-value while the optimization process itself stays hidden:

1. **Identity = stable.** Keep the master's professional identity headline. Never copy the JD's target title into `.role-line` or the summary opener.
2. **Skills section = exact-match layer.** Include exact JD terms when they are true, important, and a reasonable claim of experience grounded in `Work Experience/` notes. Never add a JD-only skill on adjacency alone.
3. **Bullets / summary = conventional terminology + bridges.** Match the employer's concepts and conventional industry terms; do not lift distinctive multi-word JD phrases or sentence structures. When the canonical notes use an internal term for a JD-required concept, bridge explicitly to the accurate industry/JD equivalent rather than forcing reviewers to infer the mapping or silently renaming the accomplishment.
4. **Acronyms once.** Both expanded form and acronym appear somewhere once (usually in Skills); afterward use one form only.
5. **Tailor by selection, not rewrite.** Prefer bullet selection, ordering, project choice, summary emphasis, Relevant Highlights selection, and skills ordering. Minimize semantic rewrites of canonical accomplishments.

## Resume masters

Maintained master resumes are the stable baselines that `build-targeted-resume` copies and tunes. The blank template remains the sole layout/CSS source; masters are filled HTML derived from the template + `Work Experience/` notes. The **number of masters and what each is for is user configuration** — every user's split is different — and lives in the user-owned manifest.

### Manifest: `Work Experience/resume-masters.md`

One entry per master. Suggested structure:

```markdown
# Resume Masters

How this candidate's maintained resumes are split. Used by `generate-master-resumes`
(to build/update) and by `build-targeted-resume` / `extract-job-signals` (to classify
a JD and pick the best-fit baseline).

## <Name>

- **Purpose:** <What role family this master targets>
- **Identity headline:** `<Exact string for .role-line and summary opener>`
- **Role-family cues:** <Keywords, stacks, and signals that mean "use this master">
- **File:** `Resume Masters/Master Resume - <Name>.html`
```

Illustrative example (not a hardcoded default — adapt per user):

```markdown
# Resume Masters

## AI / Platform

- **Purpose:** AI platform, ML infrastructure, and AI-adjacent distributed systems roles
- **Identity headline:** `Senior Software Engineer | AI Platforms & Distributed Systems`
- **Role-family cues:** AI platform, ML infra, LLM, RAG, inference, AI engineering, agentic systems
- **File:** `Resume Masters/Master Resume - AI Platform.html`

## Backend

- **Purpose:** Backend and distributed systems roles without a primary AI mandate
- **Identity headline:** `Senior Software Engineer | Backend & Distributed Systems`
- **Role-family cues:** backend, distributed systems, microservices, API platform, data pipeline (non-ML-primary)
- **File:** `Resume Masters/Master Resume - Backend.html`
```

Prefer a small set (1–3). A third "general" master is usually unnecessary if a personal site can serve as the broader CV; add one only when a concrete use case appears.

### Generated files: `Resume Masters/`

```
Resume Masters/
  Master Resume - <Name>.html
```

Created and updated by `generate-master-resumes`. Tailoring copies the selected file into `Job Applications/<Company>/<Role>/Resume - <Company> - <Role>.html` and edits the copy.

### Regeneration triggers

Regenerate masters (via `generate-master-resumes`) when:

- A role, skill, metric, or project is added/changed in `Work Experience/`
- The identity headline or purpose in the manifest changes
- The blank template or `formatting-guide.md` changes in a way that should apply to all resumes
- `job-application` freshness check finds notes newer than the master HTML

### Stable identity

Each master's identity headline is the candidate's professional identity for that role family. Tailored resumes **keep that headline** and adopt JD terminology only via the layered model in "Layered ATS optimization" above (exact match in Skills when grounded; conventional terminology + bridges in bullets). Do not copy the JD's target title into `.role-line` or the summary opener — exact title mirroring reads as mechanical and reduces perceived authenticity, even when it helps ATS searchability elsewhere.

## Consulting and contract work

How to present independent consulting depends on engagement length and scope. Both algorithms and humans read very differently based on this decision.

### Decision rule

- **Short engagements (under ~6 months) or many parallel/overlapping clients:** Consolidate under a single overarching "Independent Consultant" or LLC-name heading.
- **Long engagements (6+ months) with distinct scope and a recognizable client:** List as separate roles with a contract modifier.

### Consolidated format

```
Independent Consultant (or <LLC Name>) | Remote
MM/YYYY – Present
- Engagement 1: <Client industry/type>. <Verb + tech + outcome>.
- Engagement 2: <Client industry/type>. <Verb + tech + outcome>.
- Engagement 3: <Client industry/type>. <Verb + tech + outcome>.
```

Each engagement becomes a bullet. Continuous date range across all engagements ensures the ATS calculates tenure correctly. If a specific client name adds credibility and confidentiality allows, use it.

### Separate-role format (for long, distinct engagements)

```
Senior <Title> — Contract | <Client / Recognizable Company> | <Location or Remote>
MM/YYYY – MM/YYYY
- <Verb + tech + outcome>
- <Verb + tech + outcome>
- <Verb + tech + outcome>
```

The "Contract" / "Consultant" label is important — without it, the role reads as a short tenure and may trigger job-hopping concerns.

### Concurrent roles

When a consulting (or other secondary) engagement **overlaps in dates** with a full-time role, make the concurrency unambiguous on the resume. ATS risk from overlapping dates is usually low; human reviewers may pause to reconcile whether both were full-time.

Preferred presentation:

- Label the secondary engagement as part-time consulting, e.g. `Consultant — Part-time | <Client>` or include "Part-time" in the role line.
- Add a one-line clarifier that it ran alongside the full-time role (this can be the role-context line or the first short bullet). One line is enough — do not spend a full accomplishment bullet on the clarification.
- Do **not** put employer consent, permission, or background-check narrative on the resume. Those details belong in conversation if asked.

Example shape:

```
Consultant — Part-time | <Client> | <Location or Remote>
Mon YYYY – Mon YYYY
Part-time consulting alongside full-time role at <Full-Time Employer>.
- <Verb + tech + outcome>
```

Apply this whenever dates overlap, including on master resumes — concurrent clarity is part of the stable baseline, not a per-JD tweak.

### Common pitfalls

- **Listing every 1-2 month gig as a separate job.** Reads as job-hopping; depresses calculated total tenure.
- **Using "Consultant" alone as a job title.** Reads as non-technical advisory work. Always pair with the actual technical title: "Senior Software Engineer — Contract" or "AI Architect, Independent Consultant".
- **Omitting the contract modifier.** Without it, a 9-month engagement at a known company looks like a short stay and a possible departure problem.

## Tracking and follow-up

- Keep a simple spreadsheet of applications: company, role, channel (direct/Easy Apply/referral), date submitted, status, recruiter contact if known.
- Direct outreach to the hiring manager or a team member on LinkedIn after applying tends to outperform passive waiting. Keep it short and reference a specific point of relevance.
- If you applied via Easy Apply for a role you genuinely want, follow up by also applying through the company's portal a few days later — the company's ATS will likely keep both records and the direct submission has the better parser.
