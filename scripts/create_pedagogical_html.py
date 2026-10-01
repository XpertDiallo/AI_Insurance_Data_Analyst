"""Render the pedagogical notebook as a standalone, dependency-free HTML page."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path


def render_markdown(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    in_code = False
    code_lines: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(paragraph).strip()
            text = html.escape(text)
            text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
            text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
            output.append(f"<p>{text}</p>")
            paragraph.clear()

    for line in lines:
        if line.startswith("```"):
            if in_code:
                output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            continue
        match = re.match(r"^(#{1,3})\s+(.*)$", line)
        if match:
            flush_paragraph()
            level = len(match.group(1))
            text = html.escape(match.group(2))
            text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
            text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
            output.append(f"<h{level + 1}>{text}</h{level + 1}>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            item = html.escape(line[2:])
            item = re.sub(r"`([^`]+)`", r"<code>\1</code>", item)
            item = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", item)
            if not output or (output[-1] != "<ul>" and not output[-1].startswith("<li>")):
                output.append("<ul>")
            output.append(f"<li>{item}</li>")
            continue
        if output and output[-1].startswith("<li>"):
            output.append("</ul>")
        paragraph.append(line)
    flush_paragraph()
    if output and output[-1].startswith("<li>"):
        output.append("</ul>")
    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "\n".join(output)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    notebook_path = root / "docs" / "AI_Insurance_Data_Analyst_Pedagogical.ipynb"
    output_path = root / "docs" / "AI_Insurance_Data_Analyst_Pedagogical.html"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    sections: list[str] = []
    for index, cell in enumerate(notebook["cells"], start=1):
        source = "".join(cell.get("source", []))
        if cell["cell_type"] == "markdown":
            sections.append(f'<section class="markdown-cell">{render_markdown(source)}</section>')
        else:
            sections.append(
                f'<section class="code-cell"><div class="cell-label">Bloc Python {index}</div>'
                f"<pre><code>{html.escape(source)}</code></pre></section>"
            )
    document = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Insurance Data Analyst V2 — Notebook pédagogique</title>
<style>
:root {{ --navy:#17365d; --blue:#2f5597; --ink:#243447; --muted:#667085; --paper:#fff; --bg:#f3f6fa; --code:#172033; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif; }}
header {{ background:linear-gradient(135deg,var(--navy),var(--blue)); color:#fff; padding:48px max(24px,calc((100% - 1100px)/2)); }}
header h1 {{ margin:0 0 8px; font-size:2.1rem; }}
header p {{ margin:0; opacity:.9; max-width:850px; }}
main {{ max-width:1100px; margin:28px auto 64px; padding:0 20px; }}
section {{ background:var(--paper); border-radius:12px; box-shadow:0 2px 12px #1d355710; margin:18px 0; padding:24px 30px; }}
.markdown-cell h2 {{ color:var(--navy); border-bottom:1px solid #e5eaf1; padding-bottom:8px; }}
.markdown-cell h3 {{ color:var(--blue); }}
.markdown-cell p {{ margin:10px 0; }}
.markdown-cell li {{ margin:4px 0; }}
code {{ background:#eef2f7; color:#243447; border-radius:4px; padding:2px 5px; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.92em; }}
pre {{ background:var(--code); color:#e8eef8; border-radius:9px; overflow:auto; padding:18px; line-height:1.5; font-size:.9rem; }}
pre code {{ background:transparent; color:inherit; padding:0; border-radius:0; }}
.code-cell {{ border-left:5px solid var(--blue); padding-top:16px; padding-bottom:16px; }}
.cell-label {{ color:var(--blue); font-size:.78rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; margin-bottom:8px; }}
footer {{ max-width:1100px; margin:0 auto 45px; padding:0 20px; color:var(--muted); font-size:.9rem; }}
@media (max-width:700px) {{ header {{ padding:32px 20px; }} section {{ padding:18px; }} }}
</style>
</head>
<body>
<header><h1>AI Insurance Data Analyst V2</h1><p>Version HTML pédagogique — architecture, services déterministes et orchestration Agentic AI.</p></header>
<main>{''.join(sections)}</main>
<footer>Document généré depuis docs/AI_Insurance_Data_Analyst_Pedagogical.ipynb. Les calculs restent exécutables dans le notebook et validés par les tests du projet.</footer>
</body>
</html>
"""
    output_path.write_text(document, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
