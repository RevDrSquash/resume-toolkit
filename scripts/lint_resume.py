"""Detect AI-sounding patterns in a generated resume.

Reads a resume file (HTML or Markdown) and reports deterministic matches
against the patterns enumerated in `.claude/skills/resume-toolkit/reference/formatting-guide.md`
(the "AI-sounding patterns to avoid" and "Words to avoid" sections).

Also runs HTML-only length checks: an over-long summary, and bullets past
their ideal/maximum length (the wall-of-text guard). See the length
threshold constants below.

Intended use: called by the `review-resume` skill before the model runs
its checklist pass, so it can fold the deterministic findings into its
prioritized critique.

Usage:
    python .claude/skills/resume-toolkit/scripts/lint_resume.py "<path-to-resume.html or .md>"
    python .claude/skills/resume-toolkit/scripts/lint_resume.py "<path>" --format json

Exit code is always 0 (informational). The output is the source of truth
for the number of issues found.
"""

import argparse
import html as _html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Pattern


# ---------------------------------------------------------------------------
# Length thresholds (characters)
# ---------------------------------------------------------------------------
# Measured in characters, not words: character count tracks how many physical
# lines an element wraps to on the page, which is what creates a "wall of
# text". (Words mis-rank dense technical bullets — "Retrieval-Augmented
# Generation" is one idea but three long tokens.) The template renders body
# text at 10pt across a ~7.1in content column, so a line holds ~100 chars.
#
#   SUMMARY_MAX_CHARS   ~90 words / well above the 50-80 word target, so it
#                       only fires on genuinely bloated summaries.
#   BULLET_IDEAL_CHARS  ~1.5 lines / ~22 words. Bullets read best at ~1 line;
#                       past this they start to sprawl (minor nudge).
#   BULLET_MAX_CHARS    past ~2 lines / ~33 words. This is the wall-of-text
#                       threshold (material).
SUMMARY_MAX_CHARS = 600
BULLET_IDEAL_CHARS = 150
BULLET_MAX_CHARS = 220


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    severity: str  # "critical" | "material" | "minor"
    why: str
    fix: str
    pattern: Optional[Pattern] = None  # None for non-regex (length) rules


RULES: List[Rule] = [
    Rule(
        name="em-dash",
        severity="critical",
        pattern=re.compile(r"[—―]"),  # — and ―
        why=(
            "Em-dashes are one of the strongest AI-text signals recruiters "
            "screen for. A resume flagged as AI-written is often discarded."
        ),
        fix=(
            "Replace with a comma, colon, parentheses, or rephrase. "
            "For date ranges, use a plain hyphen (-)."
        ),
    ),
    Rule(
        name="en-dash-in-prose",
        severity="minor",
        pattern=re.compile(r"[–]"),  # –
        why=(
            "En-dashes in prose are another AI-text tell. The formatting "
            "guide asks for plain hyphens (-) even in date ranges."
        ),
        fix="Replace with a plain hyphen (-).",
    ),
    Rule(
        name="excessive-colons",
        severity="material",
        # Two or more colons on a single non-empty line, where each segment
        # has substantive text. Excludes plain skills-category lines like
        # "Languages: Python, Go" (single colon) but catches the AI cadence
        # "Optimization: Database: Reduced load time".
        pattern=re.compile(
            r"^(?!\s*$)[^:\n]{1,60}:\s*[^:\n]{1,60}:\s*[^:\n]+$",
            re.MULTILINE,
        ),
        why=(
            "Compartmentalized 'Topic: Sub-topic: Outcome' phrasing on a "
            "single line is an AI cadence. Humans usually write flowing "
            "bullets with one idea per line."
        ),
        fix=(
            "Rewrite as a single coherent sentence: action verb + technology "
            "+ quantified outcome."
        ),
    ),
    Rule(
        name="ai-favorite-verb",
        severity="material",
        pattern=re.compile(
            r"\b(leveraged|leveraging|utilized|utilizing|spearheaded|"
            r"orchestrated|facilitated|delved|navigated|fostered|catalyzed|"
            r"synergized|synergised)\b",
            re.IGNORECASE,
        ),
        why=(
            "AI-favorite verbs sound senior without being specific. "
            "Recruiters screening for AI-generated resumes flag them on sight."
        ),
        fix=(
            "Use a concrete verb tied to the actual work: Built, Shipped, "
            "Cut, Doubled, Migrated, Wrote, Reduced, Led, Architected."
        ),
    ),
    Rule(
        name="grandiose-adjective",
        severity="material",
        pattern=re.compile(
            r"\b(robust|seamless|seamlessly|meticulous|meticulously|tapestry|"
            r"unparalleled|cutting[- ]edge|state[- ]of[- ]the[- ]art|"
            r"bleeding[- ]edge|next[- ]generation|holistic|comprehensive "
            r"(?:suite|solution|approach|understanding))\b",
            re.IGNORECASE,
        ),
        why=(
            "Grandiose adjectives are AI puffery. They consume space and "
            "signal nothing concrete."
        ),
        fix=(
            "Cut the adjective, or replace with the specific metric that "
            "proves the claim."
        ),
    ),
    Rule(
        name="puffery-on-known-entity",
        severity="material",
        pattern=re.compile(
            r"\b("
            r"one of the (?:world's|largest|leading|biggest)|"
            r"world's (?:largest|leading|biggest|most)|"
            r"industry[- ]leading|"
            r"best[- ]in[- ]class|"
            r"world[- ]class|"
            r"market[- ]leading"
            r")\b",
            re.IGNORECASE,
        ),
        why=(
            "Don't describe well-known companies, products, or platforms "
            "with superlatives. The reader already knows the brand."
        ),
        fix=(
            "State the work done and let the brand recognition do its own "
            "work. e.g., 'Shipped X at Stripe' not 'industry-leading payments "
            "platform Stripe'."
        ),
    ),
    Rule(
        name="antithesis-cadence",
        severity="material",
        # The contrast-pivot cadence AI defaults to: set up one side, then
        # swing to the other. Covers the additive correlative ("not only X
        # but also Y") and the corrective negation-reversal ("not just X but
        # Y", "doesn't just X; it Ys", "it's not X, it's Y", "more than just
        # X", "not about X but about Y"). [^.\n] keeps each match in one line.
        pattern=re.compile(
            r"(?:"
            r"\bnot only\b[^.\n]{1,80}?\bbut also\b"
            r"|"
            r"\bnot just\b[^.\n]{1,60}?\b(?:but|yet)\b"
            r"|"
            r"\b(?:does(?:n['’]t| not)|do(?:n['’]t| not)|is(?:n['’]t| not)|"
            r"are(?:n['’]t| not)|was(?:n['’]t| not)|were(?:n['’]t| not)|"
            r"won['’]t|wo n['’]t)\s+just\b[^.\n]{1,70}?[;,]\s*"
            r"(?:it|they|we|this|that|the)\b"
            r"|"
            r"\b(?:it['’]s|that['’]s|this is)\s+not\b[^.\n]{1,60}?[,;]\s*"
            r"(?:it['’]s|that['’]s|but|they['’]re|rather)\b"
            r"|"
            r"\bmore than just\b"
            r"|"
            r"\b(?:not|isn['’]t|aren['’]t)\s+about\b[^.\n]{1,60}?"
            r"\b(?:but|it['’]s)\s+about\b"
            r")",
            re.IGNORECASE,
        ),
        why=(
            "The contrast-pivot cadence ('not only X but also Y', 'not just X "
            "but Y', 'doesn't just X; it Ys', 'it's not X, it's Y', 'more than "
            "just X') is a strong, formulaic AI tell."
        ),
        fix=(
            "Drop the setup and state the affirmative claim directly with a "
            "verb and a metric. 'Doesn't just store data; it transforms it' -> "
            "'Transforms 2TB/day of raw events into queryable tables'."
        ),
    ),
    Rule(
        name="semicolon",
        severity="minor",
        # Any semicolon in resume body text. Weakly associated with AI prose,
        # but the stronger reason to flag it: a semicolon almost always joins
        # two independent clauses, i.e. two ideas crammed into one bullet,
        # which breaks the one-idea-per-bullet rule. CSS/inline-style
        # semicolons never reach here (style/script and tags are stripped
        # before matching).
        pattern=re.compile(r";"),
        why=(
            "Semicolons rarely belong on a resume: they usually fuse two ideas "
            "into one bullet (breaking one-idea-per-bullet), and they read as "
            "an AI-prose tell to some recruiters."
        ),
        fix=(
            "Split into two bullets, or replace with a comma or period. If the "
            "semicolon separates list items, use commas."
        ),
    ),
    Rule(
        name="fast-paced-landscape",
        severity="material",
        pattern=re.compile(
            r"\b(in (?:today's|the) )?"
            r"(ever[\s-]evolving|fast[\s-]paced|rapidly evolving|"
            r"ever[\s-]changing|dynamic|complex)\b"
            r"[^.\n]{0,40}?"
            r"\b(landscape|world|industry|field|environment|ecosystem)\b",
            re.IGNORECASE,
        ),
        why=(
            "'In today's fast-paced [X] landscape' framings are pure AI "
            "scaffolding and signal nothing."
        ),
        fix="Delete the framing. Open with the specific action or claim.",
    ),
    Rule(
        name="a-testament-to",
        severity="minor",
        pattern=re.compile(r"\ba testament to\b", re.IGNORECASE),
        why="'A testament to' is a formulaic AI flourish.",
        fix="State the concrete result directly.",
    ),
    Rule(
        name="delivering-unparalleled",
        severity="material",
        pattern=re.compile(
            r"\bdeliver(?:ing|ed|s)?\s+(?:unparalleled|exceptional|"
            r"outstanding|world[- ]class|best[- ]in[- ]class|"
            r"unmatched|superior)\b",
            re.IGNORECASE,
        ),
        why="'Delivering unparalleled X' is empty AI puffery.",
        fix=(
            "Replace with the metric: 'cut p95 latency 40%', 'doubled "
            "throughput', 'reduced infra cost $80k/yr'."
        ),
    ),
    Rule(
        name="equipped-with-comprehensive",
        severity="material",
        pattern=re.compile(
            r"\bequipped with (?:a )?comprehensive\b",
            re.IGNORECASE,
        ),
        why="'Equipped with a comprehensive [X]' is AI scaffolding.",
        fix="Name the specific skills or tools and what was built with them.",
    ),
    Rule(
        name="fluff-word",
        severity="material",
        pattern=re.compile(
            r"\b("
            r"results[- ]driven|"
            r"results[- ]oriented|"
            r"synergy|synergies|synergistic|"
            r"rockstar|"
            r"ninja|"
            r"guru|"
            r"go[- ]getter|"
            r"team player|"
            r"passionate (?:professional|developer|engineer|leader)?|"
            r"dynamic (?:professional|individual|leader)|"
            r"innovative (?:thinker|professional)|"
            r"highly motivated|"
            r"detail[- ]oriented|"
            r"self[- ]starter|"
            r"hard[- ]working|"
            r"thinks outside the box"
            r")\b",
            re.IGNORECASE,
        ),
        why="Fluff words signal nothing and consume space.",
        fix="Cut, and replace with a specific quantified outcome.",
    ),
    Rule(
        name="tricolon-opener",
        severity="minor",
        # Matches bullet/sentence starts with "By/Through/With/Using X, Y,
        # and Z, ..." — the three-noun balanced clause that AI defaults to.
        pattern=re.compile(
            r"(?:^|[\n•\-\*]\s*)"
            r"(?:By|Through|With|Using|Leveraging|Combining)\s+"
            r"\w[\w\s/&-]*?,\s+"
            r"\w[\w\s/&-]*?,?\s+and\s+"
            r"\w[\w\s/&-]*?,",
            re.IGNORECASE,
        ),
        why=(
            "Tricolon openers ('By X, Y, and Z, ...') are an AI cadence. "
            "Prefer one specific action per bullet."
        ),
        fix="Drop the three-noun preamble. Start with the verb.",
    ),
    Rule(
        name="symmetrical-adjective-stack",
        severity="minor",
        pattern=re.compile(
            r"\b(scalable|robust|resilient|reliable|secure|efficient|"
            r"performant|maintainable|extensible|flexible|modular),\s+"
            r"\w+(?:\s+\w+)?,?\s+and\s+"
            r"(scalable|robust|resilient|reliable|secure|efficient|"
            r"performant|maintainable|extensible|flexible|modular)\b",
            re.IGNORECASE,
        ),
        why=(
            "Symmetrical adjective stacking ('scalable, robust, and "
            "resilient') is an AI cadence."
        ),
        fix=(
            "Pick the one adjective that matters, cut the rest, or replace "
            "with the specific metric."
        ),
    ),
    Rule(
        name="outdated-tech",
        severity="minor",
        # Only flag if appearing as a standalone skill (preceded by comma /
        # start of line / colon / bullet). Avoids false positives in prose
        # like "migrated off jQuery".
        pattern=re.compile(
            r"(?:^|[,:;•\-\*]\s*)"
            r"(jQuery|Subversion|SVN|Flash|Web 2\.0|Silverlight|"
            r"CoffeeScript|AngularJS)\b",
            re.IGNORECASE,
        ),
        why=(
            "Outdated tech listed as a headline skill dates the candidate "
            "and crowds out current keywords."
        ),
        fix=(
            "Remove from Skills, or relegate to a 'legacy migrations' bullet "
            "if you migrated off it."
        ),
    ),
]


# Synthetic rules for the length checks. They carry no regex pattern; findings
# are produced structurally by lint_lengths() rather than by pattern matching.
_RULE_SUMMARY_LONG = Rule(
    name="summary-too-long",
    severity="material",
    why=(
        f"The summary runs past {SUMMARY_MAX_CHARS} characters (~90 words). A "
        "summary that long reads as a wall of text; the target is 3-4 "
        "sentences / 50-80 words."
    ),
    fix=(
        "Cut to 3-4 sentences. Keep the identity headline, 3-5 keywords, and 1-2 "
        "standout metrics; move everything else into the bullets."
    ),
)
_RULE_BULLET_LONG = Rule(
    name="bullet-too-long",
    severity="material",
    why=(
        f"The bullet runs past {BULLET_MAX_CHARS} characters (~2 lines / ~33 "
        "words). Bullets this long become a wall of text and bury the outcome."
    ),
    fix=(
        "Cut to one idea. Lead with the verb, name the tech, end on the "
        "metric; drop qualifiers and context the reader can infer."
    ),
)
_RULE_BULLET_OVER_IDEAL = Rule(
    name="bullet-over-ideal",
    severity="minor",
    why=(
        f"The bullet runs past {BULLET_IDEAL_CHARS} characters (~1.5 lines). "
        "Bullets read best at roughly one line; this one is starting to sprawl."
    ),
    fix="Tighten toward a single line: trim filler words and redundant context.",
)


# ---------------------------------------------------------------------------
# HTML → text conversion
# ---------------------------------------------------------------------------

_BLOCK_CLOSERS = re.compile(
    r"</(p|li|h[1-6]|div|section|tr|td|th|article|header|footer|main|aside|"
    r"nav|ul|ol|table|thead|tbody|dl|dd|dt|blockquote|pre)\s*>",
    re.IGNORECASE,
)
_BR_TAG = re.compile(r"<br\s*/?>", re.IGNORECASE)
_STYLE_OR_SCRIPT = re.compile(
    r"<(style|script)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_ANY_TAG = re.compile(r"<[^>]+>")


def html_to_text(content: str) -> str:
    """Strip HTML, preserving one logical line per block element."""
    # Drop comments and <style>/<script> contents entirely — none of it is
    # part of the rendered resume, so it must not be linted.
    content = _HTML_COMMENT.sub("", content)
    content = _STYLE_OR_SCRIPT.sub("", content)
    # Block-level closers and <br> become newlines.
    content = _BLOCK_CLOSERS.sub("\n", content)
    content = _BR_TAG.sub("\n", content)
    # Strip every remaining tag.
    content = _ANY_TAG.sub("", content)
    # Decode entities.
    content = _html.unescape(content)
    # Normalize whitespace within each line; drop empty lines.
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in content.splitlines()]
    return "\n".join(line for line in lines if line)


# ---------------------------------------------------------------------------
# Finding collection
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    rule: Rule
    line_number: int
    matched_text: str
    line_excerpt: str


def lint(text: str) -> List[Finding]:
    findings: List[Finding] = []
    # Precompute line offsets for fast line-number lookup.
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)

    def offset_to_line(offset: int) -> int:
        # Binary search would be fine; linear is plenty for resume lengths.
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1  # 1-indexed

    def line_at(line_number: int) -> str:
        start = line_starts[line_number - 1]
        end = line_starts[line_number] - 1 if line_number < len(line_starts) else len(text)
        return text[start:end]

    for rule in RULES:
        for match in rule.pattern.finditer(text):
            # Some patterns anchor on a preceding newline or bullet char.
            # Advance past leading whitespace so the line number reflects
            # the line the actual matched content sits on.
            start = match.start()
            while start < len(text) and text[start] in " \t\n\r":
                start += 1
            line_number = offset_to_line(start)
            excerpt = line_at(line_number).strip()
            # Trim very long lines so the report stays readable.
            if len(excerpt) > 200:
                rel = start - line_starts[line_number - 1]
                lo = max(0, rel - 80)
                hi = min(len(excerpt), rel + 120)
                excerpt = ("..." if lo > 0 else "") + excerpt[lo:hi] + ("..." if hi < len(excerpt) else "")
            findings.append(
                Finding(
                    rule=rule,
                    line_number=line_number,
                    matched_text=match.group(0).strip(),
                    line_excerpt=excerpt,
                )
            )
    return findings


# Length checks read the raw HTML so they can target specific elements by
# class (.summary, ul.bullets li). They're HTML-only: the styled HTML is the
# real deliverable, and a Markdown bullet/summary can't be told apart from a
# skills line without the class hooks. Regex rules above still run on Markdown.
_SUMMARY_BLOCK = re.compile(
    r'<p[^>]*class="[^"]*\bsummary\b[^"]*"[^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)
_BULLETS_UL = re.compile(
    r'<ul[^>]*class="[^"]*\bbullets\b[^"]*"[^>]*>(.*?)</ul>',
    re.IGNORECASE | re.DOTALL,
)
_LI_ITEM = re.compile(r"<li[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)


def _element_text(inner_html: str) -> str:
    """Inner HTML -> clean visible text (tags stripped, entities decoded)."""
    text = _ANY_TAG.sub("", inner_html)
    text = _html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def lint_lengths(raw: str, suffix: str) -> List[Finding]:
    """Flag over-long summary and bullets in the raw HTML."""
    if suffix not in {".html", ".htm"}:
        return []

    findings: List[Finding] = []
    # Blank out comments (keeping length so offsets still map to source lines)
    # so commented-out example markup isn't measured.
    raw = _HTML_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw)

    def line_of(offset: int) -> int:
        return raw.count("\n", 0, offset) + 1

    def excerpt(text: str) -> str:
        return text if len(text) <= 200 else text[:197] + "..."

    for m in _SUMMARY_BLOCK.finditer(raw):
        text = _element_text(m.group(1))
        if len(text) > SUMMARY_MAX_CHARS:
            findings.append(
                Finding(
                    rule=_RULE_SUMMARY_LONG,
                    line_number=line_of(m.start()),
                    matched_text=f"{len(text)} chars",
                    line_excerpt=excerpt(text),
                )
            )

    for ul in _BULLETS_UL.finditer(raw):
        base = ul.start(1)
        for li in _LI_ITEM.finditer(ul.group(1)):
            text = _element_text(li.group(1))
            if not text:
                continue
            if len(text) > BULLET_MAX_CHARS:
                rule = _RULE_BULLET_LONG
            elif len(text) > BULLET_IDEAL_CHARS:
                rule = _RULE_BULLET_OVER_IDEAL
            else:
                continue
            findings.append(
                Finding(
                    rule=rule,
                    line_number=line_of(base + li.start()),
                    matched_text=f"{len(text)} chars",
                    line_excerpt=excerpt(text),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"critical": 0, "material": 1, "minor": 2}


def format_text_report(findings: List[Finding], path: Path) -> str:
    if not findings:
        return (
            f"Resume lint: {path}\n"
            "================================\n"
            "No AI-sounding pattern matches.\n"
            "(This is a deterministic check; it doesn't replace the full "
            "review-resume audit.)\n"
        )

    findings = sorted(
        findings,
        key=lambda f: (_SEVERITY_ORDER[f.rule.severity], f.line_number),
    )

    counts = {"critical": 0, "material": 0, "minor": 0}
    for f in findings:
        counts[f.rule.severity] += 1

    out = []
    out.append(f"Resume lint: {path}")
    out.append("================================")
    out.append(
        f"{len(findings)} issue(s): "
        f"{counts['critical']} critical, "
        f"{counts['material']} material, "
        f"{counts['minor']} minor."
    )
    out.append("")

    last_severity = None
    for f in findings:
        if f.rule.severity != last_severity:
            label = f.rule.severity.upper()
            out.append(f"-- {label} --")
            last_severity = f.rule.severity
        out.append(f"[{f.rule.name}] line {f.line_number}")
        out.append(f"  match:   {f.matched_text!r}")
        out.append(f"  context: {f.line_excerpt}")
        out.append(f"  why:     {f.rule.why}")
        out.append(f"  fix:     {f.rule.fix}")
        out.append("")

    return "\n".join(out)


def format_json_report(findings: List[Finding], path: Path) -> str:
    payload = {
        "file": str(path),
        "counts": {
            "critical": sum(1 for f in findings if f.rule.severity == "critical"),
            "material": sum(1 for f in findings if f.rule.severity == "material"),
            "minor": sum(1 for f in findings if f.rule.severity == "minor"),
            "total": len(findings),
        },
        "findings": [
            {
                "rule": f.rule.name,
                "severity": f.rule.severity,
                "line": f.line_number,
                "match": f.matched_text,
                "context": f.line_excerpt,
                "why": f.rule.why,
                "fix": f.rule.fix,
            }
            for f in sorted(
                findings,
                key=lambda f: (_SEVERITY_ORDER[f.rule.severity], f.line_number),
            )
        ],
    }
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Lint a resume for AI-sounding patterns."
    )
    parser.add_argument("path", help="Path to the resume (.html, .htm, or .md).")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    text = html_to_text(raw) if suffix in {".html", ".htm"} else raw
    findings = lint(text) + lint_lengths(raw, suffix)

    if args.format == "json":
        print(format_json_report(findings, path))
    else:
        print(format_text_report(findings, path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
