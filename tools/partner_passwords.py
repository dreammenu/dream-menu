"""Individual partner passwords, alongside the main DM_PASSWORD set in Vercel.

  python3 tools/partner_passwords.py add "Partner name"      make a new password, print it ONCE
  python3 tools/partner_passwords.py add "Name" --password x  use a password you choose (12+ characters)
  python3 tools/partner_passwords.py revoke "Partner name"   stop that password working
  python3 tools/partner_passwords.py list                    who has a password (never the passwords)

Only a slow one-way hash of each password is stored (tools/data/partner-keys.json and a marked block
in middleware.js). The password itself is shown once and kept nowhere in the site or repository, so
note it down before closing the window. Commit and push after any change; it takes effect on deploy.
The main password (DM_PASSWORD in Vercel, used by the first partner) is not touched by this tool.
"""
import datetime, hashlib, json, os, re, secrets, sys

FN = 'tools/data/partner-keys.json'
MW = 'middleware.js'
SALT = b'dream-menu-partner-key-v1'
ITER = 100000
ALPHA = 'abcdefghjkmnpqrstuvwxyz23456789'   # no look-alikes (0/o, 1/l/i)


def digest(pw):
    return hashlib.pbkdf2_hmac('sha256', pw.strip().lower().encode(), SALT, ITER).hex()


def make():
    return 'dm-' + '-'.join(''.join(secrets.choice(ALPHA) for _ in range(4)) for _ in range(3))


def load():
    return json.load(open(FN, encoding='utf-8')) if os.path.exists(FN) else []


def save(keys):
    json.dump(keys, open(FN, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    s = open(MW, encoding='utf-8').read()
    slug = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
    body = ''.join(f"  ['{k['hash']}', '{slug(k['label'])}'], // {k['label']} (added {k['added']})\n" for k in keys)
    s2, n = re.subn(r'(// partner-keys:start\n).*?(// partner-keys:end)', lambda m: m.group(1) + body + m.group(2), s, flags=re.S)
    if n != 1:
        raise SystemExit('middleware.js: partner-keys block not found')
    open(MW, 'w', encoding='utf-8').write(s2)


def main(a):
    keys = load()
    if not a or a[0] == 'list':
        for k in keys:
            print(f"{k['label']:<32} added {k['added']}")
        if a and a[0] == 'list':
            save(keys)   # keeps middleware.js in step with the list
        print(f'{len(keys)} individual passwords, plus the main password set in Vercel (DM_PASSWORD).')
    elif a[0] == 'add' and len(a) >= 2:
        label = a[1].replace('*/', '').replace('\n', ' ').strip()
        if any(k['label'].lower() == label.lower() for k in keys):
            raise SystemExit(f'"{label}" already has a password. Revoke it first to issue a new one.')
        pw = a[a.index('--password') + 1] if '--password' in a else make()
        if len(pw.strip()) < 12:
            raise SystemExit('Use at least 12 characters.')
        keys.append(dict(label=label, hash=digest(pw), added=datetime.date.today().isoformat()))
        save(keys)
        print(f'{label}: {pw.strip().lower()}')
    elif a[0] == 'revoke' and len(a) >= 2:
        left = [k for k in keys if k['label'].lower() != a[1].lower()]
        if len(left) == len(keys):
            raise SystemExit(f'No password found for "{a[1]}".')
        save(left)
        print(f'Revoked: {a[1]}. Commit and push to make it take effect.')
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
