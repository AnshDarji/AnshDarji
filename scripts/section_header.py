"""Generate self-contained, theme-aware section headings (stdlib only)."""
import argparse
from pathlib import Path
from xml.sax.saxutils import escape

HEADINGS = {'about': 'about', 'stack': 'technical stack', 'work': 'featured work',
            'wins': 'achievements', 'stats': 'activity & stats'}

def render(label):
    label = label.lower()
    start = 12 + len(label) * 10 + 28
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="48" viewBox="0 0 720 48" role="img" aria-label="{escape(label)}">
<style>text{{fill:#24292f;font:16px ui-monospace,Consolas,monospace}}line{{stroke:#d0d7de}}@media(prefers-color-scheme:dark){{text{{fill:#e6edf3}}line{{stroke:#30363d}}}}</style>
<text x="12" y="30">{escape(label)}</text><line x1="{start}" y1="25" x2="708" y2="25" stroke-width="1"/>
</svg>'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label', nargs='?')
    parser.add_argument('-o', '--out', type=Path)
    args = parser.parse_args()
    if args.label:
        if not args.out:
            parser.error('--out is required with a label')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render(args.label), encoding='utf-8')
    else:
        Path('assets').mkdir(exist_ok=True)
        for name, label in HEADINGS.items():
            Path(f'assets/h-{name}.svg').write_text(render(label), encoding='utf-8')
