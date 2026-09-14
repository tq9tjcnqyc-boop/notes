#!/usr/bin/env python3
"""把 ~/notes 的纯文本笔记编译成静态站点，输出到 _site/。只用标准库。

- 日记 2026/09/12.txt   -> _site/2026/09/12.html
- 具名页 pages/名字.txt  -> _site/pages/名字.html
- 生成 _site/index.html
- 正文里的 [[2026-09-11]] / [[项目A]] 变成站内链接
- 每个页面底部列出反向链接（哪些页面 [[引用了本页]]）
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
       font-family: -apple-system, "PingFang SC", "Hiragino Sans GB",
                    "Microsoft YaHei", sans-serif;
       font-size: 16px; line-height: 1.8; }
main { max-width: 44rem; margin: 0 auto; padding: 3rem 1.25rem 6rem; }
h1 { font-size: 1.1rem; font-weight: 600; color: #8a8578;
     letter-spacing: .02em; margin: 0 0 1.5rem; }
pre { white-space: pre-wrap; word-break: break-word; margin: 0;
      font: inherit;
      font-variant-numeric: tabular-nums; }
a { color: #2f6f4f; text-underline-offset: .2em; }
nav { margin-bottom: 2rem; font-size: .9rem; }
ul { list-style: none; padding: 0; }
li { margin: .2rem 0; }
li span { color: #a9a396; margin-left: .6em; font-size: .85em; }
.missing { color: #b5544a; text-decoration-style: dashed; }
hr { border: 0; border-top: 1px solid #e6e3da; margin: 3rem 0 2rem; }
.backlinks { margin-top: 3rem; border-top: 1px solid #e6e3da; padding-top: 1.25rem; }
.backlinks h2 { font-size: .78rem; font-weight: 600; color: #a9a396;
                letter-spacing: .1em; text-transform: uppercase; margin: 0 0 .6rem; }
.backlinks li { font-size: .95rem; line-height: 1.7; }
@media (prefers-color-scheme: dark) {
  body { background: #1c1c1a; color: #d8d5cc; }
  h1 { color: #8f8b80; }
  a { color: #7fc39b; }
  li span { color: #6f6b62; }
  hr { border-top-color: #33322e; }
  .backlinks { border-top-color: #33322e; }
  .backlinks h2 { color: #6f6b62; }
}
"""


def target_of(label):
    """[[标签]] 对应的输出文件路径。"""
    if DATE.fullmatch(label):
        return OUT / (label.replace("-", "/") + ".html")
    return OUT / "pages" / f"{label}.html"


def wikilinks(body):
    """正文里出现的 [[...]] 标签，去重并保持先后顺序。"""
    seen = {}
    for m in WIKI.finditer(body):
        label = m.group(1).strip()
        if label:
            seen.setdefault(label, None)
    return list(seen)


def render(notes, out_file, title, body, links):
    """把一段正文渲染成一个页面；links 是 [(标题, 输出路径)] 的反向链接。"""
    def href(target):
        return html.escape(os.path.relpath(target, out_file.parent))

    def wiki(m):
        label = m.group(1).strip()
        target = target_of(label)
        cls = "" if target in notes else ' class="missing"'
        return f'<a href="{href(target)}"{cls}>{html.escape(label)}</a>'

    text = html.escape(body)
    text = WIKI.sub(wiki, text)
    back = f'<nav><a href="{href(OUT / "index.html")}">← 全部笔记</a></nav>'
    if links:
        rows = "".join(
            f'<li><a href="{href(target)}">{html.escape(name)}</a></li>'
            for name, target in links
        )
        section = (f'<section class="backlinks"><h2>链接到本页</h2>'
                   f"<ul>{rows}</ul></section>")
    else:
        section = ""
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        f'<!doctype html><html lang="zh"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
        f"<body><main>{back}<h1>{html.escape(title)}</h1>"
        f"<pre>{text}</pre>{section}</main></body></html>\n",
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

    # 先把所有页面读进来，算出各自的标题和反向链接，再统一渲染。
    documents = []      # (out_file, 标题, 正文)
    titles = {}         # out_file -> 标题
    for src in dailies + pages:
        rel = src.relative_to(ROOT).with_suffix(".html")
        title = ("-".join(src.relative_to(ROOT).with_suffix("").parts)
                 if src in dailies else src.stem)
        out_file = OUT / rel
        titles[out_file] = title
        documents.append((out_file, title, src.read_text(encoding="utf-8").strip()))

    backlinks = {out_file: [] for out_file, _, _ in documents}
    for out_file, title, body in documents:
        for label in wikilinks(body):
            target = target_of(label)
            if target in titles and target != out_file:
                backlinks[target].append((title, out_file))

    for out_file, title, body in documents:
        links = sorted(backlinks[out_file], key=lambda item: item[0])
        render(notes, out_file, title, body, links)

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
