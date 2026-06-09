# Resume Formatting Guide

Normative rules for producing an ATS-parseable, recruiter-friendly resume. Used by `build-targeted-resume` (to apply) and `review-resume` (to check).

## Primary considerations, in priority order

1. **Parseability.** If an ATS can't extract the right text into the right fields, nothing else matters. Single-column, standard headers, MM/YYYY dates, plain text contact info.
2. **Coverage.** Every required skill from the target JD must appear at least once, in context.
3. **Recruiter skimmability.** Most reviewers spend under 15 seconds on page one. Top of page one must contain the title mirror, the most recent role's first bullet, and the strongest 5 skills.
4. **Density without fluff.** A senior resume's signal-to-noise ratio matters more than its length. Quantified bullets, no buzzwords, no padding.

## File format

- **Text-based PDF or DOCX are both reliable in 2026.** Either works for any major ATS.
- **Never submit image-based or scanned PDFs.** No extractable text layer = universal parse failure.
- DOCX is the more conservative choice if you suspect an unusually old ATS deployment. PDF preserves visual fidelity across machines, which helps the human reader.
- Test before submitting: copy all text from the PDF/DOCX, paste into a plain text editor. If the reading order is scrambled, spaces are missing, or sections are interleaved, the file will fail an ATS scan.

## Layout rules (hard requirements)

- **Single column only.** Multi-column layouts get read left-to-right across the page, fusing unrelated content. Non-negotiable.
- **No text boxes, layout tables, or floating elements.** Parsers either skip them or read them out of order.
- **No icons, progress bars, or star ratings.** They render as nothing (best case) or garbage characters (worst case). Icons used in place of words (e.g., a phone icon for "Phone:") drop the contextual anchor and the data after it may be lost.
- **No graphics or background images.**
- **Standard system fonts only.** Arial, Calibri, Times New Roman, Helvetica. Avoid custom or downloaded fonts — some merge letter pairs into single glyphs (`ti`, `fi`), causing the parser to read "communica on" for "communication".
- **Contact info in body text, not in the document header space.** Microsoft Word's "header" region is invisible to many parsers — putting your phone/email there creates a blank candidate profile.

## Section structure (in order)

1. **Header**
   - Full name (largest text on the page, but not gimmicky size)
   - Phone number (numbers and dashes only, no icons)
   - Email (plain text, no `mailto:` styling weirdness)
   - City, State (no full street address — privacy and irrelevance)
   - LinkedIn URL (plain text, full URL or `linkedin.com/in/handle`)
   - GitHub URL (plain text) if relevant to the role

2. **Professional Summary** (3-4 sentences)
   - Sentence 1: Mirror the exact target job title + years of experience + core identity. Example: "Senior AI Engineer with 12 years of experience building distributed systems and production ML infrastructure."
   - Sentence 2-3: Specific high-signal capabilities tied to the role.
   - Sentence 4 (optional): Notable scope/scale or industry context.
   - No fluff. No "results-driven, passionate professional". No objective statement ("Seeking a role where...") — it's outdated and centers what you want, not what you bring.
   - **Anchor the summary with one — at most two — of your strongest, most role-relevant metrics, then stop.** A single high-impact number in the opening establishes credibility instantly and is what the 7-second skim rewards: "Reduced hallucination rates 40%", "Cut inference cost 50%", "Scaled to 100k req/s". Make it specific and, where it lands cleanly, a delta ("from 4s to 800ms"), not a vague claim ("significantly improved"). One or two is the ceiling. A summary *stacked* with metrics — "serving 200 organizations at 100k requests/day, driving a 30% latency reduction across..." — reads as a stats dump and erodes the human voice; that's the failure mode to avoid. Pick the figure(s) most relevant to this JD; the remaining numbers belong in the bullets, where the full proof lives.
   - **Cap the length.** 3-4 sentences, ~50-80 words. Past ~600 characters the summary reads as a wall of text and `lint_resume.py` flags it; trim back to the essentials rather than letting it sprawl.

3. **Skills**
   - Title this section exactly "Skills" — a standard header ATS parsers reliably detect as a skills-section anchor. Avoid "Core Competencies" or other creative variants.
   - Comma-separated, organized by category
   - Standard categories for senior engineering: Languages | AI/ML Frameworks | Cloud & Infrastructure | Data & Databases | DevOps & Tooling
   - Dual-format acronyms on first mention: "Retrieval-Augmented Generation (RAG)"
   - 15-25 items total is reasonable; resist the urge to list every framework you've ever touched

4. **Professional Experience** (reverse-chronological)
   - Format per role:
     ```
     Job Title | Employer Name | City, State (or Remote)
     MM/YYYY – MM/YYYY (or Present)
     - Bullet 1: verb + skill/context + quantified outcome
     - Bullet 2: ...
     ```
   - 3-6 bullets for recent roles, 2-3 for older ones
   - Every bullet in a role from the last 5 years should have a number or a concrete outcome
   - Roles older than 10 years: condense to a "Previous Experience" block with no bullets, just titles/employers/dates

5. **Education**
   - Degree, Major, Institution, Graduation Year
   - Omit GPA after ~5 years experience unless exceptional
   - List relevant coursework only if early-career

6. **Certifications** (optional)
   - Full title + acronym: "AWS Certified Solutions Architect – Professional (AWS-SAP)"

## Date formatting (hard rules)

- **Always MM/YYYY** or "Month YYYY" (e.g., `03/2022 – Present` or `March 2022 – Present`)
- **Never** "Summer 2022", "Spring '21", "'21–'23", "2022-now"
- Use `Present` for current roles, not `Current`, `Now`, or open-ended dashes
- **Use one date format for every entry on the resume.** Mixing styles across roles (e.g., `Jan 2019 – Mar 2022` on one role, `06/2017 – 12/2018` on another, `2015 – 2017` on a third) makes the ATS's chronological calculator fail silently — it can credit a candidate with a fraction of their real tenure even when each individual date is valid. Pick `MM/YYYY` or `Month YYYY` and apply it uniformly. This directly protects the years-of-experience math, including the per-skill duration sums the parser computes (see "How to answer YOE questions" in `.claude/skills/resume-toolkit/reference/application-protocol.md`).

## Bullet quality rules

- **Start with a strong verb.** Past tense for past roles, present tense for current. (Architected, Built, Reduced, Led, Shipped, Deployed.)
- **Include the technology or context.** "Built a feature" is invisible. "Built a RAG pipeline on AWS Bedrock" is searchable.
- **End with a quantified outcome.** Percentages, time saved, latency reduced, cost saved, headcount unblocked, dollars driven.
- **Write metrics as numerals, with units or symbols.** `50%`, `$2M`, `80k req/s`, `5+ years` — never spelled out (`fifty percent`) and never a vague quantifier (`roughly half`, `many`, `significant`). Numerals extract reliably through an ATS and are what a 15-second skim catches; words and estimates get missed or read as filler. Where the data supports it, frame against a baseline or timeframe (`from 4s to 800ms`, `per quarter`, `within 90 days`) for comparability — but never invent a baseline to fit the pattern.
- **One idea per bullet.** Compound bullets dilute both human readability and keyword density.
- **Keep each bullet to about one line.** A bullet that wraps past two lines reads as a wall of text and buries the outcome. Aim for ~150 characters; treat ~220 as a hard cap. (`lint_resume.py` flags both thresholds.) Cut qualifiers and context the reader can infer.
- **Avoid semicolons.** A semicolon in a bullet almost always splices two ideas into one line — break them apart, or use a comma or period. (Semicolons are also a mild AI-prose tell, though far weaker than em-dashes.)

## Length

- 12+ years experience: **two pages**
- 3-10 years: whatever fits without cramping (often two)
- Under 3 years: one page

## Words to avoid

- **Fluff:** results-driven, synergy, rockstar, ninja, guru, go-getter, team player, passionate, dynamic, innovative
- **Outdated tech as primary skills:** jQuery, Subversion (SVN), Flash, "Web 2.0"
- **Overly broad** where specifics are expected: "Machine Learning" alone (use "RAG", "LoRA fine-tuning", etc.), "Cloud" alone (use "AWS Bedrock", "EKS", etc.)

## AI-sounding patterns to avoid

The intended reader is a senior technical hiring manager or a technical ATS (see the "Target audience and tone" section in `.claude/skills/resume-toolkit/skills/build-targeted-resume/SKILL.md` for the operating frame). Anything that signals "this was written by an LLM trying to sound impressive" works against that reader. Recruiters in 2026 actively screen for AI-generated resumes, and a flagged resume gets discarded regardless of how good the candidate is. Avoid the tells.

- **No em-dashes (`—`) anywhere in the resume.** Em-dashes are one of the strongest AI-text signals recruiters look for. Use commas, parentheses, semicolons, colons, or rephrase. Also avoid en-dashes (`–`) in prose; use a plain hyphen (`-`) for date ranges to be safe.
- **No puffery descriptions of well-known companies or products.** The reader knows what Amazon S3, AWS, Google, Meta, Stripe, etc. are. Do not write phrases like "one of the world's largest production data platforms," "industry-leading," "world-class," "best-in-class," or similar adjectival framings of well-known systems. State the work done and let the brand recognition do its own work. (This is also a fluff signal even when not strictly AI-generated — it reads as padding.)
- **No "leveraged", "utilized", "spearheaded", "orchestrated", "facilitated"** as verbs of choice. These are AI-favorite verbs because they sound senior without being specific. Use the concrete verb: "Built", "Shipped", "Cut", "Doubled", "Migrated", "Wrote".
- **No tricolon openers ("By X, Y, and Z, the team...").** The three-noun balanced clause is an AI cadence. Prefer one specific action per bullet.
- **No negation-reversal antithesis.** "Not only X but also Y", "not just X but Y", "it's not X, it's Y", "doesn't just X; it Ys", "more than just X" — the contrast-then-pivot cadence is a strong AI tell. State the affirmative claim directly: "Transforms 2TB/day of events into queryable tables", not "doesn't just store data; it transforms it".
- **No "in today's fast-paced [X] landscape" / "in the rapidly evolving world of [Y]"** framings. These are pure AI scaffolding and signal nothing.
- **No symmetrical adjective stacking ("scalable, robust, and resilient infrastructure").** Pick the one that matters and cut the rest.

## Self-test

Before submitting any resume:

1. **The Notepad test.** Copy all visible text. Paste into Notepad (or any plain text editor). If the reading order is wrong, words are merged, or sections interleave, the file will fail an ATS scan. Fix the formatting and retest.
2. **The 15-second test.** Look at page one for 15 seconds. Can you tell the target role, the seniority, and the 5 strongest skills? If not, restructure the top of the resume.
3. **The metric test.** Count bullets without numbers or concrete outcomes in the most recent two roles. If more than ~30%, rewrite.

## Starting template

For the actual fill-in skeleton, use `.claude/skills/resume-toolkit/skills/build-targeted-resume/resume-template.html`. It's the canonical structure and the only template that gets rendered by `publish-resume`.
