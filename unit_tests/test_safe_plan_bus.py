# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Chatboo toast drops when the Safe Plan row is no longer pending."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_toast_listens_for_the_row():
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    for js in (owl2, owl1):
        assert '_dropSafePlanCard' in js
        assert 'pns_verif_' in js
        assert "status === 'pending'" in js or 'status === "pending"' in js
    assert 'subscribe("pns_safe_plan"' in owl2
    assert "type === 'pns_safe_plan'" in owl1
