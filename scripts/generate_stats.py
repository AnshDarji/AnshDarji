"""GitHub-only profile stats. Stdlib; token never written to output.

Uses a rolling 365-day UTC window. Current streak may end today or yesterday;
longest streak is within this window (earliest range wins ties). Languages are
bytes across owned public repositories, including forks, with full pagination.
GITHUB_TOKEN can only report data its GitHub installation is allowed to read.
--mock produces clearly labelled preview assets without network requests.
"""
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

API = 'https://api.github.com/graphql'

def graphql(query, variables, token):
    request = Request(API, data=json.dumps({'query': query, 'variables': variables}).encode(),
                      headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                               'User-Agent': 'profile-stats', 'Accept': 'application/vnd.github+json'})
    try:
        with urlopen(request, timeout=45) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f'GitHub GraphQL HTTP {error.code}; existing assets preserved') from None
    except URLError:
        raise RuntimeError('GitHub GraphQL connection failed; existing assets preserved') from None
    if result.get('errors') or not result.get('data'):
        raise RuntimeError('GitHub GraphQL returned errors; check token permissions and query')
    return result['data']

def fetch(login, today, token):
    start = today - timedelta(days=364)
    data = graphql('''query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){contributionsCollection(from:$from,to:$to){
        contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}
      }}}''', {'login': login, 'from': start.isoformat()+'T00:00:00Z',
               'to': today.isoformat()+'T23:59:59Z'}, token)
    if not data['user']:
        raise RuntimeError('GitHub user not found')
    calendar = data['user']['contributionsCollection']['contributionCalendar']
    days = {d['date']: d['contributionCount'] for w in calendar['weeks'] for d in w['contributionDays']}
    languages, cursor = Counter(), None
    while True:
        connection = graphql('''query($login:String!,$cursor:String){user(login:$login){
          repositories(first:100,after:$cursor,ownerAffiliations:[OWNER],privacy:PUBLIC){
            nodes{name} pageInfo{hasNextPage endCursor}}}}''',
          {'login': login, 'cursor': cursor}, token)['user']['repositories']
        for repo in connection['nodes']:
            lang_cursor = None
            while True:
                lang = graphql('''query($owner:String!,$name:String!,$cursor:String){
                  repository(owner:$owner,name:$name){languages(first:100,after:$cursor){
                    edges{size node{name}} pageInfo{hasNextPage endCursor}}}}''',
                  {'owner': login, 'name': repo['name'], 'cursor': lang_cursor}, token)['repository']['languages']
                for edge in lang['edges']:
                    languages[edge['node']['name']] += edge['size']
                if not lang['pageInfo']['hasNextPage']:
                    break
                lang_cursor = lang['pageInfo']['endCursor']
                if not lang_cursor:
                    raise RuntimeError('Missing language pagination cursor')
        if not connection['pageInfo']['hasNextPage']:
            break
        cursor = connection['pageInfo']['endCursor']
        if not cursor:
            raise RuntimeError('Missing repository pagination cursor')
    return days, languages

def summarize(days, today):
    start = today - timedelta(days=364)
    sequence = [(start+timedelta(days=i), max(0, int(days.get((start+timedelta(days=i)).isoformat(), 0)))) for i in range(365)]
    weekly = Counter()
    best, run, best_start, best_end = 0, 0, None, None
    for day, count in sequence:
        weekly[day-timedelta(days=day.weekday())] += count
        if count:
            run += 1
            if run > best:
                best, best_start, best_end = run, day-timedelta(days=run-1), day
        else:
            run = 0
    end = 364 if sequence[-1][1] else 363
    current = 0
    while end >= 0 and sequence[end][1]:
        current += 1
        end -= 1
    return {'total': sum(n for _, n in sequence), 'weekly': list(weekly.values()),
            'current': current, 'longest': best,
            'range': f'{best_start} – {best_end}' if best else 'No streak in this window'}

def render(days, languages, today, theme, mock=False):
    stats = summarize(days, today)
    dark = theme == 'dark'
    bg, fg, muted, accent = ('#0d1117','#e6edf3','#9aa5b1','#8aa3b5') if dark else ('#ffffff','#24292f','#576574','#526e82')
    shades = [accent] + (['#b6bdc5','#929ba5','#737e89','#596571','#424e5a'] if dark else ['#747f8a','#939da6','#b0b8bf','#ccd2d7','#e2e6e9'])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 420" width="720" height="420" role="img" aria-label="GitHub activity statistics">',
             f'<rect width="720" height="420" fill="{bg}"/>',
             f'<style>text{{font-family:ui-monospace,Consolas,monospace;fill:{fg};font-size:14px}}.label{{fill:{muted};font-size:12px}}.number{{font-size:32px;font-weight:600}}</style>']
    def text(x,y,value,cls='',**attrs):
        extra = ' '.join(f'{k.replace("_", "-")}="{escape(str(v))}"' for k,v in attrs.items())
        parts.append(f'<text x="{x}" y="{y}" class="{cls}" {extra}>{escape(str(value))}</text>')
    text(24,22,'MOCK DATA — preview only' if mock else f'Updated {today} · UTC · last 365 days','label')
    text(24,64,'contributions, last year','label')
    text(24,104,f'{stats["total"]:,}','number')
    weekly = stats['weekly']
    step, peak = 400/len(weekly), max(weekly,default=0) or 1
    for i,count in enumerate(weekly):
        height = max(1, count/peak*65)
        parts.append(f'<rect x="{288+i*step:.2f}" y="{114-height:.2f}" width="{max(1,step-2):.2f}" height="{height:.2f}" fill="{accent}"/>')
    text(288,133,'weekly contributions','label')
    text(24,174,'current streak','label'); text(24,211,f'{stats["current"]}d','number')
    text(360,174,'longest streak · last year','label'); text(360,211,f'{stats["longest"]}d','number')
    text(360,234,stats['range'],'label')
    text(24,274,'top languages · bytes in owned public repos','label')
    ranked = sorted(((k,v) for k,v in languages.items() if v > 0), key=lambda x:(-x[1],x[0]))
    if len(ranked)>6:
        ranked = ranked[:5]+[('Other',sum(v for _,v in ranked[5:]))]
    total = sum(v for _,v in ranked)
    if not total:
        text(24,311,'No language bytes available','label')
    else:
        x = 24
        for i,(name,value) in enumerate(ranked):
            width = 672*value/total
            parts.append(f'<rect x="{x:.3f}" y="292" width="{width:.3f}" height="12" fill="{shades[i]}"/>')
            x += width
            lx,ly = 24+(i%2)*336, 332+(i//2)*27
            parts.append(f'<rect x="{lx}" y="{ly-9}" width="8" height="8" fill="{shades[i]}"/>')
            text(lx+16,ly,f'{name}  {100*value/total:.1f}%', **({'textLength':290,'lengthAdjust':'spacingAndGlyphs'} if len(name)>24 else {}))
    parts.append('</svg>')
    return '\n'.join(parts)

def mock_data(today):
    start = today-timedelta(days=364)
    days = {(start+timedelta(days=i)).isoformat(): (i%9+1 if i%13<8 else 0) for i in range(365)}
    return days, {'Python':51000,'C++':27000,'JavaScript':12000,'HTML':5000,'CSS':3000,'Shell':2000}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user', default=os.environ.get('GITHUB_REPOSITORY_OWNER','AnshDarji'))
    parser.add_argument('--out-dir', type=Path, default=Path('assets'))
    parser.add_argument('--mock', action='store_true')
    args = parser.parse_args()
    today = datetime.now(timezone.utc).date()
    if args.mock:
        today = date(2026,9,28)
        days,languages = mock_data(today)
    else:
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            parser.error('GITHUB_TOKEN is required; use --mock for offline previews')
        days,languages = fetch(args.user,today,token)
    assets = {theme:render(days,languages,today,theme,args.mock) for theme in ('dark','light')}
    for svg in assets.values():
        ET.fromstring(svg)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    for theme,svg in assets.items():
        path = args.out_dir/f'stats-{theme}.svg'
        temporary = path.with_suffix('.tmp')
        temporary.write_text(svg,encoding='utf-8')
        temporary.replace(path)

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, KeyError) as error:
        print(f'Stats generation failed: {error}',file=sys.stderr)
        sys.exit(1)
