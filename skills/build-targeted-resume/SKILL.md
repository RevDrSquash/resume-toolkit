---
name: build-targeted-resume
description: Build a targeted, ATS-optimized resume HTML for a specific job from the user's experience and a signal report. Outputs styled HTML, ready for review and later PDF rendering. Trigger when the user wants to draft, tailor, or update their resume for a specific job description. Takes a JD, a signal report, and the user's experience notes; produces a single styled HTML file.
---

# Build Targeted Resume

Produce a two-page, ATS-compatible resume tailored to a specific job description using the user's existing experience. The deliverable is a styled HTML file: visually polished (single column, right-aligned dates) and ATS-parseable (real text layer in DOM order, MM/YYYY dates, no tables-for-layout). The visual styling (colors, fonts, accent rules) is owned by the bundled template file, not this document. This skill stops at the HTML; rendering it to PDF is `publish-resume`'s job.

## When to use

- User has a target job and wants a tailored resume drafted
- User wants to update their existing resume for a new posting
- User has experience notes (`Work Experience/`) and wants a targeted variant

## Inputs

- **Required:** The original job description
- **Required:** A signal report (markdown, in the format produced by `extract-job-signals`)
- **Required:** User's experience notes — the `Work Experience/` directory (`work history.md`, `experience - <Company>.md`, `skills - technical.md`) or, failing that, any freeform career summary
- **Required:** Stable personal facts — `Work Experience/personal-details.md` (name, location, phone, email, LinkedIn, education). These are the source of truth for the header and Education section; do not re-derive them from a recent resume. If the file is missing a fact you need, ask the user rather than pulling it from an old resume.
- **Bundled template:** `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` (styled HTML skeleton with the canonical CSS and section structure — copy and fill)
- **Reference:** `.claude/skills/resume-toolkit/reference/formatting-guide.md` (parseability rules: single-column reading order, MM/YYYY dates, no icons — still apply to the HTML output)
- **Reference:** `.claude/skills/resume-toolkit/reference/industry-signals.md` (industry-standard keyword lexicon)

**Build from canonical sources, never from a previous resume.** Layout comes from the bundled template (+ `formatting-guide.md`); experience content comes from the `Work Experience/` notes; personal facts come from `personal-details.md`. Previous resumes — including the most recent one in another `Job Applications/` folder — are **presumed stale** for both formatting *and* content (old layout, retired phrasing, outdated bullets, missing recently-added roles). Don't pattern-match off one. Consult a prior artifact only as a last resort when a canonical source is genuinely missing something, verify against canonical, and prefer back-filling the canonical source over copying it forward. Full rule: "Canonical sources & precedence" in `.claude/skills/resume-toolkit/reference/application-protocol.md`.

## Target audience and tone

Assume the reader is a Senior Engineering Manager or a highly technical ATS. Operate in a high-context environment.

- **Don't define, qualify, or explain standard industry tools, languages, platforms, or frameworks.** The reader knows what Python, Kubernetes, PostgreSQL, AWS, Kafka, and Docker are. Skip the in-line definitions and explanatory asides.
- **State the tool, then jump straight to the architecture, the implementation detail, or the business impact.** "Used Kafka for the event bus" is wasted space. "Scaled the Kafka event bus to 80k msgs/sec by repartitioning on user-id and replacing the consumer-group coordinator" is the bullet.
- **Report work, not vocabulary.** When a bullet starts to explain what a technology is, the writer has slipped into performing knowledge. Cut back to what was done and what changed.

Example:
- Don't: "Worked extensively with Apache Kafka, a distributed event streaming platform used for high-throughput pipelines, to build real-time data ingestion."
- Do: "Built a Kafka ingestion pipeline handling 80k events/sec at p99 under 50ms, replacing a nightly batch ETL."

For the catalog of specific phrasings and verbs to avoid (em-dashes, "leveraged"/"utilized", tricolons, puffery, etc.), see the "AI-sounding patterns to avoid" section in `.claude/skills/resume-toolkit/reference/formatting-guide.md`. This section sets the audience frame; that section enumerates the patterns.

## Process

### 1. Mirror the title
Place the exact "Title to Mirror" string from the signal report in the professional summary's opening sentence and (if appropriate) the resume header. This is the single highest-leverage edit.

### 2. Cover required skills
Compare the signal report's `Required Skills` list against the user's actual experience. For every required skill the user genuinely has:
- Add it to the dedicated `Skills` section
- Use exact JD phrasing (dual-format acronyms: "Retrieval-Augmented Generation (RAG)")
- Embed the most important 3-5 required skills into bullet points in the most recent role, paired with a metric

For skills the user doesn't have: do not invent them. Note the gap for the user to consider.

**Meet the minimum years of experience (skill-duration math).** For each item in the signal report's `Minimum Years of Experience` section, the keyword must clear the ATS's duration calculation, not just appear once. ATS compute skill-specific experience by finding the keyword inside dated work-experience entries and **summing the durations of those roles**. A skill that lives only in the Skills section has no date anchors attached, so most parsers (Workday, Taleo, iCIMS) credit it with **zero** years — even if the user has a decade of it. To clear a "5+ years of X" requirement:

- Identify which of the user's roles genuinely used skill X, using the role attribution in `Work Experience/skills - technical.md` (and the per-role `experience - <Company>.md` notes). If the notes don't say when a skill was used, **ask the user** — don't guess which roles can carry it.
- Ensure X appears in the bullets (or role-context line) of enough of those dated roles that their durations sum to at least the required minimum. This usually means **back-porting** the keyword into older roles, not just featuring it in the most recent one.
- Back-port **truthfully**. Only weave a keyword into a role where the user actually used that skill. Integrating a genuinely-used term into an older bullet is legitimate even if it wasn't that role's headline achievement; inventing usage is not. If the user's real history can't reach the minimum, that's a candidate gap — note it for the user, never fabricate tenure.
- This is a deliberate exception to the "don't touch bullets from older roles" guidance in the 80/20 rule (`.claude/skills/resume-toolkit/reference/application-protocol.md`): when a hard YOE minimum demands it, editing an older role's bullet to carry a genuinely-used keyword is the correct move.
- Keep the date format identical across **every** role (the template's `Mon YYYY - Mon YYYY`). Mixed date styles make the parser's duration arithmetic fail silently and can wipe out the YOE you just built.
- Secondary reinforcement only: some advanced semantic parsers (Daxtra, Sovren) read an explicit `C++ (7+ years)` callout in the Skills section and honor the literal number. It's a safe addition where natural, but never a substitute for back-porting — legacy and rule-based parsers ignore it.

### 3. Apply the 80/20 baseline
The resume should be ~80% stable core (foundational skills the user always lists) and ~20% swappable based on the signal report. Swap zones:
- Professional Summary (3-4 sentences, includes mirrored title, 3-5 critical keywords, and 1-2 standout role-relevant metrics — never a stack)
- Skills section top-of-list ordering
- Top bullet of most recent role

### 4. Contextualize bullets with Action-Skill Pairs
For each verb-skill pair in the signal report, write or revise a bullet in the relevant role that:
- Starts with the action verb (or a stronger synonym)
- Names the skill/technology
- Ends with a quantified outcome (latency reduced X%, throughput Y, cost Z, headcount unblocked, etc.)

This verb → skill → metric shape is Google's X-Y-Z formula ("Accomplished [X] as measured by [Y], by doing [Z]"): the action is the accomplishment, the metric is the measurement, the skill/method is how. It pairs a keyword with a number in the exact structure an ATS and a skimming reader both extract cleanly.

**Format every metric as a numeral with its unit or symbol** — `50%`, `$2M`, `80k msgs/sec`, `4M+ queries/month` — never spelled out (`fifty percent`) and never a vague quantifier (`roughly half`, `many`, `significant`). Numerals are what survives an ATS scan and what a 15-second skim catches; words and vague estimates get missed or read as filler. Where the underlying data supports it, frame the change against a baseline or timeframe (`from 4s to 800ms`, `per quarter`, `within 90 days`) so the number is comparable and concrete. Do not invent a baseline to fit the pattern — if you only have the end-state number, state just that.

Example: signal report has "Deploy RAG pipelines" → bullet: "Deployed production RAG pipeline on AWS Bedrock serving 4M+ queries/month with p95 latency under 800ms."

### 5. Cover implicit industry expectations
For each item in the signal report's `Implicit Industry Expectations`, ensure it appears at least once in the resume — typically in the Skills section or woven into an existing bullet. Don't pad bullets just to fit these in.

### 6. Fill the HTML template
Copy `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` into the job-application folder as `Resume - <Company> - <Role>.html`, then replace the placeholder tokens with the user's tailored content. The template bakes in:

- Single column, sequential DOM order (ATS extracts in correct reading order even where flexbox visually right-aligns dates)
- Visual styling (accent colors, accent rules, font family, base font size) — whatever the current template defines is what new resumes should use
- MM/YYYY-equivalent date format (e.g., `Sep 2025 - Apr 2026`)
- Section order: Header → Summary → Work Experience → Education → Skills (titled "Skills", not "Core Competencies", so ATS parsers detect it as a standard skills-section anchor)
- Print-ready `@page` letter, 0.55in/0.6in margins, page-break-inside protection on `.entry` blocks

The parseability rules in `.claude/skills/resume-toolkit/reference/formatting-guide.md` still apply (single column, no icons, no layout tables, no header-region contact info). The HTML template already conforms — just don't add anti-parser elements when extending it.

### 7. Length and pruning
- Target two pages for senior candidates (10+ years experience)
- Reverse-chronological
- Roles older than 10 years: condense to a "Previous Experience" line block without bullets
- Consulting: apply the consulting protocol from `.claude/skills/resume-toolkit/reference/application-protocol.md` (consolidate short engagements; list 6+ month engagements with distinct scope as separate roles)
- **Write for concision up front.** Keep each bullet to roughly one line and the summary to 3-4 sentences. `.claude/skills/resume-toolkit/scripts/lint_resume.py` flags bullets over ~150 chars as sprawling and over ~220 chars as a wall of text, and a summary over ~600 chars as bloated; treat those findings as rewrite prompts, not just warnings. Dense, single-idea bullets are the main defense against a two-page resume spilling onto a third.
- Estimate length from the HTML content density (bullet counts, section sizes). Page-count verification happens at PDF-render time. If the resume runs long, the fix is cutting words here — not shrinking the CSS. The template's spacing is deliberately roomy so the page doesn't read as a wall of text; CSS tightening is `publish-resume`'s last resort (within fixed floors), never a substitute for concise writing.

## Output

One file in the job-application folder:

1. **`Resume - <Company> - <Role>.html`** — the styled HTML, copied from the bundled template and filled with tailored content. Section order:
   1. Header — Name, target title (mirrored), City/Region/Country, Phone, Email, LinkedIn URL (plain text). Pull name, location, phone, email, and LinkedIn from `Work Experience/personal-details.md`.
   2. Summary — 3-4 sentences; first sentence includes mirrored title
   3. Work Experience — Reverse-chronological. `Mon YYYY - Mon YYYY` (or `Present`). Each role: title/employer, dates, location, bullets
   4. Education — Degree, Major, Institution, Graduation Year. Pull from `Work Experience/personal-details.md`.
   5. Skills — Comma-separated, organized by category, with purple-accent labels. Title this section exactly "Skills" so ATS parsers reliably detect it as a standard skills-section anchor.

Do not render the PDF from this skill — that's `publish-resume`'s job.

## Rules and constraints

- **Never invent skills, projects, or metrics.** If the user hasn't claimed it in their input, don't put it on the resume. Flag gaps for the user instead.
- **Mirror the JD's exact phrasing for required skills.** Don't paraphrase or substitute synonyms unless dual-formatting an acronym.
- **Quantify or cut.** Every bullet under a recent role should have a number or a concrete outcome. Bullets without either are filler — remove or rewrite. Write metrics as numerals with units/symbols (`50%`, `$2M`, `80k req/s`), never spelled out (`fifty percent`) or vague (`many`, `significant`, `roughly half`).
- **No fluff words.** Strip "results-driven", "synergy", "rockstar", "team player". They cost space and signal nothing.
- **Don't over-tailor.** The resume should still describe the user's actual career — modular swaps in the summary, skills, and top bullets, not a full rewrite to mimic the JD.
- **Output the full resume, not a diff.** Even for an update, produce the complete final document so the user can replace their working copy.
- **Apply the AI-sounding patterns rules from `.claude/skills/resume-toolkit/reference/formatting-guide.md`.** That section is the source of truth for em-dashes, puffery on well-known entities, AI-favorite verbs ("leveraged", "utilized", "spearheaded"), tricolon openers, fast-paced-landscape framings, and adjective stacking. A resume that reads as AI-written gets discarded.

## Gotchas

- **The canonical sources supersede previously produced resumes and cover letters — for content as well as formatting.** When tailoring a new resume, take *formatting* from `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` (+ `.claude/skills/resume-toolkit/reference/formatting-guide.md` and `.claude/skills/resume-toolkit/reference/industry-signals.md`) and take *experience content* — bullets, metrics, role scope, and which roles even exist — from the `Work Experience/` notes. Do not pattern-match off a recent resume in another job-application folder. Those reflect the template, the rules, **and the user's experience notes** as they existed at the time, and the user evolves all of them. Anchoring on a prior artifact silently inherits its drift: not just stale formatting (older accent colors, retired phrasing, outdated section ordering) but **stale content** — superseded bullet wording, metrics that have since been corrected, and missing roles the user has added to `Work Experience/` since. A prior resume is a last-resort fallback only, used per the precedence rule in `.claude/skills/resume-toolkit/reference/application-protocol.md` when a canonical source is genuinely missing something.


## Self-check before returning

Content:
- [ ] Mirrored title appears in the summary's first sentence and in the `.role-line` under the name
- [ ] Every Required Skill the user genuinely has is covered
- [ ] Top 3-5 required keywords are embedded in recent-role bullets with metrics
- [ ] Every required per-skill minimum from `Minimum Years of Experience` is backed by the keyword appearing across dated roles whose durations sum to at least the minimum (not just in the Skills section); minimums the user can't truthfully reach are flagged as gaps, not faked
- [ ] Date format is identical across every role (no mixed styles that would break the parser's duration math)
- [ ] All metrics are numerals with units/symbols (`50%`, `$2M`), never spelled out or vague (`fifty percent`, `many`, `significant`)
- [ ] All Implicit Industry Expectations appear at least once
- [ ] Acronyms are dual-formatted on first mention
- [ ] Dates are `Mon YYYY` format throughout
- [ ] No placeholder tokens (`[FULL NAME]`, `[City, Region, ...]`, etc.) remain from the template
- [ ] No em-dashes (`—`) anywhere; no other AI-sounding patterns from `.claude/skills/resume-toolkit/reference/formatting-guide.md` (puffery on well-known entities, "leveraged"/"utilized" verbs, tricolons, negation-reversal antithesis like "not just X but Y" / "it's not X, it's Y", fast-paced-landscape framings, adjective stacking)
- [ ] No semicolons in bullets (split the ideas or use a comma/period)
- [ ] Summary anchors on 1-2 standout metrics (numerals, role-relevant), not zero and not a stats dump (per `formatting-guide.md` Professional Summary rules)
- [ ] Bullets read at ~one line and the summary at 3-4 sentences; nothing sprawls into a wall of text (`.claude/skills/resume-toolkit/scripts/lint_resume.py` reports zero length findings)
