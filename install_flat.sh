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
# addons_path. Odoo 14 uses stacks/owl1; Odoo 15 and later use stacks/owl2.
# The flat manifest carries the series in its version and the banner in
# images, as the Odoo Apps Store reads them.
# Odoo 13 and older are not supported (README, "Odoo versions").
# An existing <addons_dir>/<module>/ is replaced.

set -euo pipefail

# Series with a published branch, written by publish.sh from publish.conf.
TESTED_SERIES="14.0 19.0"

die() { echo "Error: $*" >&2; exit 1; }

[ $# -ge 2 ] || die "usage: $0 <odoo-series, e.g. 19.0> <addons_dir> [owl1|owl2]"

SERIES="$1"
DEST="$2"
STACK="${3:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

major="${SERIES%%.*}"
[[ "$major" =~ ^[0-9]+$ ]] || die "Odoo series must look like 19.0, got: $SERIES"
[ "$major" -ge 14 ] || die "Odoo $SERIES is not supported: this suite starts at 14.0 (README, \"Odoo versions\")"
if [ -z "$STACK" ]; then
    if [ "$major" -eq 14 ]; then STACK=owl1; else STACK=owl2; fi
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

page = os.path.join(out, 'static', 'description', 'index.html')
if os.path.isfile(page):
    with open(page, encoding='utf-8') as fh:
        html = fh.read()
    parts = re.split(r'(?is)(<style.*?</style>|<script.*?</script>)', html)
    for i in range(0, len(parts), 2):
        parts[i] = ''.join(c if ord(c) < 128 else '&#%d;' % ord(c) for c in parts[i])
    with open(page, 'w', encoding='ascii') as fh:
        fh.write(''.join(parts))
PY

find "$OUT" -name '__pycache__' -type d -prune -exec rm -rf {} +

echo "$OUT  (Odoo $SERIES, $STACK)"
