---
name: build-targeted-resume
description: Build a targeted, ATS-optimized resume HTML for a specific job by copying the best-fit master resume and tuning it to the signal report. Outputs styled HTML, ready for review and later PDF rendering. Trigger when the user wants to draft, tailor, or update their resume for a specific job description. Takes a JD, a signal report, and the user's master resumes; produces a single styled HTML file.
---

# Build Targeted Resume

Produce a two-page, ATS-compatible resume tailored to a specific job description by **copying the best-fit master resume and tuning it**, not by rebuilding from a blank template. The deliverable is a styled HTML file: visually polished (single column, right-aligned dates) and ATS-parseable (real text layer in DOM order, MM/YYYY dates, no tables-for-layout). The visual styling (colors, fonts, accent rules) is owned by the bundled template file that the masters themselves were built from. This skill stops at the HTML; rendering it to PDF is `publish-resume`'s job.

Masters and the user-owned split live outside this skill — see "Resume masters" in `.claude/skills/resume-toolkit/reference/application-protocol.md`. If masters are missing, direct the user to `generate-master-resumes` first.

## When to use

- User has a target job and wants a tailored resume drafted
- User wants to update their existing resume for a new posting
- User has maintained masters under `Resume Masters/` and wants a targeted variant

## Inputs

- **Required:** The original job description
- **Required:** A signal report (markdown, in the format produced by `extract-job-signals`)
- **Required:** User's master resumes — `Resume Masters/Master Resume - <Name>.html` plus the manifest `Work Experience/resume-masters.md` (used to classify the JD and pick the baseline)
- **Required:** User's experience notes — the `Work Experience/` directory (`work history.md`, `experience - <Company> - <Position>.md`, `skills - technical.md`) for grounding checks, YOE back-porting, and filling gaps the master doesn't yet cover
- **Required:** Stable personal facts — `Work Experience/personal-details.md` (name, location, phone, email, LinkedIn, education). These are the source of truth for the header and Education section; do not re-derive them from a recent tailored resume. If the file is missing a fact you need, ask the user rather than pulling it from an old resume.
- **Fallback only:** Blank template at `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html` — use only if the user declines to generate masters first
- **Reference:** `.claude/skills/resume-toolkit/reference/formatting-guide.md` (parseability rules: single-column reading order, MM/YYYY dates, no icons — still apply to the HTML output)
- **Reference:** `.claude/skills/resume-toolkit/reference/industry-signals.md` (industry-standard keyword lexicon)
- **Reference:** `.claude/skills/resume-toolkit/reference/application-protocol.md` (masters, concurrent roles, 80/20)

**Start from the selected master, never from a previous tailored resume.** The master is the sanctioned ~80% baseline (stable identity, chronology, grounded claims). Experience content that must change still comes from the `Work Experience/` notes; personal facts come from `personal-details.md`. Previous tailored resumes under `Job Applications/` are **presumed stale** for both formatting *and* content. Don't pattern-match off one. Consult a prior tailored artifact only as a last resort when a canonical source is genuinely missing something, verify against canonical, and prefer back-filling the notes (then regenerating the master) over copying a tailored artifact forward. Full rule: "Canonical sources & precedence" in `.claude/skills/resume-toolkit/reference/application-protocol.md`.

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

### 0. Select and copy the best-fit master

1. Read `Work Experience/resume-masters.md` and the signal report's `Role Family` (and `Target Title` / skills) to classify the posting against the manifest's role-family cues.
2. Pick the closer master. If two are equally close, prefer the one whose identity headline and purpose best match the JD's primary stack; tell the user which you chose and why.
3. If masters or the manifest are missing, **stop and direct the user to `generate-master-resumes`**. Only fall back to copying the blank template if the user explicitly declines to create masters — and note that the draft will lack a stable baseline.
4. Copy `Resume Masters/Master Resume - <Name>.html` into the job-application folder as `Resume - <Company> - <Role>.html`. That copy is the starting point for every subsequent step.

### 1. Keep the stable identity

**Do not copy the JD's target title into the resume headline or the summary's identity.** Keep the master's stable identity headline (`.role-line` and summary opener) verbatim — that is the candidate's professional identity for this role family.

- The signal report's `Target Title` is for terminology mapping and ATS searchability elsewhere, not for rebuilding who the candidate is.
- Adopt JD terminology via the layered model (exact phrasing in Skills when grounded; conventional terminology + bridges in bullets) **only where it accurately maps to existing experience**. Prefer omission or an explicit gap over forced matching or inventing missing skills.
- Never invent a new identity string for a single posting.

### 2. Cover required skills (layered ATS matching)

Compare the signal report's `Required Skills` list against the user's actual experience (master + `Work Experience/` notes). Optimization is **layered** so the resume stays ATS-aware without looking mechanically reconstructed from the JD:

**Skills section = exact-match ATS layer.** For every required skill the user genuinely has — and only when the claim is true, important, and a reasonable claim of experience:

- Add it to the dedicated `Skills` section (or promote it in the ordering if already present)
- Use exact JD phrasing there
- **Never add a JD-only skill based on adjacency.** Exact-match terms must still be grounded in documented experience (`Work Experience/` notes or the master). If the user has a related but different skill, do not invent the JD's term; note the gap instead

**Bullets and summary = conventional terminology, not JD echo.** Embed the most important 3-5 required *concepts* into recent-role bullets paired with a metric, using conventional industry terminology the JD also uses — not distinctive multi-word JD phrases or sentence structures. Prefer the signal report's `Distinctive JD Phrases (do not echo)` list as a denylist for bullets/summary. Match the employer's concepts; do not copy the posting's voice.

**Terminology bridging.** When the canonical notes or master use an internal / non-standard term for something the JD requires, make the connection explicit in the bullet or Skills entry (e.g., bridge the canonical term to the accurate industry/JD equivalent). Do not force reviewers to infer the mapping, and do not silently rename the accomplishment to the JD's phrasing.

**Acronyms once.** Ensure both the expanded form and the acronym appear somewhere once when useful for ATS (the Skills section is the natural home: "Retrieval-Augmented Generation (RAG)"). After that first dual-format, use one form only — usually the acronym. Do not re-expand the same acronym throughout the resume.

For skills the user doesn't have: do not invent them. Note the gap for the user to consider.

**Meet the minimum years of experience (skill-duration math).** For each item in the signal report's `Minimum Years of Experience` section, the keyword must clear the ATS's duration calculation, not just appear once. ATS compute skill-specific experience by finding the keyword inside dated work-experience entries and **summing the durations of those roles**. A skill that lives only in the Skills section has no date anchors attached, so most parsers (Workday, Taleo, iCIMS) credit it with **zero** years — even if the user has a decade of it. To clear a "5+ years of X" requirement:

- Identify which of the user's roles genuinely used skill X, using the role attribution in `Work Experience/skills - technical.md` (and the per-role `experience - <Company>.md` notes). If the notes don't say when a skill was used, **ask the user** — don't guess which roles can carry it.
- Ensure X appears in the bullets (or role-context line) of enough of those dated roles that their durations sum to at least the required minimum. This usually means **back-porting** the keyword into older roles, not just featuring it in the most recent one.
- Back-port **truthfully**. Only weave a keyword into a role where the user actually used that skill. Integrating a genuinely-used term into an older bullet is legitimate even if it wasn't that role's headline achievement; inventing usage is not. If the user's real history can't reach the minimum, that's a candidate gap — note it for the user, never fabricate tenure.
- This is a deliberate exception to the "don't touch bullets from older roles" guidance in the 80/20 rule (`.claude/skills/resume-toolkit/reference/application-protocol.md`): when a hard YOE minimum demands it, editing an older role's bullet to carry a genuinely-used keyword is the correct move.
- Keep the date format identical across **every** role (the template's `Mon YYYY - Mon YYYY`). Mixed date styles make the parser's duration arithmetic fail silently and can wipe out the YOE you just built.
- Secondary reinforcement only: some advanced semantic parsers (Daxtra, Sovren) read an explicit `C++ (7+ years)` callout in the Skills section and honor the literal number. It's a safe addition where natural, but never a substitute for back-porting — legacy and rule-based parsers ignore it.

### 3. Apply the 80/20 baseline

The copied master **is** the ~80% stable core. The ~20% swappable layer for this posting (selection and ordering first; minimize semantic rewrites):

- Professional Summary emphasis (keep the identity opener; adjust the following sentences for role-relevant capabilities and 1-2 standout metrics — never a stack, never a new identity)
- Skills section top-of-list ordering and exact JD phrasing for skills the user already has (the exact-match layer)
- Bullet selection and reordering to surface the most relevant evidence; top bullet of most recent role
- Projects or secondary emphasis the master de-emphasized for this role family

Preserve from the master: identity headline, employment chronology, employers, dates, titles, grounded claims, and canonical accomplishment wording wherever selection already covers the requirement. Do not rebuild the candidate around the target title.

### 4. Cover Action-Skill Pairs by selection first

For each verb-skill pair in the signal report, prefer **selecting and reordering** existing master bullets that already carry the pair (or a truthful conventional equivalent) over rewriting them. Tailor aggressively through bullet selection, ordering, project choice, summary emphasis, and skills ordering; **minimize unnecessary semantic rewrites of canonical accomplishments**.

Only write or revise a bullet when no grounded master bullet can truthfully carry the keyword. When you do rewrite, keep the verb → skill → metric shape:

- Starts with the action verb (or a stronger synonym)
- Names the skill/technology in conventional terminology (not a distinctive JD phrase)
- Ends with a quantified outcome (latency reduced X%, throughput Y, cost Z, headcount unblocked, etc.)

This verb → skill → metric shape is Google's X-Y-Z formula ("Accomplished [X] as measured by [Y], by doing [Z]"): the action is the accomplishment, the metric is the measurement, the skill/method is how. It pairs a keyword with a number in the exact structure an ATS and a skimming reader both extract cleanly.

**Format every metric as a numeral with its unit or symbol** — `50%`, `$2M`, `80k msgs/sec`, `4M+ queries/month` — never spelled out (`fifty percent`) and never a vague quantifier (`roughly half`, `many`, `significant`). Numerals are what survives an ATS scan and what a 15-second skim catches; words and vague estimates get missed or read as filler. Where the underlying data supports it, frame the change against a baseline or timeframe (`from 4s to 800ms`, `per quarter`, `within 90 days`) so the number is comparable and concrete. Do not invent a baseline to fit the pattern — if you only have the end-state number, state just that.

Example: signal report has "Deploy RAG pipelines" and the master already has a strong RAG deployment bullet → promote that bullet; do not rewrite it to echo the JD. Only if nothing covers it: "Deployed production RAG pipeline on AWS Bedrock serving 4M+ queries/month with p95 latency under 800ms."

### 5. Cover implicit industry expectations

For each item in the signal report's `Implicit Industry Expectations`, ensure it appears at least once in the resume — typically in the Skills section or woven into an existing bullet. Don't pad bullets just to fit these in.

### 6. Preserve layout; fill only content gaps

The master already carries the correct HTML structure and CSS from the blank template. When editing:

- Keep section order, classes, and styling intact
- Update the `<title>` to `Resume - <Company> - <Role>` style naming as appropriate
- Pull header contact info and Education from `personal-details.md` if the master is somehow out of date — and prefer regenerating the master over silently diverging
- Confirm concurrent / overlapping roles still carry the part-time consulting clarifier from `application-protocol.md`

The parseability rules in `.claude/skills/resume-toolkit/reference/formatting-guide.md` still apply (single column, no icons, no layout tables, no header-region contact info). Don't add anti-parser elements when extending the HTML.

### 7. Length and pruning

- Target two pages for senior candidates (10+ years experience)
- Reverse-chronological
- Roles older than 10 years: condense to a "Previous Experience" line block without bullets
- Consulting: apply the consulting protocol from `.claude/skills/resume-toolkit/reference/application-protocol.md` (consolidate short engagements; list 6+ month engagements with distinct scope as separate roles; clarify concurrent part-time work)
- **Write for concision up front.** Keep each bullet to roughly one line and the summary to 3-4 sentences. `.claude/skills/resume-toolkit/scripts/lint_resume.py` flags bullets over ~150 chars as sprawling and over ~220 chars as a wall of text, and a summary over ~600 chars as bloated; treat those findings as rewrite prompts, not just warnings. Dense, single-idea bullets are the main defense against a two-page resume spilling onto a third.
- Estimate length from the HTML content density (bullet counts, section sizes). Page-count verification happens at PDF-render time. If the resume runs long, the fix is cutting words here — not shrinking the CSS. The template's spacing is deliberately roomy so the page doesn't read as a wall of text; CSS tightening is `publish-resume`'s last resort (within fixed floors), never a substitute for concise writing.

## Output

One file in the job-application folder:

1. **`Resume - <Company> - <Role>.html`** — the styled HTML, copied from the selected master and tailored. Section order (inherited from the master / template):
   1. Header — Name, **stable identity headline** (from the master / manifest, not the JD title), City/Region/Country, Phone, Email, LinkedIn URL (plain text). Pull name, location, phone, email, and LinkedIn from `Work Experience/personal-details.md` if refreshing.
   2. Summary — 3-4 sentences; first sentence keeps the stable identity; subsequent sentences emphasize role-relevant capabilities and 1-2 metrics
   3. Work Experience — Reverse-chronological. `Mon YYYY - Mon YYYY` (or `Present`). Each role: title/employer, dates, location, bullets
   4. Education — Degree, Major, Institution, Graduation Year. Pull from `Work Experience/personal-details.md`.
   5. Skills — Comma-separated, organized by category, with purple-accent labels. Title this section exactly "Skills" so ATS parsers reliably detect it as a standard skills-section anchor.

Do not render the PDF from this skill — that's `publish-resume`'s job.

## Rules and constraints

- **Never invent skills, projects, or metrics.** If the user hasn't claimed it in their input, don't put it on the resume. Flag gaps for the user instead. Never add a JD-only skill on adjacency — exact-match terms in Skills must still be grounded in documented experience.
- **Keep the stable identity.** Do not paste the JD's `Target Title` into `.role-line` or the summary's identity opener.
- **Layer exact-match vs. conventional terminology.** Put exact JD phrasing in the Skills section (grounded terms only). In bullets and summary, match the employer's concepts and conventional industry terminology — do not lift distinctive multi-word JD phrases or sentence structures. Dual-format each acronym once (usually in Skills); use the short form afterward.
- **Bridge terminology when it differs.** When the master/notes use an internal term for a JD-required concept, make the mapping explicit rather than forcing reviewers to infer it or silently renaming the accomplishment.
- **Quantify or cut.** Every bullet under a recent role should have a number or a concrete outcome. Bullets without either are filler — remove or rewrite. Write metrics as numerals with units/symbols (`50%`, `$2M`, `80k req/s`), never spelled out (`fifty percent`) or vague (`many`, `significant`, `roughly half`).
- **No fluff words.** Strip "results-driven", "synergy", "rockstar", "team player". They cost space and signal nothing.
- **Don't over-tailor.** Prefer omission over forced matching. Tailor via selection, ordering, project choice, summary emphasis, and skills ordering — minimize semantic rewrites of canonical accomplishments. A resume that looks mechanically reconstructed from the JD reads as over-tuned or AI-generated; preserve high-value keyword matching while hiding the optimization process itself.
- **Output the full resume, not a diff.** Even for an update, produce the complete final document so the user can replace their working copy.
- **Apply the AI-sounding patterns rules from `.claude/skills/resume-toolkit/reference/formatting-guide.md`.** That section is the source of truth for em-dashes, puffery on well-known entities, AI-favorite verbs ("leveraged", "utilized", "spearheaded"), tricolon openers, fast-paced-landscape framings, adjective stacking, and JD phrase echoing. A resume that reads as AI-written gets discarded.

## Gotchas

- **The selected master is the sanctioned baseline; prior tailored resumes are not.** Take *layout* from the master (which itself came from the blank template) and take *experience content that must change* from the `Work Experience/` notes. Do not pattern-match off a recent resume in another job-application folder. Those reflect the rules **and the user's experience notes** as they existed at the time, and the user evolves all of them. Anchoring on a prior tailored artifact silently inherits its drift: not just stale formatting but **stale content** — superseded bullet wording, metrics that have since been corrected, missing roles, and — under the old flow — JD titles copied into the identity. A prior tailored resume is a last-resort fallback only, used per the precedence rule in `.claude/skills/resume-toolkit/reference/application-protocol.md` when a canonical source is genuinely missing something.
- **If the master itself is wrong, regenerate it.** Fix the note or template, run `generate-master-resumes`, then re-tailor. Do not permanently fork experience content only inside one job folder.


## Self-check before returning

Content:
- [ ] Stable identity headline from the selected master / manifest appears in `.role-line` and the summary opener — **not** the JD's `Target Title`
- [ ] Selected master is named in the chat response (which master, why)
- [ ] Every Required Skill the user genuinely has is covered (exact JD phrasing in Skills; conventional terminology in bullets) — no JD-only skills added on adjacency
- [ ] Top 3-5 required concepts are embedded in recent-role bullets with metrics
- [ ] No distinctive JD phrases or sentence structures echoed in bullets/summary (check the signal report's `Distinctive JD Phrases` denylist)
- [ ] Terminology bridges are explicit where the master/notes use an internal term for a JD-required concept
- [ ] Canonical master bullet wording preserved where selection/reordering already covers the requirement — no unnecessary semantic rewrites
- [ ] Every required per-skill minimum from `Minimum Years of Experience` is backed by the keyword appearing across dated roles whose durations sum to at least the minimum (not just in the Skills section); minimums the user can't truthfully reach are flagged as gaps, not faked
- [ ] Date format is identical across every role (no mixed styles that would break the parser's duration math)
- [ ] Overlapping roles still carry a part-time / consulting clarifier
- [ ] All metrics are numerals with units/symbols (`50%`, `$2M`), never spelled out or vague (`fifty percent`, `many`, `significant`)
- [ ] All Implicit Industry Expectations appear at least once
- [ ] Each acronym is dual-formatted once (expanded + acronym, usually in Skills); subsequent mentions use one form only — no repeated expansions
- [ ] Dates are `Mon YYYY` format throughout
- [ ] No placeholder tokens (`[FULL NAME]`, `[City, Region, ...]`, etc.) remain from the template
- [ ] No em-dashes (`—`) anywhere; no other AI-sounding patterns from `.claude/skills/resume-toolkit/reference/formatting-guide.md` (puffery on well-known entities, "leveraged"/"utilized" verbs, tricolons, negation-reversal antithesis like "not just X but Y" / "it's not X, it's Y", fast-paced-landscape framings, adjective stacking, JD phrase echoing)
- [ ] No semicolons in bullets (split the ideas or use a comma/period)
- [ ] Summary anchors on 1-2 standout metrics (numerals, role-relevant), not zero and not a stats dump (per `formatting-guide.md` Professional Summary rules)
- [ ] Bullets read at ~one line and the summary at 3-4 sentences; nothing sprawls into a wall of text (`.claude/skills/resume-toolkit/scripts/lint_resume.py` reports zero length findings)
