# Application Protocol

How to actually submit applications — channel choice, knockout questions, experience-notes hygiene, and consulting representation. Used by `build-targeted-resume` (for consulting formatting), `job-application` (for channel choice and knockout questions when assembling an application), and as a standalone reference when deciding how to apply.

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

Every targeted resume is assembled from **canonical sources**, never from a previous resume. There are exactly two, plus one for personal facts:

- **Formatting & layout** comes from `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` (the fill-in skeleton — section order, CSS, accent colors, date format) and the rules in `.claude/skills/resume-toolkit/reference/formatting-guide.md`. Copy the template fresh for each application.
- **Experience content** comes from the **`Work Experience/` notes** — `work history.md` (dates/titles), `experience - <Company> - <Position>.md` (scope, accomplishments, draft bullets), `skills - technical.md` / `skills - soft.md` (skill catalogue + role attribution), and `projects.md`. See "Experience notes hygiene" below.
- **Personal facts** (name, location, phone, email, LinkedIn, education) come from `Work Experience/personal-details.md`.

**Precedence / fallback rule.** Previous resumes and cover letters — anything under `Job Applications/<Company>/<Role>/` — are **not canonical**. They are point-in-time snapshots and are presumed **stale**. Do not pattern-match a new resume off a prior artifact for either layout or content. Consult a prior artifact only as a **last resort**, when a canonical source genuinely lacks something you need; when you do, verify it against the canonical sources, and prefer **back-filling the canonical source** (the template or the `Work Experience/` notes) over copying the artifact forward.

**Why this matters.** Canonical sources are edited **once** and propagate to every future resume — change the template layout, revise a bullet, or add a new role in `Work Experience/`, and the next resume reflects it automatically. A prior artifact does the opposite: anchoring on it silently inherits its drift (retired accent colors and phrasing, outdated section ordering, stale bullets, and roles that have since been added or changed), reproducing an old state instead of the intended current one.

## Experience notes hygiene

The source of truth for experience content is the **`Work Experience/` notes** (per "Canonical sources & precedence" above), not a single master-resume document and not a prior tailored resume. That directory is the evidence database every targeted resume draws from:

- **`work history.md`** — the authoritative record of employers, titles, locations, and dates. Resume date ranges come from here.
- **`experience - <Company> - <Position>.md`** — one file per role: scope, responsibilities, accomplishments, and draft bullets.
- **`skills - technical.md` / `skills - soft.md`** — the skill catalogue (see the skill-to-role mapping note below).
- **`projects.md`** — side projects and open-source work not tied to an employer.

Keep these healthy:

- **Capture everything, trim nothing.** Every project, technology, metric, role, and quantified outcome belongs in the notes even if no single resume uses it all. These files are for you, not for submission.
- **Update cadence:** every time you finish something worth mentioning, or quarterly at minimum. The hardest part of tailoring is reconstructing forgotten metrics — capture them while fresh.

### Record which skills map to which roles

`skills - technical.md` catalogues each technology with the roles (and, where known, the duration) it was used in — e.g., "C++ — ACD Systems (7 years), MDA Space". Maintain that role attribution deliberately, because two parts of the tailoring process depend on it:

- **Truthful back-porting for YOE minimums.** When a JD sets a hard per-skill minimum ("5+ years C++"), `build-targeted-resume` weaves that keyword into the bullets of older dated roles so the parser's duration sum clears the bar. It may only do this for roles where the skill was genuinely used — the per-role mapping is what tells it which roles those are. Without it, the builder has to stop and ask.
- **Bullet optimization.** When a nice-to-have skill was used in several roles, the mapping lets the builder place it once — in whichever role has the fewest other bullets or the weakest coverage — instead of redundantly across all of them, keeping each role's bullets dense and distinct.

When a skill's role attribution or rough duration is missing from the notes, fill it in rather than guessing at draft time.

### The 80/20 targeting rule

Each targeted resume is ~80% stable core and ~20% swappable per application:

- **80% baseline (stable across applications):** Header, education, certifications, foundational skills you always list, your 2-3 most recent roles' core bullets, your professional summary's general identity.
- **20% swappable per JD:** The mirrored job title, top-of-skills-section ordering, top bullet of the most recent role, 5-10 specific keywords swapped in based on the signal report.

Swap zones, ordered by leverage:

1. The professional summary's opening sentence (mirror the title; include 3-5 target keywords)
2. The Skills section's ordering and dual-format acronym variants
3. The top bullet of the most recent role
4. Implicit-industry-expectation keywords woven into existing bullets

Don't touch:
- Job titles (unless the title was genuinely different — never inflate)
- Employer names, dates, location
- Education
- Bullets from older roles — **with one exception:** when a JD sets a hard per-skill minimum-years requirement (e.g., "5+ years C++"), back-port that genuinely-used keyword into older roles so the dated work history sums to the minimum. ATS credit skill-specific experience only from dated roles where the keyword appears, so a skill confined to recent roles or the Skills section is under-counted. Only ever back-port a skill the user actually used in that role; never invent usage to pad tenure. See the skill-duration math in `build-targeted-resume`.

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

### Common pitfalls

- **Listing every 1-2 month gig as a separate job.** Reads as job-hopping; depresses calculated total tenure.
- **Using "Consultant" alone as a job title.** Reads as non-technical advisory work. Always pair with the actual technical title: "Senior Software Engineer — Contract" or "AI Architect, Independent Consultant".
- **Omitting the contract modifier.** Without it, a 9-month engagement at a known company looks like a short stay and a possible departure problem.

## Tracking and follow-up

- Keep a simple spreadsheet of applications: company, role, channel (direct/Easy Apply/referral), date submitted, status, recruiter contact if known.
- Direct outreach to the hiring manager or a team member on LinkedIn after applying tends to outperform passive waiting. Keep it short and reference a specific point of relevance.
- If you applied via Easy Apply for a role you genuinely want, follow up by also applying through the company's portal a few days later — the company's ATS will likely keep both records and the direct submission has the better parser.
