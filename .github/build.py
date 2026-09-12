#!/usr/bin/env python3
"""把 ~/notes 的纯文本笔记编译成静态站点，输出到 _site/。只用标准库。

- 日记 2026/09/12.txt   -> _site/2026/09/12.html
- 具名页 pages/名字.txt  -> _site/pages/名字.html
- 生成 _site/index.html
- 正文里的 [[2026-09-11]] / [[项目A]] 变成站内链接
"""
import html
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
WIKI = re.compile(r"\[\[([^\[\]]+)\]\]")

CSS = """
:root { color-scheme: light dark; }
body { margin: 0; background: #fbfbfa; color: #26251f;
       font: 16px/1.8 ui-serif, "Songti SC", Georgia, serif; }
main { max-width: 44rem; margin: 0 auto; padding: 3rem 1.25rem 6rem; }
h1 { font-size: 1.1rem; font-weight: 600; color: #8a8578;
     letter-spacing: .02em; margin: 0 0 1.5rem; }
pre { white-space: pre-wrap; word-break: break-word; margin: 0;
      font: inherit; }
a { color: #2f6f4f; text-underline-offset: .2em; }
nav { margin-bottom: 2rem; font-size: .9rem; }
ul { list-style: none; padding: 0; }
li { margin: .2rem 0; }
li span { color: #a9a396; margin-left: .6em; font-size: .85em; }
.missing { color: #b5544a; text-decoration-style: dashed; }
hr { border: 0; border-top: 1px solid #e6e3da; margin: 3rem 0 2rem; }
@media (prefers-color-scheme: dark) {
  body { background: #1c1c1a; color: #d8d5cc; }
  h1 { color: #8f8b80; }
  a { color: #7fc39b; }
  li span { color: #6f6b62; }
  hr { border-top-color: #33322e; }
}
"""


def render(notes, out_file, title, body):
    """把一段正文渲染成一个页面。"""
    def href(target):
        return html.escape(os.path.relpath(target, out_file.parent))

    def wiki(m):
        label = m.group(1).strip()
        if DATE.fullmatch(label):
            target = OUT / (label.replace("-", "/") + ".html")
        else:
            target = OUT / "pages" / f"{label}.html"
        cls = "" if target in notes else ' class="missing"'
        return f'<a href="{href(target)}"{cls}>{html.escape(label)}</a>'

    text = html.escape(body)
    text = WIKI.sub(wiki, text)
    back = f'<nav><a href="{href(OUT / "index.html")}">← 全部笔记</a></nav>'
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        f'<!doctype html><html lang="zh"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
        f"<body><main>{back}<h1>{html.escape(title)}</h1>"
        f"<pre>{text}</pre></main></body></html>\n",
        encoding="utf-8",
    )


def main():
    if OUT.exists():
        shutil.rmtree(OUT)

    dailies, pages, notes = [], [], set()

    for src in sorted(ROOT.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/*.txt")):
        dailies.append(src)
        notes.add(OUT / src.relative_to(ROOT).with_suffix(".html"))
    if (ROOT / "pages").exists():
        for src in sorted((ROOT / "pages").glob("*.txt")):
            pages.append(src)
            notes.add(OUT / "pages" / f"{src.stem}.html")

    for src in dailies + pages:
        rel = src.relative_to(ROOT).with_suffix(".html")
        title = ("-".join(src.relative_to(ROOT).with_suffix("").parts)
                 if src in dailies else src.stem)
        render(notes, OUT / rel, title, src.read_text(encoding="utf-8").strip())

    rows = []
    for src in reversed(dailies):
        name = "-".join(src.relative_to(ROOT).with_suffix("").parts)
        rows.append((name, src.relative_to(ROOT).with_suffix(".html"), ""))
    for src in sorted(pages):
        rows.append((src.stem, Path("pages") / f"{src.stem}.html", "pages"))

    items = "\n".join(
        f'<li><a href="{html.escape(os.path.relpath(OUT / rel, OUT))}">{html.escape(name)}</a>'
        f'{"<span>" + tag + "</span>" if tag else ""}</li>'
        for name, rel, tag in rows
    ) or "<li>还没有笔记</li>"

    (OUT / "index.html").write_text(
        f'<!doctype html><html lang="zh"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>笔记</title><style>{CSS}</style></head><body><main>"
        f"<h1>笔记</h1><ul>{items}</ul><hr>"
        f"<p style='font-size:.85rem;color:#a9a396'>"
        f"{len(dailies)} 篇日记 · {len(pages)} 个页面</p>"
        f"</main></body></html>\n",
        encoding="utf-8",
    )
    print(f"built {len(dailies)} dailies + {len(pages)} pages -> {OUT}")


if __name__ == "__main__":
    main()
