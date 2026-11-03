# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Vendored PDF libs stay on a patched jsPDF; unused SheetJS is not shipped."""
from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_STACKS = _ROOT / 'stacks'
_JSPDF_FIXED = (3, 0, 2)


def _js(stack, name):
    return _STACKS / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js' / name


def test_jspdf_is_patched_in_both_stacks():
    for stack in ('owl1', 'owl2'):
        head = _js(stack, 'jspdf.umd.min.js').read_text(encoding='utf-8')[:400]
        found = re.search(r'Version (\d+)\.(\d+)\.(\d+)', head)
        assert found, stack
        assert tuple(int(p) for p in found.groups()) >= _JSPDF_FIXED, stack
        auto = _js(stack, 'jspdf.plugin.autotable.min.js').read_text(encoding='utf-8')[:400]
        assert re.search(r'AutoTable plugin v[5-9]\.', auto), stack


def test_sheetjs_is_not_shipped():
    assets = (_STACKS / 'owl1' / 'pns_ai_chatboo' / 'views' / 'assets.xml').read_text(encoding='utf-8')
    manifest = (_STACKS / 'owl2' / 'pns_ai_chatboo' / '__manifest__.py').read_text(encoding='utf-8')
    assert 'xlsx.full' not in assets
    assert 'xlsx.full' not in manifest
    assert not list(_ROOT.glob('common/static/**/xlsx*.js'))
    assert not list(_STACKS.glob('*/pns_ai_chatboo/static/**/xlsx*.js'))


def test_skill_fallback_lookup_hides_other_users_private_skills():
    src = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')
    body = src.split('def _command_resolves_skill', 1)[1].split('\n    def ', 1)[0]
    assert 'Skill.filter_visible_for_user(' in body
    assert "Skill.search([('active', '=', True)], limit=80)\n" not in body
