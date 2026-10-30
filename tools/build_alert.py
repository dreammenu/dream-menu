#!/usr/bin/env python3
"""Writes the partner mover alert for Dunns from partner/briefing-extra.js:
tools/data/alerts/<data date>.txt and .html (newly clear, no longer clear, top five trend scores).
Claude puts the alert into Gmail as a draft for Gordon to check and send; the files are the record.

Run after build_briefing_extras.py:  python3 tools/build_alert.py
"""
import datetime as dt, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
s = open('partner/briefing-extra.js', encoding='utf-8').read()
X = json.loads(s[s.index('=') + 1:].strip().rstrip(';'))
d = lambda x: dt.date.fromisoformat(x).strftime('%-d %B %Y')
sg = lambda v: f'{"+" if v > 0 else ""}{v:.1f}'
E = html.escape
C = X['changes']
name = lambda r: f'{r["l"]} ({r["course"].lower()}{", group" if r["level"] == "Group" else ""})'

subject = f'Dream Menu partner alert: what moved, data to {d(X["last"])}'
txt = [f'Dream Menu partner alert, data to {d(X["last"])}', '']
htm = [f'<p><b>Dream Menu partner alert</b>, data to {d(X["last"])}.</p>']
if C:
    txt.append(f'Compared with the last briefing (data to {d(C["since"])}):')
    htm.append(f'<p>Compared with the last briefing (data to {d(C["since"])}):</p><ul>')
    for title, rows, f in (('Newly clear', C['new'], lambda r: f'{name(r)}: {sg(r["move"])} pts'),
                           ('No longer clear', C['gone'], lambda r: f'{name(r)}: was {sg(r["was"])} pts'),
                           ('Still clear, biggest', C['kept'][:5], lambda r: f'{name(r)}: {sg(r["move"])} pts')):
        txt.append(f'- {title}: ' + ('; '.join(f(r) for r in rows) if rows else 'none'))
        htm.append(f'<li><b>{title}:</b> ' + (E('; '.join(f(r) for r in rows)) if rows else 'none') + '</li>')
    htm.append('</ul>')
top = X['score'][:5]
txt += ['', 'Top trend scores (out of 10): ' + '; '.join(f'{o["l"]} ({o["cl"].lower()}) {o["s10"]:.1f}, {o["tier"]}' for o in top), '',
        'Full detail, by course and by Dunns range: https://www.dream-menu.com/briefing (partner sign-in).']
htm += ['<p><b>Top trend scores</b> (out of 10): ' + E('; '.join(f'{o["l"]} ({o["cl"].lower()}) {o["s10"]:.1f}, {o["tier"]}' for o in top)) + '</p>',
        '<p>Full detail, by course and by Dunns range, is in the <a href="https://www.dream-menu.com/briefing">partner briefing</a> (sign-in needed).</p>']
os.makedirs('tools/data/alerts', exist_ok=True)
open(f'tools/data/alerts/{X["last"]}.txt', 'w', encoding='utf-8').write(subject + '\n\n' + '\n'.join(txt) + '\n')
open(f'tools/data/alerts/{X["last"]}.html', 'w', encoding='utf-8').write(''.join(htm))
print(subject)
print('\n'.join(txt))
