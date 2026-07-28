"""Fetch a job description as exact markdown via OpenPostings CLI (preferred) or HTTP.

Acquisition order:
  1. `openpostings jd <url> --json` — normalized text (db / ats-api) or raw HTML
  2. On server_down / network / CLI missing: direct HTTP GET, treat as raw HTML
  3. Raw HTML → readability main-content extraction + HTML→markdown + invisible strip

Always strips zero-width characters. Flags (never strips) likely prompt-injection
patterns into YAML frontmatter `warnings`.

Usage:
    python fetch_jd.py "<url>" [--out <file>] [--company NAME] [--title TITLE]
    python fetch_jd.py "<url>" --json-meta   # also print a sidecar JSON summary to stderr

Exit codes:
  0  success (markdown written)
  1  error (not_found, empty, network failure after retries, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Comment

# Optional deps for raw-HTML path
try:
    from readability import Document  # readability-lxml
except ImportError:  # pragma: no cover
    Document = None  # type: ignore

try:
    from markdownify import markdownify as html_to_md
except ImportError:  # pragma: no cover
    html_to_md = None  # type: ignore


ZERO_WIDTH_RE = re.compile(
    "[\u200b\u200c\u200d\u2060\ufeff\u00ad]"
)

# ATS host hints for frontmatter
ATS_HOST_MAP = {
    "ashbyhq.com": "ashby",
    "greenhouse.io": "greenhouse",
    "boards.greenhouse.io": "greenhouse",
    "myworkdayjobs.com": "workday",
    "workday.com": "workday",
    "lever.co": "lever",
    "jobs.lever.co": "lever",
    "icims.com": "icims",
    "smartrecruiters.com": "smartrecruiters",
    "jobvite.com": "jobvite",
    "bamboohr.com": "bamboohr",
}


# ---------------------------------------------------------------------------
# Sanitization & injection flagging
# ---------------------------------------------------------------------------

def strip_zero_width(text: str) -> str:
    return ZERO_WIDTH_RE.sub("", text)


def strip_invisible_html(soup: BeautifulSoup) -> None:
    """Remove comments and hidden elements in-place (human never sees them)."""
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    hidden_selectors = [
        {"style": re.compile(r"display\s*:\s*none", re.I)},
        {"style": re.compile(r"visibility\s*:\s*hidden", re.I)},
        {"hidden": True},
        {"aria-hidden": "true"},
    ]
    for attrs in hidden_selectors:
        for el in soup.find_all(attrs=attrs):
            el.decompose()

    # white-on-white / near-invisible text via inline style
    for el in soup.find_all(style=True):
        style = el.get("style") or ""
        if re.search(r"color\s*:\s*(?:#fff(?:fff)?|white|rgba?\(\s*255)", style, re.I):
            if re.search(r"background(?:-color)?\s*:\s*(?:#fff(?:fff)?|white)", style, re.I):
                el.decompose()


INJECTION_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    (
        "ai_imperative",
        re.compile(
            r"(?i)\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior|above)\s+"
            r"(?:instructions?|prompts?|rules?)\b"
            r"|\byou\s+are\s+now\b"
            r"|\bact\s+as\s+(?:an?\s+)?(?:ai|assistant|system)\b"
            r"|\bsystem\s*:\s*"
            r"|\bdo\s+not\s+follow\s+(?:your|the)\s+(?:instructions?|guidelines?)\b",
        ),
    ),
    (
        "exfiltration_request",
        re.compile(
            r"(?i)\b(?:send|upload|post|exfiltrate|transmit|email)\b"
            r".{0,80}\b(?:credentials?|password|api[_\s-]?key|secret|token|resume|cv)\b"
            r".{0,80}https?://",
        ),
    ),
    (
        "large_base64",
        re.compile(r"(?:[A-Za-z0-9+/]{80,}={0,2})"),
    ),
    (
        "credential_near_url",
        re.compile(
            r"(?i)\b(?:password|passwd|api[_\s-]?key|secret|credential|token|auth)\b"
            r".{0,40}https?://|"
            r"https?://.{0,40}\b(?:password|passwd|api[_\s-]?key|secret|credential|token)\b",
        ),
    ),
]


def scan_injection(text: str) -> List[str]:
    warnings: List[str] = []
    for label, pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            warnings.append(label)
    return warnings


# ---------------------------------------------------------------------------
# ATS / metadata helpers
# ---------------------------------------------------------------------------

def detect_ats(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    for needle, name in ATS_HOST_MAP.items():
        if host.endswith(needle) or needle in host:
            return name
    return "unknown"


def yaml_quote(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    # Prefer plain scalars when safe; otherwise double-quote.
    if re.fullmatch(r"[A-Za-z0-9_./:@+-]+", s) and s not in ("true", "false", "null"):
        return s
    escaped = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def format_warnings(warnings: List[str]) -> str:
    if not warnings:
        return "[]"
    items = ", ".join(yaml_quote(w) for w in warnings)
    return f"[{items}]"


def build_frontmatter(
    *,
    company: Optional[str],
    title: Optional[str],
    url: str,
    ats: str,
    source: str,
    warnings: List[str],
) -> str:
    fetched = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "---",
        f"company: {yaml_quote(company)}",
        f"title: {yaml_quote(title)}",
        f"url: {yaml_quote(url)}",
        f"ats: {yaml_quote(ats)}",
        f"fetched: {fetched}",
        f"source: {yaml_quote(source)}",
        f"warnings: {format_warnings(warnings)}",
        "---",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Raw HTML extraction
# ---------------------------------------------------------------------------

def extract_from_html(html: str) -> str:
    """Readability-style main content → markdown, with invisible stripping."""
    soup = BeautifulSoup(html, "html.parser")
    strip_invisible_html(soup)
    cleaned_html = str(soup)

    main_html = cleaned_html
    if Document is not None:
        try:
            doc = Document(cleaned_html)
            main_html = doc.summary(html_partial=True)
        except Exception:
            main_html = cleaned_html

    if html_to_md is not None:
        md = html_to_md(main_html, heading_style="ATX", strip=["script", "style", "noscript"])
    else:
        # Fallback: plain text from soup
        body = BeautifulSoup(main_html, "html.parser")
        md = body.get_text("\n", strip=True)

    md = strip_zero_width(md)
    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md


def sanity_check(text: str) -> Optional[str]:
    """Return a warning code if extraction looks broken, else None."""
    stripped = text.strip()
    if len(stripped) < 200:
        return "implausibly_short"
    # Need some sentence-like structure
    if not re.search(r"[.!?]\s+[A-Z]", stripped) and stripped.count("\n") < 3:
        return "no_sentence_structure"
    # Navigation boilerplate heuristic
    lower = stripped.lower()
    nav_hits = sum(
        1
        for phrase in ("cookie policy", "privacy policy", "sign in", "log in", "accept all cookies")
        if phrase in lower
    )
    if nav_hits >= 3 and len(stripped) < 800:
        return "navigation_boilerplate"
    return None


# ---------------------------------------------------------------------------
# OpenPostings CLI + HTTP
# ---------------------------------------------------------------------------

def resolve_openpostings_cmd() -> Optional[List[str]]:
    """Return argv prefix to invoke the OpenPostings CLI (Windows npm .cmd-safe)."""
    for name in ("openpostings", "openpostings.cmd", "openpostings.CMD"):
        path = shutil.which(name)
        if not path:
            continue
        lower = path.lower()
        if lower.endswith(".cmd") or lower.endswith(".bat"):
            # CreateProcess cannot launch npm's .cmd shims directly.
            return ["cmd", "/c", path]
        return [path]
    return None


def run_openpostings_jd(url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Return (envelope_dict, error_message). envelope is None on hard failure."""
    argv_prefix = resolve_openpostings_cmd()
    if not argv_prefix:
        return None, "cli_missing"

    try:
        proc = subprocess.run(
            [*argv_prefix, "jd", url, "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except FileNotFoundError:
        return None, "cli_missing"
    except subprocess.TimeoutExpired:
        return None, "timeout"

    stdout = (proc.stdout or "").strip()
    if not stdout:
        return None, f"empty_stdout exit={proc.returncode} stderr={(proc.stderr or '')[:200]}"

    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError:
        return None, f"invalid_json exit={proc.returncode}"

    return envelope, None


def http_get(url: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        resp = requests.get(
            url,
            timeout=45,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; resume-toolkit-fetch-jd/1.0; "
                    "+https://github.com/RevDrSquash/resume-toolkit)"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text, None
    except requests.RequestException as exc:
        return None, str(exc)


def source_label(cli_source: Optional[str], via_raw_extract: bool) -> str:
    if via_raw_extract:
        return "raw-extract"
    if cli_source == "db":
        return "cli-db"
    if cli_source == "ats-api":
        return "cli-ats-api"
    if cli_source == "raw-html":
        return "raw-extract"
    return "raw-extract"


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def fetch_jd(
    url: str,
    *,
    company: Optional[str] = None,
    title: Optional[str] = None,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Returns (markdown_document_or_None, meta).
    meta always includes ok, source, warnings, error (if any).
    """
    meta: Dict[str, Any] = {
        "ok": False,
        "url": url,
        "company": company,
        "title": title,
        "ats": detect_ats(url),
        "source": None,
        "warnings": [],
        "error": None,
        "error_kind": None,
        "sanity": None,
    }

    text: Optional[str] = None
    via_raw = False
    cli_source: Optional[str] = None

    envelope, cli_err = run_openpostings_jd(url)

    if cli_err == "cli_missing":
        meta["warnings"].append("cli_missing_fallback_http")
        html, http_err = http_get(url)
        if http_err or not html:
            meta["error"] = http_err or "empty_http_body"
            meta["error_kind"] = "network"
            return None, meta
        text = extract_from_html(html)
        via_raw = True
        cli_source = None
    elif cli_err:
        # Unexpected CLI failure — try HTTP once
        meta["warnings"].append(f"cli_error:{cli_err}")
        html, http_err = http_get(url)
        if http_err or not html:
            meta["error"] = cli_err
            meta["error_kind"] = "error"
            return None, meta
        text = extract_from_html(html)
        via_raw = True
    else:
        assert envelope is not None
        if envelope.get("ok") is True and not envelope.get("raw"):
            text = strip_zero_width(envelope.get("text") or "")
            cli_source = envelope.get("source")
            via_raw = False
        elif envelope.get("raw") is True:
            html = envelope.get("text") or ""
            text = extract_from_html(html)
            cli_source = envelope.get("source") or "raw-html"
            via_raw = True
        else:
            kind = envelope.get("error_kind") or "error"
            meta["error"] = envelope.get("error") or kind
            meta["error_kind"] = kind

            if kind == "not_found":
                return None, meta

            if kind in ("server_down", "network"):
                # Retry CLI once, then HTTP
                envelope2, cli_err2 = run_openpostings_jd(url)
                if (
                    envelope2
                    and envelope2.get("ok") is True
                    and not envelope2.get("raw")
                ):
                    text = strip_zero_width(envelope2.get("text") or "")
                    cli_source = envelope2.get("source")
                    via_raw = False
                    meta["error"] = None
                    meta["error_kind"] = None
                elif envelope2 and envelope2.get("raw") is True:
                    text = extract_from_html(envelope2.get("text") or "")
                    cli_source = envelope2.get("source") or "raw-html"
                    via_raw = True
                    meta["error"] = None
                    meta["error_kind"] = None
                else:
                    html, http_err = http_get(url)
                    if http_err or not html:
                        return None, meta
                    text = extract_from_html(html)
                    via_raw = True
                    meta["error"] = None
                    meta["error_kind"] = None
                    meta["warnings"].append("http_fallback_after_cli_error")
            else:
                # empty_description / error — try HTTP as last resort for empty
                html, http_err = http_get(url)
                if http_err or not html:
                    return None, meta
                text = extract_from_html(html)
                via_raw = True
                meta["error"] = None
                meta["error_kind"] = None
                meta["warnings"].append(f"http_fallback_after_{kind}")

    if not text or not text.strip():
        meta["error"] = "empty_description"
        meta["error_kind"] = "empty_description"
        return None, meta

    text = strip_zero_width(text)
    injection = scan_injection(text)
    meta["warnings"].extend(injection)

    sanity = sanity_check(text)
    if sanity:
        meta["sanity"] = sanity
        meta["warnings"].append(f"sanity:{sanity}")

    src = source_label(cli_source, via_raw)
    meta["source"] = src
    meta["ok"] = True

    body = text.strip() + "\n"
    doc = build_frontmatter(
        company=company,
        title=title,
        url=url,
        ats=meta["ats"],
        source=src,
        warnings=meta["warnings"],
    ) + body

    return doc, meta


def main() -> int:
    # Force UTF-8 on Windows consoles
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Fetch a job description as exact markdown.")
    parser.add_argument("url", help="Job posting URL")
    parser.add_argument("--out", "-o", help="Write markdown to this file (UTF-8)")
    parser.add_argument("--company", help="Company name for frontmatter")
    parser.add_argument("--title", help="Job title for frontmatter")
    parser.add_argument(
        "--json-meta",
        action="store_true",
        help="Print JSON metadata to stderr (always; useful for agents)",
    )
    args = parser.parse_args()

    url = args.url.strip()
    if "linkedin.com" in url.lower():
        print(
            "LinkedIn URLs must use the linkedin-job-to-markdown skill, not this script.",
            file=sys.stderr,
        )
        meta = {
            "ok": False,
            "error": "linkedin_use_dedicated_skill",
            "error_kind": "error",
            "url": url,
        }
        print(json.dumps(meta), file=sys.stderr)
        return 1

    doc, meta = fetch_jd(url, company=args.company, title=args.title)

    if args.json_meta or not meta.get("ok"):
        print(json.dumps(meta, ensure_ascii=False), file=sys.stderr)

    if not meta.get("ok") or doc is None:
        return 1

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(doc, encoding="utf-8")
        print(str(out_path.resolve()))
    else:
        sys.stdout.write(doc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
