---
name: extract-job-signals
description: Parse a job description into a structured signal report (required skills, nice-to-haves, target title, role family, action-skill pairs, knockout questions). Trigger when the user provides a job description URL or pasted text and wants to extract what their resume should target. Writes the full report to a markdown file by default and returns only a high-level summary plus important flags in chat.
---

# Extract Job Signals

Turn a raw job description into a concise, structured report of what an applicant's resume must contain to clear ATS filters and recruiter screens for that specific role.

## When to use

- User pastes or links a job description and asks "what should my resume hit for this?"
- User is about to tailor a resume for a specific posting
- User wants to evaluate whether a role matches their experience before applying

## Inputs

- **Required:** Job description text (pasted, fetched from URL, or extracted from a file)
- **Optional:** Company name and seniority level if not obvious from the JD
- **Optional:** Reference to `.claude/skills/resume-toolkit/reference/industry-signals.md` for implicit keywords expected in the user's domain

## Process

1. **Find the target title.** Locate the canonical job title in the JD header. If multiple variants appear (e.g., "Senior AI Engineer" in the header, "Staff ML Engineer" in the apply button), prefer the apply-button/URL version — that's what the recruiter searches on. Record it as `Target Title` for terminology mapping and ATS searchability in skills/bullets. **Do not treat it as the resume headline** — `build-targeted-resume` keeps a stable professional identity from the selected master instead of copying this string into `.role-line` or the summary opener.
2. **Classify the role family.** Map the posting to a role family so `build-targeted-resume` can pick the best-fit master. If `Work Experience/resume-masters.md` exists, use its role-family / classification cues and name the closest manifest entry (or the closest purpose label). If the manifest is missing, infer a short family label from the JD (e.g., "AI / Platform", "Backend", "Full-stack", "Data / ML") and note that masters were unavailable. Record the result as `Role Family`.
3. **Extract Required Skills.** Pull every hard skill, technology, framework, methodology, and certification listed under "Requirements" / "Must-Haves" / "Qualifications". These drive knockout filters and primary ATS search queries.
4. **Extract Nice-to-Haves.** Pull every skill under "Preferred" / "Bonus" / "Nice-to-have". These act as tie-breakers in ranking.
5. **Build Action-Skill Pairs.** Scan the "Responsibilities" section for verb-skill pairs (e.g., "Deploy RAG pipelines" → `deploy + RAG`). These tell the resume builder what verb-context to wrap each keyword in.
6. **Capture Distinctive JD Phrases.** Pull multi-word phrasings and sentence structures unique to this posting (marketing-y role blurbs, idiosyncratic stacks of requirements, house jargon) into `Distinctive JD Phrases (do not echo)`. The builder uses this as a denylist for bullets/summary so the resume does not look reconstructed from the JD.
7. **Extract minimum years of experience.** Capture *every* explicit minimum-experience requirement as a separate line item, not a single lumped number: the overall career minimum *and* each skill- or domain-specific minimum (e.g., "5+ years Python", "3+ years Kubernetes", "2+ years leading teams"). For each, record the exact skill phrasing from the JD and the number. This matters because ATS compute skill-specific experience by summing the dated work-history roles where that keyword appears — a skill the resume lists only in a Skills section is credited with **zero** years. The downstream build skill needs each minimum itemized so it can place the keyword in enough dated roles to clear the math. Capture soft/preferred minimums ("ideally 5+ years", "bonus: 3+ years GraphQL") too, but tag them `preferred` so they aren't treated as knockouts.
8. **Identify Likely Knockout Questions.** Flag anything that will likely appear as a yes/no form filter: visa sponsorship, location/remote, security clearance, specific YOE thresholds, degree requirements, on-call willingness.
9. **Cross-reference industry signals.** Read `.claude/skills/resume-toolkit/reference/industry-signals.md`. List any implicit-but-expected keywords for this role type that are NOT in the JD but recruiters will search for anyway (e.g., a senior SWE role implicitly expects "system design" even if unstated).
10. **Note red flags.** Anything in the JD that suggests poor fit, unrealistic scope, or potential filter mismatches with the user's background.
11. **Write the report to a markdown file.** By default, save the full report to a `Signal Report - <Company> - <Job Title>.md` file alongside the job description (typically in the same `Job Applications/<Company>/<Job Title>/` directory the JD came from). Only skip the file and respond inline if the user explicitly asked for the report in chat or there is no obvious directory to write to.

## Output destination

The full structured report is a **file artifact, not a chat dump.** Write it to disk by default (see Process step 11), then keep your chat response short:

- A 1–3 sentence high-level summary (role fit, what the resume must lead with).
- Any important flags — knockout risks, mismatches, or anything the user must act on before applying.
- A pointer to the saved file path.

Do **not** paste the entire report back into the conversation when you've written it to a file. The file is the deliverable; the chat response is the briefing.

## Output format

The file must contain these sections, in this order:

```markdown
# Signal Report: <Job Title> at <Company>

## Target Title
<Exact JD title string. For terminology mapping and ATS searchability in skills/bullets — not for the resume headline or summary identity.>

## Role Family
<Closest master name or purpose from Work Experience/resume-masters.md when available; otherwise a short inferred family label. Used by build-targeted-resume to select the baseline master.>

## Required Skills
<Comma-separated list. Use exact JD phrasing — this list feeds the Skills section (exact-match ATS layer), not verbatim reuse in bullets. For acronyms, include both forms once: "Retrieval-Augmented Generation (RAG)".>

## Nice-to-Have Keywords
<Comma-separated list.>

## Action-Skill Pairs
- <verb> <skill/object> — e.g., "Deploy RAG pipelines", "Optimize SQL queries"

## Distinctive JD Phrases (do not echo)
<Multi-word phrasings and sentence structures unique to this posting. The builder must not copy these verbatim into bullets or summary — exact terms belong in Skills when grounded; bullets match concepts with conventional terminology.>
- <phrase>
- <phrase>

## Implicit Industry Expectations
<Keywords not in the JD but expected for this role type. Source: industry-signals.md.>

## Minimum Years of Experience
List every explicit minimum-experience requirement as its own line, tagged `required` or `preferred`. The build skill maps each one to dated roles, so keep the skill phrasing exact and the number explicit.
- Overall: <N> years (required | preferred)
- Per skill / domain:
  - <skill, exact JD phrasing>: <N>+ years (required | preferred)
  - <skill>: <N>+ years (required | preferred)
- If the JD states only an overall minimum and no per-skill minimums, say so explicitly: "No per-skill minimums stated."

## Likely Knockout Questions
- <Each likely yes/no form filter>

## Notes / Red Flags
<Anything notable: unusual scope, mismatch with user profile, vague requirements.>
```

## Rules and constraints

- **Use exact JD phrasing for keywords.** Recruiter searches are often literal. If the JD says "Kubernetes," don't substitute "K8s" — list both if you must. Exact phrasing in this report is destined for the Skills section (exact-match layer), not for verbatim reuse in experience bullets.
- **Dual-format acronyms once** in the report (e.g., "Retrieval-Augmented Generation (RAG)"). The downstream resume expands each acronym once (usually in Skills) and uses one form afterward.
- **Capture distinctive phrases as a denylist.** Put multi-word phrasings and sentence structures unique to this posting under `Distinctive JD Phrases (do not echo)` so the builder does not reconstruct the resume in the JD's voice.
- **Don't invent skills.** If the JD doesn't mention it and industry-signals.md doesn't flag it as implicit, leave it out.
- **Don't editorialize.** This skill produces signals, not advice. The Build and Review skills decide how to act on them.
- **Cap each section reasonably.** Required Skills typically 8-15 items; Nice-to-Haves 3-8; Action-Skill Pairs 5-10; Distinctive Phrases 3-8. If the JD has more, prioritize by frequency and section weight (Requirements > Responsibilities > About You).

## What NOT to do

- Don't include behavioral fluff ("results-driven", "team player") even if the JD uses it. It's noise.
- Don't try to write resume bullets here — this is signal extraction only.
- Don't apply formatting rules — those belong in the Build/Review skills via `.claude/skills/resume-toolkit/reference/formatting-guide.md`.
