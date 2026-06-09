"""Convert a resume Markdown or HTML file to an ATS-friendly PDF.

Usage: python md_resume_to_pdf.py "<input.{md,html}>" "<output.pdf>"

For .md input: applies the bundled ATS-friendly template (single column,
Helvetica, standard headers, plain-text contact info) via xhtml2pdf.

For .html input: renders the file via headless Chromium (Playwright) so
the file's own CSS, including flexbox, CSS variables, pseudo-elements,
and @page rules, is honored. The resulting PDF has a real text layer in
DOM order, so it remains ATS-parseable.

If Playwright (or its Chromium download) is unavailable (e.g., a sandbox
that blocks the Playwright CDN), the script falls back to WeasyPrint, a
pure-Python HTML/CSS renderer that produces equivalent ATS-parseable PDFs
without needing a browser binary.

HTML rendering prerequisites (either path works):
    pip install playwright && playwright install chromium
    pip install weasyprint
"""
import os
import re
import sys
import html
from xhtml2pdf import pisa


_PUNCT = {
    "–": "-", "—": "-", "−": "-",
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "…": "...", " ": " ",
}


def sanitize(text: str) -> str:
    """Map non-ASCII punctuation to ASCII so the base font encodes it cleanly."""
    for k, v in _PUNCT.items():
        text = text.replace(k, v)
    return text


def md_inline(text: str) -> str:
    """Escape HTML, then convert **bold** to <b>."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


DATE_RE = re.compile(r"^\d{2}/\d{4}\s*[–—-]\s*(\d{2}/\d{4}|Present)")


def parse(md: str) -> str:
    lines = md.splitlines()
    name = ""
    preamble: list[str] = []
    i = 0

    while i < len(lines):
        ln = lines[i].strip()
        i += 1
        if ln.startswith("# ") and not ln.startswith("## "):
            name = ln[2:].strip()
            break

    while i < len(lines):
        ln = lines[i].strip()
        if ln.startswith("## "):
            break
        if ln:
            preamble.append(ln)
        i += 1

    title = preamble[0] if preamble else ""
    contact = "<br/>".join(md_inline(p) for p in preamble[1:])

    parts: list[str] = [
        f'<h1>{md_inline(name)}</h1>',
        f'<p class="title">{md_inline(title)}</p>',
        f'<p class="contact">{contact}</p>',
    ]

    section = None
    list_open = False

    def close_list():
        nonlocal list_open
        if list_open:
            parts.append("</ul>")
            list_open = False

    while i < len(lines):
        raw = lines[i]
        ln = raw.strip()
        i += 1
        if not ln:
            continue
        if ln.startswith("## "):
            close_list()
            section = ln[3:].strip()
            parts.append(f"<h2>{md_inline(section)}</h2>")
            continue
        if ln.startswith("- "):
            if not list_open:
                parts.append("<ul>")
                list_open = True
            parts.append(f"<li>{md_inline(ln[2:].strip())}</li>")
            continue
        close_list()
        if DATE_RE.match(ln):
            parts.append(f'<p class="dates">{md_inline(ln)}</p>')
        elif ln.startswith("**") and ln.endswith("**") and "|" in ln:
            parts.append(f'<p class="rolehead">{md_inline(ln)}</p>')
        else:
            cls = "summary" if section == "Professional Summary" else "body"
            parts.append(f'<p class="{cls}">{md_inline(ln)}</p>')

    close_list()
    return "\n".join(parts)


CSS = """
@page { size: letter; margin: 0.55in 0.6in; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5px;
       color: #000; line-height: 1.32; }
h1 { font-size: 21px; margin: 0 0 1px 0; font-weight: bold; }
p.title { font-size: 12px; margin: 0 0 3px 0; font-weight: bold; }
p.contact { font-size: 9.5px; margin: 0 0 9px 0; }
h2 { font-size: 12px; margin: 11px 0 4px 0; padding-bottom: 2px;
     border-bottom: 1px solid #000; font-weight: bold;
     text-transform: uppercase; letter-spacing: 0.5px; }
p.summary { margin: 0 0 3px 0; text-align: left; }
p.body { margin: 1px 0; }
p.rolehead { margin: 7px 0 0 0; font-weight: bold; font-size: 11px; }
p.dates { margin: 0 0 2px 0; font-size: 9.5px; color: #222; }
ul { margin: 2px 0 4px 0; padding-left: 14px; }
li { margin: 0 0 2px 0; }
"""


def render_md(path: str) -> str:
    """Read a Markdown file and return a complete HTML document."""
    with open(path, "r", encoding="utf-8") as f:
        md = sanitize(f.read())
    body = parse(md)
    return (
        "<html><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


def _render_html_with_weasyprint(src: str, dst: str) -> None:
    """Pure-Python HTML to PDF fallback for environments without Chromium."""
    import weasyprint
    weasyprint.HTML(filename=src).write_pdf(dst)


def _render_html_with_playwright(src: str, dst: str) -> None:
    """Render via headless Chromium (Playwright). Raises on any failure."""
    from playwright.sync_api import sync_playwright
    src_abs = os.path.abspath(src)
    file_url = "file:///" + src_abs.replace("\\", "/")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(file_url, wait_until="networkidle")
            page.pdf(
                path=dst,
                prefer_css_page_size=True,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()


def render_html_to_pdf(src: str, dst: str) -> None:
    """Render HTML to PDF via Playwright; fall back to WeasyPrint.

    Playwright (headless Chromium) is preferred for the highest-fidelity
    rendering. If Playwright is not installed, or its Chromium binary cannot
    launch (common in sandboxes where the Playwright CDN is blocked by a
    network allowlist), we fall back to WeasyPrint, a pure-Python renderer
    that handles modern CSS and also emits a real DOM-order text layer.
    """
    try:
        _render_html_with_playwright(src, dst)
        return
    except ImportError:
        pass
    except Exception as e:
        print(
            f"Playwright path failed ({e.__class__.__name__}); "
            "falling back to WeasyPrint.",
            file=sys.stderr,
        )

    try:
        _render_html_with_weasyprint(src, dst)
    except ImportError:
        print(
            "Neither Playwright (with Chromium) nor WeasyPrint is available. "
            "Install one of:\n"
            "  pip install playwright && playwright install chromium\n"
            "  pip install weasyprint",
            file=sys.stderr,
        )
        sys.exit(3)


def main():
    if len(sys.argv) != 3:
        print("Usage: python md_resume_to_pdf.py <input.{md,html}> <output.pdf>",
              file=sys.stderr)
        sys.exit(2)
    src, dst = sys.argv[1], sys.argv[2]
    ext = os.path.splitext(src)[1].lower()
    if ext in (".html", ".htm"):
        render_html_to_pdf(src, dst)
        print(f"OK -> {dst}")
        return
    if ext not in (".md", ".markdown"):
        print(f"Unsupported file extension: {ext!r} (expected .md or .html)",
              file=sys.stderr)
        sys.exit(2)
    doc = render_md(src)
    with open(dst, "w+b") as out:
        result = pisa.CreatePDF(doc, dest=out, encoding="utf-8")
    if result.err:
        print(f"FAILED with {result.err} error(s)")
        sys.exit(1)
    print(f"OK -> {dst}")


if __name__ == "__main__":
    main()
