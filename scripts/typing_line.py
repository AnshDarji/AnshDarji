#!/usr/bin/env python3
"""Self-contained typing-effect tagline SVG (no external services).
Usage: python typing_line.py "Actively looking for SDE Summer 2027 internships" -o assets/tagline.svg
"""
import argparse
from xml.sax.saxutils import escape

def build(text, fs=15):
    cw = fs * 0.6
    tw = len(text) * cw
    W, H = int(tw + 40), int(fs * 2.4)
    dur = max(2.0, len(text) * 0.06)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(text)}">
<style>
.t{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:{fs}px;fill:#374151}}
.c{{fill:#374151;animation:blink 1s steps(1) infinite}}
@media(prefers-color-scheme:dark){{.t,.c{{fill:#d1d5db}}}}
@keyframes type{{from{{width:0}}to{{width:{tw:.0f}px}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes move{{from{{transform:translateX(0)}}to{{transform:translateX({tw:.0f}px)}}}}
#m{{animation:type {dur:.1f}s steps({len(text)},end) .8s forwards;width:0}}
.c{{animation:blink 1s steps(1) infinite,move {dur:.1f}s steps({len(text)},end) .8s forwards}}
</style>
<clipPath id="r"><rect id="m" x="20" y="0" height="{H}"/></clipPath>
<text class="t" x="20" y="{fs * 1.55:.1f}" clip-path="url(#r)" xml:space="preserve" textLength="{tw:.1f}" lengthAdjust="spacing">{escape(text)}</text>
<rect class="c" x="20" y="{fs * 0.35:.1f}" width="{cw * 0.7:.1f}" height="{fs * 1.4:.1f}"/>
</svg>'''

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("text"); p.add_argument("-o", "--out", default="tagline.svg"); p.add_argument("--fs", type=float, default=15)
    a = p.parse_args()
    open(a.out, "w", encoding="utf-8").write(build(a.text, a.fs)); print("wrote", a.out)
