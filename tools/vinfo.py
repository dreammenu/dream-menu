"""Shared 'How to read this' note for charts. Used by builders and by build_info.py."""
import re

RE = re.compile(r'<details class="vinfo">.*?</details>', re.S)


def vinfo(text, label='How to read this'):
    """text: plain HTML sentences. Kept short: what it shows, how to read it, one caution."""
    if not text:
        return ''
    paras = ''.join(f'<p>{p.strip()}</p>' for p in text.split('\n') if p.strip())
    return (f'<details class="vinfo"><summary><span class="vi-i" aria-hidden="true">i</span>{label}</summary>'
            f'<div class="vi-b">{paras}</div></details>')


def strip(s):
    return RE.sub('', s)
