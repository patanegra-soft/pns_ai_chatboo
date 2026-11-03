# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Slash menu: arrow keys must keep the active row in the overflow list."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_owl1_slash_sync_scrolls_active_row():
    src = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    sync = src.split('Keep the highlighted row in view', 1)[1].split(
        '_syncInputEl', 1,
    )[0]
    assert 'scrollIntoView' in sync
    assert "block: 'nearest'" in sync


def test_owl2_slash_arrows_scroll_active_row():
    js = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    assert 'function _scrollSlashActive' in js or '_scrollSlashActive()' in js
    body = js.split('_scrollSlashActive()', 1)[1].split('onKeydown(ev)', 1)[0]
    assert 'slashMenuRef' in body
    assert 'dropdown-item.active' in body
    assert 'scrollTop' in body
    xml = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    assert 't-ref="slashMenu"' in xml
