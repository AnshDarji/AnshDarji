"""Rebuild the original portrait SVGs from saved ASCII rows, without Pillow."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

def main():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root/'scripts/portrait_rows.json').read_text(encoding='utf-8'))
    for theme,portrait in data.items():
        lines = [portrait['prefix']]
        for row in portrait['rows']:
            lines.append(row['prefix'] + escape(row['text']) + '</text>')
        lines.append('</svg>')
        (root/f'assets/face-{theme}.svg').write_text('\n'.join(lines),encoding='utf-8')

if __name__ == '__main__':
    main()
