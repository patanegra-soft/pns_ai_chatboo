# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Last chat card must sit above the prompt, not under a 65px footer guess."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_owl1_messages_use_flex_not_fixed_footer_gap():
    src = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    assert 'bottom: 65px' not in src
    assert 'flex: 1 1 auto; min-height: 0' in src
    assert 'flex-direction: column' in src
    css = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'css' / 'chatboo_floating.css'
    ).read_text(encoding='utf-8')
    assert 'padding-bottom: 1.75rem' in css


def test_owl2_messages_keep_space_above_prompt():
    css = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'css' / 'chatboo_app.css'
    ).read_text(encoding='utf-8')
    assert 'padding-bottom: 1.75rem' in css
    js = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    help_fn = js.split('    _showBuiltinHelp(', 1)[1].split('    _matchBuiltinCommand', 1)[0]
    assert 'this._scrollSoon()' in help_fn
