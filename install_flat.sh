#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
#
# install_flat.sh — Build a plain Odoo module folder for one Odoo series
# from this multi-version tree (common/ + stacks/).
#
#   ./install_flat.sh 19.0 ~/odoo/custom-addons
#   ./install_flat.sh 14.0 /tmp/addons-14
#
# Result: <addons_dir>/<module>/ with __manifest__.py at its root, ready for
# addons_path. Odoo 14 uses stacks/owl1, Odoo 16 to 19 stacks/owl2, and
# Odoo 20 and later stacks/owl3. Odoo 15 has Owl 1 and the old views, so it
# uses stacks/owl1 with its own manifest (__manifest_o15__.py: assets in the
# manifest); a tree without that file gives Odoo 15 stacks/owl2.
# The flat manifest carries the series in its version and the banner in
# images, as the Odoo Apps Store reads them.
# Odoo 13 and older are not supported (README, "Odoo versions").
# An existing <addons_dir>/<module>/ is replaced.

set -euo pipefail

# Series with a published branch, written by publish.sh from publish.conf.
TESTED_SERIES="14.0 15.0 16.0 17.0 18.0 19.0 20.0"

die() { echo "Error: $*" >&2; exit 1; }

[ $# -ge 2 ] || die "usage: $0 <odoo-series, e.g. 19.0> <addons_dir> [owl1|owl2|owl3]"

SERIES="$1"
DEST="$2"
STACK="${3:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

major="${SERIES%%.*}"
[[ "$major" =~ ^[0-9]+$ ]] || die "Odoo series must look like 19.0, got: $SERIES"
[ "$major" -ge 14 ] || die "Odoo $SERIES is not supported: this suite starts at 14.0 (README, \"Odoo versions\")"
if [ -z "$STACK" ]; then
    if [ "$major" -eq 14 ]; then STACK=owl1; elif [ "$major" -ge 20 ]; then STACK=owl3; else STACK=owl2; fi
    if [ "$major" -eq 15 ] && compgen -G "$ROOT/stacks/owl1/*/__manifest_o15__.py" >/dev/null; then
        STACK=owl1
    fi
fi
if [ -n "$TESTED_SERIES" ] && [[ " $TESTED_SERIES " != *" $SERIES "* ]]; then
    echo "Warning: Odoo $SERIES is not tested yet (tested: $TESTED_SERIES). It may need changes." >&2
fi
[ -d "$ROOT/stacks/$STACK" ] || die "this tree has no stacks/$STACK (Odoo $SERIES)"

SRC=""
for dir in "$ROOT/stacks/$STACK"/*/; do
    [ -f "${dir}__manifest__.py" ] || continue
    [ -z "$SRC" ] || die "more than one module in stacks/$STACK"
    SRC="${dir%/}"
done
[ -n "$SRC" ] || die "no module in stacks/$STACK"
MODULE="$(basename "$SRC")"

mkdir -p "$DEST"
OUT="$(cd "$DEST" && pwd)/$MODULE"
rm -rf "$OUT"
mkdir "$OUT"

# Same layering as the internal installer: common, then adapters, then the stack.
[ -d "$ROOT/common" ] && cp -a "$ROOT/common/." "$OUT/"
[ -d "$ROOT/adapters" ] && cp -a "$ROOT/adapters" "$OUT/"
cp -a "$SRC/." "$OUT/"
if [ -f "$OUT/__manifest_o15__.py" ]; then
    if [ "$major" -eq 15 ]; then
        mv -f "$OUT/__manifest_o15__.py" "$OUT/__manifest__.py"
    else
        rm -f "$OUT/__manifest_o15__.py"
    fi
fi

for f in README.md CHANGELOG.md LICENSE NOTICE CONTRIBUTING.md SECURITY.md; do
    if [ -f "$ROOT/$f" ] && [ ! -e "$OUT/$f" ]; then
        cp "$ROOT/$f" "$OUT/$f"
    fi
done

if [ -f "$OUT/README.md" ]; then
    sed 's|common/static/description/|static/description/|g' "$OUT/README.md" > "$OUT/README.md.tmp"
    mv "$OUT/README.md.tmp" "$OUT/README.md"
fi

# What the Odoo Apps Store reads from a flat module:
# - version with the series first (19.0.2.1.542). Odoo adds the same prefix
#   when it loads a version without it, so the installed version is the same.
# - images: banner_store.png (2:1, the store crops wider pictures to that),
#   else banner.png, when the manifest names none.
# - index.html in ASCII: accents as HTML entities (same page in a browser).
# - index.html with its CSS also in style attributes: the store drops <style>.
command -v python3 >/dev/null || die "python3 is needed to write the flat manifest"
python3 - "$OUT" "$SERIES" <<'PY'
import os
import re
import sys

out, series = sys.argv[1], sys.argv[2]
path = os.path.join(out, '__manifest__.py')
with open(path, encoding='utf-8') as fh:
    text = fh.read()


def prefixed(match):
    version = match.group(2)
    if version.startswith(series + '.'):
        return match.group(0)
    return '%s%s.%s%s' % (match.group(1), series, version, match.group(3))


text = re.sub(r"""(['"]version['"]\s*:\s*['"])([^'"]+)(['"])""", prefixed, text, count=1)
banner = next((b for b in ('static/description/banner_store.png',
                            'static/description/banner.png')
               if os.path.isfile(os.path.join(out, b))), None)
if banner and not re.search(r"""['"]images['"]\s*:""", text):
    text = re.sub(r"""(\n(\s*)['"]version['"]\s*:[^\n]*\n)""",
                  lambda m: "%s%s'images': ['%s'],\n" % (m.group(1), m.group(2), banner),
                  text, count=1)
with open(path, 'w', encoding='utf-8') as fh:
    fh.write(text)

COMPOUND = re.compile(r'^([a-zA-Z][\w-]*)?((?:\.[\w-]+)*)$')
START = re.compile(r'''<([a-zA-Z][\w-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>''')
END = re.compile(r'</([a-zA-Z][\w-]*)\s*>')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'source', 'track', 'wbr'}


def selector(text):
    """[(tag, classes)] for 'tag.class tag .class', or None for anything else."""
    parts = []
    for word in text.split():
        m = COMPOUND.match(word)
        if not m or not word:
            return None
        parts.append(((m.group(1) or '').lower(), set(m.group(2).split('.')) - {''}))
    return parts or None


def declarations(body):
    pairs = []
    for item in body.split(';'):
        prop, sep, value = item.partition(':')
        if sep and prop.strip() and value.strip():
            pairs.append((prop.strip().lower(), value.strip()))
    return pairs


def important(pairs):
    return '; '.join('%s: %s%s' % (p, v, '' if '!important' in v else ' !important')
                     for p, v in pairs)


COLOR = re.compile(r'^(#[0-9a-fA-F]{3,8}|(rgb|hsl)a?\([^()]*\)|[a-zA-Z]+)$')
BORDER_STYLES = {'none', 'hidden', 'dotted', 'dashed', 'solid', 'double',
                 'groove', 'ridge', 'inset', 'outset'}
BORDER_WIDTH = re.compile(r'^([\d.]+[a-z%]*|thin|medium|thick)$')


def store_safe(merged):
    """Same look, written with properties Odoo's sanitizer keeps.

    It keeps background-color but not background, and border-<side>-width,
    -style and -color but not border-<side> (except top and bottom).
    """
    out = {}
    for prop, value in merged.items():
        side = re.match(r'^border-(left|right)$', prop)
        if prop == 'background' and COLOR.match(value) and value.lower() != 'none':
            out['background-color'] = value
        elif side:
            parts = re.findall(r'\w+\([^()]*\)|\S+', value)
            width = next((p for p in parts if BORDER_WIDTH.match(p)), None)
            style = next((p for p in parts if p.lower() in BORDER_STYLES), None)
            color = next((p for p in parts if p not in (width, style)), None)
            for key, val in (('width', width), ('style', style), ('color', color)):
                if val:
                    out['border-%s-%s' % (side.group(1), key)] = val
        else:
            out[prop] = value
    return out


def matches(sel, tag, classes, ancestors):
    def fits(part, t, c):
        return (not part[0] or part[0] == t) and part[1] <= c
    if not fits(sel[-1], tag, classes):
        return False
    rest = sel[:-1]
    for t, c, *_ in reversed(ancestors):
        if rest and fits(rest[-1], t, c):
            rest = rest[:-1]
    return not rest


def inline_styles(html):
    """Copy the page's CSS into style attributes.

    The Apps Store drops <style> from the description; it keeps style
    attributes. Rules made only of tags and classes go inline. The rest
    (:target, pseudo-classes, @media, *) stays in <style> with !important,
    so it still wins over the inline copy where a stylesheet is read.
    """
    block = re.search(r'(?is)(<style[^>]*>)(.*?)(</style>)', html)
    if not block:
        return html
    css = re.sub(r'(?s)/\*.*?\*/', '', block.group(2))
    rules, kept, i = [], [], 0
    while True:
        j = css.find('{', i)
        if j < 0:
            break
        prelude = css[i:j].strip()
        if prelude.startswith('@'):
            depth, k = 1, j + 1
            while k < len(css) and depth:
                depth += {'{': 1, '}': -1}.get(css[k], 0)
                k += 1
            inner = re.sub(r'([^{}]+)\{([^{}]*)\}',
                           lambda m: '  %s { %s }\n' % (m.group(1).strip(),
                                                        important(declarations(m.group(2)))),
                           css[j + 1:k - 1])
            kept.append('%s {\n%s}' % (prelude, inner))
            i = k
            continue
        k = css.find('}', j)
        pairs = declarations(css[j + 1:k])
        other = []
        for text in prelude.split(','):
            sel = selector(text)
            if sel:
                spec = (sum(len(c) for _, c in sel), sum(1 for t, _ in sel if t))
                rules.append((spec, len(rules), sel, pairs))
            elif text.strip():
                other.append(text.strip())
        if other:
            kept.append('%s { %s }' % (', '.join(other), important(pairs)))
        i = k + 1
    rules.sort(key=lambda r: (r[0], r[1]))

    stack, out = [], []

    def start(m):
        tag, attrs = m.group(1).lower(), m.group(2)
        cls = re.search(r'''\sclass\s*=\s*["']([^"']*)["']''', attrs)
        classes = set(cls.group(1).split()) if cls else set()
        merged = {}
        for _, _, sel, pairs in rules:
            if matches(sel, tag, classes, stack):
                for p, v in pairs:
                    merged.pop(p, None)
                    merged[p] = v.replace('"', "'")
        # The sanitizer drops gap and justify-content. In a flex row both come
        # back as margin-left on every child but the first: the gap itself,
        # or auto, which shares the free space like space-between.
        if stack:
            parent = stack[-1]
            if parent[2] and parent[3] and 'margin-left' not in merged and 'margin' not in merged:
                merged['margin-left'] = parent[2]
            parent[3] += 1
        gap = None
        if merged.get('display') in ('flex', 'inline-flex') \
                and merged.get('flex-direction', 'row') == 'row':
            spread = merged.get('justify-content') == 'space-between'
            if 'gap' in merged and not spread:
                gap = merged.pop('gap').split()[-1]
            elif spread and 'gap' not in merged:
                gap = 'auto'
                merged.pop('justify-content')
        if not (tag in VOID or attrs.rstrip().endswith('/')):
            stack.append([tag, classes, gap, 0])
        if not merged:
            return m.group(0)
        style = '; '.join('%s: %s' % kv for kv in store_safe(merged).items())
        own = re.search(r'''\sstyle\s*=\s*(["'])(.*?)\1''', attrs, re.S)
        if own:
            attrs = attrs[:own.start()] + ' style="%s; %s"' % (style, own.group(2)) + attrs[own.end():]
        elif attrs.rstrip().endswith('/'):
            attrs = attrs.rstrip()[:-1].rstrip() + ' style="%s" /' % style
        else:
            attrs = attrs.rstrip() + ' style="%s"' % style
        return '<%s%s>' % (m.group(1), attrs)

    def end(m):
        tag = m.group(1).lower()
        if any(entry[0] == tag for entry in stack):
            while stack and stack.pop()[0] != tag:
                pass
        return m.group(0)

    html = html[:block.start(2)] + '\n' + '\n'.join(kept) + '\n' + html[block.end(2):]
    for piece in re.split(r'(?is)(<!--.*?-->|<style.*?</style>|<script.*?</script>)', html):
        if re.match(r'(?is)<(!--|style|script)', piece):
            out.append(piece)
            continue
        pos = 0
        for m in re.finditer(r'%s|%s' % (START.pattern, END.pattern), piece):
            out.append(piece[pos:m.start()])
            sm, em = START.fullmatch(m.group(0)), END.fullmatch(m.group(0))
            out.append(start(sm) if sm else end(em))
            pos = m.end()
        out.append(piece[pos:])
    return ''.join(out)


page = os.path.join(out, 'static', 'description', 'index.html')
if os.path.isfile(page):
    with open(page, encoding='utf-8') as fh:
        html = inline_styles(fh.read())
    parts = re.split(r'(?is)(<style.*?</style>|<script.*?</script>)', html)
    for i in range(0, len(parts), 2):
        parts[i] = ''.join(c if ord(c) < 128 else '&#%d;' % ord(c) for c in parts[i])
    with open(page, 'w', encoding='ascii') as fh:
        fh.write(''.join(parts))
PY

find "$OUT" -name '__pycache__' -type d -prune -exec rm -rf {} +

echo "$OUT  (Odoo $SERIES, $STACK)"
