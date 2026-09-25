"""把霞鹜文楷（LXGW WenKai，SIL OFL 1.1）裁剪成只含动画用字的单个 woff2。

霞鹜文楷的网页字体包按 unicode-range 拆成了很多子集文件。这里先找出页面里用到的字，
从对应子集中各自裁剪，再合并成一个小字体文件。

用法：
  npm install lxgw-wenkai-webfont
  python3 make_font.py node_modules/lxgw-wenkai-webfont/lxgwwenkai-regular.css explainer.html fonts/lxgw-wenkai-subset.woff2
"""
import logging
import os
import re
import sys
import tempfile

from fontTools import subset
from fontTools.merge import Merger
from fontTools.ttLib import TTFont

logging.getLogger("fontTools").setLevel(logging.ERROR)


def parse_ranges(css_path):
    css = open(css_path, encoding="utf-8").read()
    base = os.path.dirname(css_path)
    faces = []
    for block in re.findall(r"@font-face\s*{(.*?)}", css, re.S):
        src = re.search(r"url\(['\"]?([^'\")]+\.woff2)", block)
        rng = re.search(r"unicode-range:\s*([^;}]+)", block)
        if not src or not rng:
            continue
        cps = set()
        for part in rng.group(1).split(","):
            part = part.strip().upper().replace("U+", "")
            if "-" in part:
                a, b = part.split("-")
                cps.update(range(int(a, 16), int(b, 16) + 1))
            elif "?" in part:
                cps.update(range(int(part.replace("?", "0"), 16), int(part.replace("?", "F"), 16) + 1))
            else:
                cps.add(int(part, 16))
        faces.append((os.path.join(base, src.group(1)), cps))
    return faces


def main(css_path, html_path, out_path):
    html = open(html_path, encoding="utf-8").read()
    wanted = {ord(c) for c in html if ord(c) > 0x7F} | set(range(0x20, 0x7F))
    faces = parse_ranges(css_path)
    tmp = tempfile.mkdtemp()
    parts = []
    for i, (path, cps) in enumerate(faces):
        need = wanted & cps
        if not need:
            continue
        font = TTFont(path)
        opts = subset.Options()
        opts.layout_features = ["*"]
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=need)
        sub.subset(font)
        font.flavor = None
        p = os.path.join(tmp, f"{i}.ttf")
        font.save(p)
        parts.append(p)
    merged = Merger().merge(parts)
    merged.flavor = "woff2"
    merged.save(out_path)
    missing = wanted - set(merged.getBestCmap())
    print(f"{len(parts)} 个子集 -> {out_path}（{os.path.getsize(out_path) // 1024} KB）")
    if missing:
        print("字体中缺少：", "".join(chr(c) for c in sorted(missing) if c > 0x7F))


if __name__ == "__main__":
    main(*sys.argv[1:4])
