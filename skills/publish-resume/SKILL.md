---
name: publish-resume
description: Render a resume HTML to an ATS-parseable PDF via the bundled converter, verify page count, and run the Notepad parseability test. Trigger when the user wants to publish, render, export, finalize, or produce the PDF of a resume HTML that has already been reviewed and approved.
---

# Publish Resume

Convert a resume HTML into a final PDF that is both visually polished and ATS-parseable. Run this only after the user has approved the HTML content.

## When to use

- User says "publish", "render", "export to PDF", "finalize", "produce the PDF" for a resume HTML
- The HTML is final and the user is ready to ship

## Inputs

- **Required:** Path to the styled resume HTML file (e.g., `Job Applications/<Company>/<Role>/Resume - <Company> - <Role>.html`)
- **Bundled converter:** `.claude/skills/resume-toolkit/scripts/md_resume_to_pdf.py` (HTML → PDF via headless Chromium; also handles `.md` input via xhtml2pdf for the bare ATS variant)
- **Reference:** `.claude/skills/resume-toolkit/reference/formatting-guide.md` (parseability rules used to interpret the Notepad test)

Prerequisites are already installed in this workspace: `playwright` + `chromium`, `xhtml2pdf`, `markdown`, `pypdf`.

## Process

### 1. Confirm readiness
Before rendering, confirm the user considers the HTML final. If they haven't reviewed it (e.g., they're rendering a hand-edited draft they haven't audited), briefly flag that they may want to run `review-resume` first, then proceed if they confirm.

### 2. Render the PDF
Run the bundled converter. The script auto-dispatches on extension: `.html` goes through Playwright/Chromium, `.md` goes through xhtml2pdf.

```
python .claude/skills/resume-toolkit/scripts/md_resume_to_pdf.py "Job Applications/<Company>/<Role>/Resume - <Company> - <Role>.html" "Job Applications/<Company>/<Role>/Resume - <Company> - <Role>.pdf"
```

Expect `OK -> <pdf>` and exit 0. If the converter errors, surface the message verbatim — do not try to work around it by hand-editing the HTML structure unless the user asks.

### 3. Verify page count and parseability (Notepad test)
Extract the PDF text and confirm reading order, section order, page count, and that there are zero replacement characters (U+FFFD):

```python
import pypdf
r = pypdf.PdfReader("<output>.pdf")
print("pages:", len(r.pages))
print("\n".join(p.extract_text() for p in r.pages))
```

Check:
- Page count is 2 for senior candidates (10+ years), or 1 for candidates with under 3 years
- Extracted text is in correct reading order (header → summary → experience → education → competencies)
- Dates render as `Mon YYYY` (not garbled, not split across lines)
- Zero U+FFFD replacement characters
- No raw HTML or CSS tokens leaked into the text layer

### 4. Fix oversize — content first, CSS last
If the rendered PDF is 3 pages when it should be 2 (or 2 pages when it should be 1), fix it in this order. A resume should earn its length by being concise, not by being crammed into a smaller font — cramming is what produces the wall-of-text look the template is tuned to avoid.

1. **Tighten content first (strongly preferred).** Kick back to `build-targeted-resume` — or ask the user — to shorten the text: cut the longest bullets to a single line, drop the weakest bullet from the most-bulleted role, trim the summary toward 3 sentences, and remove low-signal qualifiers. Running `python .claude/skills/resume-toolkit/scripts/lint_resume.py "<html>"` points straight at what to cut: the `bullet-too-long`, `bullet-over-ideal`, and `summary-too-long` findings are the over-length offenders. A 3-page resume should almost always be fixed here.
2. **CSS tightening — last resort, near-misses only.** If the content is already tight and the overflow is just a few lines, nudge the `<style>` block. Never go below the template's floors:
   - body `font-size`: 10pt → down to **9.5pt** (floor)
   - `line-height`: 1.4 → down to **1.25** (floor)
   - `section` / `.entry` / `h2` margins, and `ul.bullets li` margin down to **2px** (floor)

Re-render and re-verify. Apply at most one CSS pass. If it's still oversized after that, stop and kick back to the user: recommend content cuts via `build-targeted-resume` rather than shrinking past the floors. Don't silently delete bullets here — content changes belong upstream.

### 5. Bare ATS variant (optional)
If the user explicitly wants the bare ATS-only variant (plain markdown, no styling, single-column), generate the `.md` source from the HTML and run the converter on that instead. The same script handles both inputs.

### 6. Report
Tell the user:
- The PDF output path
- The page count
- That the Notepad test passed (or, if not, what failed and what was tightened)
- Any remaining concerns the user should eyeball (e.g., a borderline 2-page result that might overflow on a different Chromium version)

## Output

One file in the job-application folder:

1. **`Resume - <Company> - <Role>.pdf`** — produced by running `.claude/skills/resume-toolkit/scripts/md_resume_to_pdf.py` on the HTML. Real text layer in DOM order, ATS-parseable, page count matches seniority target.

## Rules and constraints

- **Do not edit resume content.** This skill only renders and verifies. Wording, bullet, and structural changes belong to `build-targeted-resume`. The only edits permitted here are CSS adjustments in the HTML's `<style>` block to fit page targets, and only after the user has approved the content. When a resume is oversized, prefer content concision (upstream) over CSS tightening, and never tighten CSS below the floors in step 4.
- **Do not invent fixes for converter errors.** If `md_resume_to_pdf.py` fails, surface the error and stop. Don't try to substitute an alternative rendering path without asking.
- **Notepad test is non-negotiable.** A pretty PDF that doesn't parse cleanly is worse than a plain one that does. If the test surfaces replacement characters or wrong reading order, do not declare success — investigate.

## Self-check before returning

- [ ] Ran `.claude/skills/resume-toolkit/scripts/md_resume_to_pdf.py` and got `OK -> <pdf>` (exit 0)
- [ ] PDF page count matches the target (2 for senior, 1 for under 3 years)
- [ ] Notepad test: extracted text in correct reading order, zero U+FFFD characters
- [ ] If oversized, tried content concision (upstream) before CSS; any CSS tightening stayed within the step-4 floors (font 9.5pt, line-height 1.25, margins 2px)
- [ ] If CSS was tightened, noted the change in the user-facing report so the user can roll it back if they want
- [ ] Reported the PDF path, page count, and parseability result to the user
