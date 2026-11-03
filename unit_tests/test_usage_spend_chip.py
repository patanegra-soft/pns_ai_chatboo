# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Footer chips: yellow spend, pastel buffer levels by context occupancy."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_spend_chip_yellow_and_buffer_levels_owl1_and_owl2():
    owl1_js = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    owl2_xml = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    assert 'o_chatboo_usage_chip--spend' in owl1_js
    assert 'o_chatboo_usage_chip--spend' in owl2_xml
    assert 'o_chatboo_usage_chip--buffer-' in owl1_js
    assert 'o_chatboo_usage_chip--buffer-{{ msg.contextInfo.bufferLevel }}' in owl2_xml
    for rel in (
        'stacks/owl1/pns_ai_chatboo/static/src/css/chatboo_floating.css',
        'stacks/owl2/pns_ai_chatboo/static/src/css/chatboo_floating.css',
    ):
        css = (_ROOT / rel).read_text(encoding='utf-8')
        spend = css.split('.o_chatboo_usage_chip--spend {', 1)[1].split('}', 1)[0]
        assert 'background: #ffe082' in spend
        assert 'color: #1d1d1d' in spend
        assert '.o_chatboo_usage_chip--buffer-ok {' in css
        assert '.o_chatboo_usage_chip--buffer-warn {' in css
        assert '.o_chatboo_usage_chip--buffer-danger {' in css
        base = css.split('.o_chatboo_usage_chip {', 1)[1].split('}', 1)[0]
        assert 'border: 1px solid #e9ecef' in base
