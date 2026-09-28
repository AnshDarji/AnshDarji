#!/usr/bin/env python3
"""Blocky pixel-font title SVG (OpenCode-style) with a left-to-right reveal.
Usage: python pixel_title.py "ANSH DARJI" -o assets/title.svg [--cell 9] [--split 1]
--split N: first N words use the muted tone, the rest the bright tone.
"""
import argparse

G = {
"A":"01110,10001,10001,11111,10001,10001,10001","B":"11110,10001,10001,11110,10001,10001,11110",
"C":"01110,10001,10000,10000,10000,10001,01110","D":"11110,10001,10001,10001,10001,10001,11110",
"E":"11111,10000,10000,11110,10000,10000,11111","F":"11111,10000,10000,11110,10000,10000,10000",
"G":"01110,10001,10000,10111,10001,10001,01111","H":"10001,10001,10001,11111,10001,10001,10001",
"I":"11111,00100,00100,00100,00100,00100,11111","J":"00111,00010,00010,00010,00010,10010,01100",
"K":"10001,10010,10100,11000,10100,10010,10001","L":"10000,10000,10000,10000,10000,10000,11111",
"M":"10001,11011,10101,10101,10001,10001,10001","N":"10001,11001,10101,10011,10001,10001,10001",
"O":"01110,10001,10001,10001,10001,10001,01110","P":"11110,10001,10001,11110,10000,10000,10000",
"Q":"01110,10001,10001,10001,10101,10010,01101","R":"11110,10001,10001,11110,10100,10010,10001",
"S":"01111,10000,10000,01110,00001,00001,11110","T":"11111,00100,00100,00100,00100,00100,00100",
"U":"10001,10001,10001,10001,10001,10001,01110","V":"10001,10001,10001,10001,10001,01010,00100",
"W":"10001,10001,10001,10101,10101,11011,10001","X":"10001,10001,01010,00100,01010,10001,10001",
"Y":"10001,10001,01010,00100,00100,00100,00100","Z":"11111,00001,00010,00100,01000,10000,11111",
"0":"01110,10001,10011,10101,11001,10001,01110","1":"00100,01100,00100,00100,00100,00100,01110",
"2":"01110,10001,00001,00010,00100,01000,11111","3":"11110,00001,00001,01110,00001,00001,11110",
"4":"00010,00110,01010,10010,11111,00010,00010","5":"11111,10000,11110,00001,00001,10001,01110",
"6":"00110,01000,10000,11110,10001,10001,01110","7":"11111,00001,00010,00100,01000,01000,01000",
"8":"01110,10001,10001,01110,10001,10001,01110","9":"01110,10001,10001,01111,00001,00010,01100",
"-":"00000,00000,00000,11111,00000,00000,00000",".":"00000,00000,00000,00000,00000,00000,00100",
"_":"00000,00000,00000,00000,00000,00000,11111",">":"10000,01000,00100,00010,00100,01000,10000",
" ":"00000,00000,00000,00000,00000,00000,00000",
}

def build(text, cell, split, cursor):
    gap = max(1, cell // 8)
    step = cell + gap
    pad = cell * 2
    x = pad
    rects, word, total_cols = [], 0, 0
    for ch in text.upper():
        rows = G.get(ch, G[" "]).split(",")
        if ch == " ":
            word += 1
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v == "1":
                    cls = "a" if word < split else "b"
                    rects.append((x + c * step, pad + r * step, cls))
        x += 6 * step
    width = x + pad
    height = pad * 2 + 7 * step
    xmax = max(r[0] for r in rects) or 1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{text}">',
    '<style>',
    '.a{fill:#9ca3af}.b{fill:#111827}.k{fill:#111827}',
    '@media(prefers-color-scheme:dark){.a{fill:#6b7280}.b{fill:#e5e7eb}.k{fill:#e5e7eb}}',
    'rect{opacity:0;animation:in .35s ease-out forwards}',
    '@keyframes in{from{opacity:0}to{opacity:1}}',
    '.k{animation:blink 1.1s steps(1) infinite;opacity:1}',
    '@keyframes blink{50%{opacity:0}}',
    '</style>']
    for (rx, ry, cls) in rects:
        d = 0.15 + 1.4 * (rx / xmax)
        out.append(f'<rect class="{cls}" x="{rx}" y="{ry}" width="{cell}" height="{cell}" style="animation-delay:{d:.2f}s"/>')
    if cursor:
        out.append(f'<rect class="k" x="{x}" y="{pad + 5 * step}" width="{cell * 2}" height="{cell}" style="animation-delay:2s"/>')
        width += cell * 3
    out.append('</svg>')
    svg = "\n".join(out)
    if cursor:
        svg = svg.replace(f'viewBox="0 0 {x + pad} {height}" width="{x + pad}"', f'viewBox="0 0 {width} {height}" width="{width}"')
    return svg

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("text"); p.add_argument("-o", "--out", default="title.svg")
    p.add_argument("--cell", type=int, default=9); p.add_argument("--split", type=int, default=1)
    p.add_argument("--no-cursor", action="store_true")
    a = p.parse_args()
    open(a.out, "w", encoding="utf-8").write(build(a.text, a.cell, a.split, not a.no_cursor))
    print("wrote", a.out)
