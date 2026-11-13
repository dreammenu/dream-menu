"""Add a subtle "How to read this" note to the charts on hand-made and generated static pages.

Run near the end of the pipeline (after build_home.py and build_venue_pages.py, before build_nav.py).
Safe to rerun: existing notes in the files it touches are removed first.
Charts drawn by script carry their own notes (dmviz.js INFO, dish-move.js, map.html), and case-study
exhibits get theirs from tools/cs_kit.py.
"""
import glob, re, sys
from vinfo import vinfo, strip

# (file pattern, regex marking the insertion point, 'before' or 'after', note). Notes say what the chart shows,
# how to read it and one caution. Repeated cards share one note placed above the group.
RULES = [
    # ---- home
    ('index.html', r'<div class="mf">Share of answers for each course</div>', 'after',
     'The single most-named dish in each course, with its share of that course’s answers. Shares look small because guests name hundreds of different dishes, so a dish on 8% is a clear leader.'),
    ('index.html', r'<div class="cgrid">', 'before',
     'Each card is one course. The percentage is the share of that course’s answers naming the dish; bars are scaled so the leader fills its row.\nAnswers that fit no dish are left out, so shares are of answers we could code.'),
    ('index.html', r'<div class="dgrid">', 'before',
     'Each bar splits every answer to one question and adds up to 100%. The large figure is the winning answer and the count beneath is how many guests answered.'),
    ('index.html', r'<div class="two">\s*<article class="lcard"><h3>Guilty pleasures', 'before',
     'Each figure is the share of all interviews naming that answer. Guests name one each and many skip the question, so the shares are small and do not add up to 100%.\nRead the order and the gaps between items rather than the size of any one figure.'),
    # ---- partner insights and briefing
    ('insights.html', r'<div id="in-courses">', 'before',
     'Each card is one course: first the share of answers by food group, then by single dish. Bars are scaled to the top item and the figure is the true share.\nGroups and dishes are two cuts of the same answers, so their figures will not match.'),
    ('insights.html', r'<div id="in-guilty">', 'before',
     'The number of guests naming each answer, most named first. These are counts across all interviews, so read them as a ranking.'),
    ('insights.html', r'<div id="in-bin">', 'before',
     'The number of guests naming each trend they would happily see go, most named first. Read it as a ranking of fatigue.'),
    ('insights.html', r'<div class="qchart"', 'before',
     'Interviews received each quarter. The latest quarter is still running, so its column will keep growing; findings use quarters with enough answers to be reliable.'),
    # ---- operator pulse report and one-pager
    ('report/operator-pulse.html', r'<p>Share naming each as a most significant pressure\.</p>', 'after',
     'Each bar is the share of operators naming that pressure. Operators could name several, so the bars do not add up to 100%.'),
    ('onepager.html', r'<div id="op-scot">', 'before',
     'Each bar is the dish’s share of all answers from guests naming Scottish venues, scaled so the leader fills the bar.'),
    # ---- venue pages
    ('venue/*.html', r'<h2>What guests name here</h2>', 'after',
     'Each bar is a dish guests named at this venue, with how many times. With numbers this small, one or two mentions is a pointer, not a verdict.'),
    ('venue/*.html', r'<h2>For which course</h2>', 'after',
     'Which part of the dream menu guests chose this venue for. "Hidden gem or next stop" means it was named as a place to try, rather than for one dish.'),
]


def run():
    done, missing = {}, []
    files = {}
    for pat, rx, where, text in RULES:
        for fn in sorted(glob.glob(pat)):
            files.setdefault(fn, []).append((rx, where, text, '*' in pat))
    for fn, rules in files.items():
        s0 = open(fn, encoding='utf-8').read()
        s = strip(s0)
        for rx, where, text, many in rules:
            note = vinfo(text)
            m = re.search(rx, s, re.S)
            if not m:
                if not many:
                    missing.append(f'{fn}: {rx[:50]}')
                continue
            i = m.start() if where == 'before' else m.end()
            s = s[:i] + note + s[i:]
            done[fn] = done.get(fn, 0) + 1
        if s != s0:
            open(fn, 'w', encoding='utf-8').write(s)
    pages = len(done)
    notes = sum(done.values())
    print(f'chart notes: {notes} on {pages} pages')
    if missing:
        print('not found (check the page still has this chart):\n  ' + '\n  '.join(missing))
        if '--strict' in sys.argv:
            raise SystemExit(1)


if __name__ == '__main__':
    run()
