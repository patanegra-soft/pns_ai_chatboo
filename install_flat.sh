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

find "$OUT" -name '__pycache__' -type d -prune -exec rm -rf {} +

echo "$OUT  (Odoo $SERIES, $STACK)"
