"""Build the member training guide from its Markdown source."""

import argparse
import json
from pathlib import Path

import markdown


ROOT = Path(__file__).resolve().parent
STYLE = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; background: #edf1f2; color: #263c46;
  font: 10.5pt/1.65 'Microsoft YaHei', 'PingFang SC', sans-serif; }
.sheet { width: 210mm; height: 297mm; margin: 16px auto; background: white;
  padding: 15mm 17mm 19mm; position: relative; break-after: page; }
.sheet:last-child { break-after: auto; }
.topline { border-top: 3px solid #2d8277; padding-top: 3mm;
  font-size: 8pt; color: #4e8178; letter-spacing: 1px; margin-bottom: 4mm; }
h1 { font-size: 25pt; line-height: 1.3; letter-spacing: .6px;
  margin: 3mm 0 5mm; color: #193b47; }
h2 { font-size: 15pt; line-height: 1.4; color: #20584f; margin: 5mm 0 2mm; }
h3 { font-size: 11pt; color: #346259; margin: 4mm 0 2mm; }
p { margin: 2.5mm 0; }
ul, ol { padding-left: 5.5mm; margin: 2mm 0; }
li { margin: 1.5mm 0; }
strong { color: #254f46; }
a { color: #247f74; text-decoration: none; overflow-wrap: anywhere; }
pre { background: #f2f7f5; border-left: 3px solid #66a798;
  padding: 3mm 4mm; margin: 3mm 0; white-space: pre-wrap;
  overflow-wrap: anywhere; font: 9.5pt/1.65 Consolas, 'Microsoft YaHei', monospace; }
code { font-family: Consolas, 'Microsoft YaHei', monospace; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0;
  font-size: 9.5pt; line-height: 1.55; }
th, td { padding: 2mm 3mm; border: 1px solid #dce8e3; text-align: left; }
th { color: #356358; background: #eef5f1; }
th:first-child, td:first-child { width: 28%; }
.footer { position: absolute; left: 17mm; right: 17mm; bottom: 8mm;
  border-top: 1px solid #dce6e2; padding-top: 2mm; color: #869d96;
  font-size: 8pt; display: flex; justify-content: space-between; }
@media print { body { background: white; } .sheet { margin: 0; } }
@media screen and (max-width: 850px) {
  body { background: white; font-size: 14px; }
  .sheet { width: 100%; height: auto; margin: 0; padding: 25px 22px 65px;
    border-bottom: 8px solid #edf1f2; }
  .footer { left: 22px; right: 22px; bottom: 18px; }
  h1 { font-size: 27px; } h2 { font-size: 20px; }
  pre { font-size: 12px; padding: 13px; }
}
"""


def build_html():
    source = (ROOT / "training-guide.md").read_text(encoding="utf-8")
    content = markdown.markdown(source, extensions=["tables", "fenced_code"])
    pages = content.split('<div class="page-break"></div>')
    sections = []
    for index, body in enumerate(pages, 1):
        sections.append(
            '<section class="sheet">'
            '<div class="topline">TANUKI · 成员培训指南</div>'
            f'<article>{body}</article><div class="footer">'
            '<span>github.com/SanN2Z/tanuki</span>'
            f'<span>{index:02} / {len(pages):02}</span></div></section>'
        )
    html = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>tanuki 成员培训指南</title>'
        f'<style>{STYLE}</style></head><body>{"".join(sections)}</body></html>'
    )
    destination = ROOT / "training-guide.html"
    destination.write_text(html, encoding="utf-8")
    return destination, len(pages)


def build_pdf(html, expected_pages, executable):
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    with sync_playwright() as playwright:
        options = {"headless": True}
        if executable:
            options["executable_path"] = str(Path(executable).resolve())
        browser = playwright.chromium.launch(**options)
        try:
            page = browser.new_page(viewport={"width": 1000, "height": 1300})
            page.goto(html.as_uri(), wait_until="load")
            page.emulate_media(media="print")
            page.evaluate("document.fonts.ready")
            layout = page.evaluate("""() => Array.from(document.querySelectorAll('.sheet')).map(sheet => ({
                contentBottom: sheet.querySelector('article').getBoundingClientRect().bottom,
                footerTop: sheet.querySelector('.footer').getBoundingClientRect().top
            }))""")
            if any(item["contentBottom"] + 8 > item["footerTop"] for item in layout):
                raise RuntimeError("Training content overlaps a page footer: " + json.dumps(layout))
            destination = ROOT / "training-guide.pdf"
            page.pdf(path=str(destination), print_background=True, prefer_css_page_size=True)
        finally:
            browser.close()
    reader = PdfReader(destination)
    if len(reader.pages) != expected_pages:
        raise RuntimeError(f"Expected {expected_pages} PDF pages, got {len(reader.pages)}")
    pdf_text = "\n".join(page.extract_text() for page in reader.pages)
    for text in ("https://github.com/SanN2Z/tanuki", "SKILL.md", "RUN.md"):
        if text not in pdf_text:
            raise RuntimeError("Required handoff text is missing from the PDF: " + text)
    return {"pdf": str(destination), "pages": len(reader.pages), "layout": layout}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", action="store_true", help="Render and check the PDF")
    parser.add_argument("--browser", help="Chromium executable used for PDF rendering")
    args = parser.parse_args()
    html, pages = build_html()
    result = {"html": str(html), "pages": pages}
    if args.pdf:
        result.update(build_pdf(html, pages, args.browser))
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
