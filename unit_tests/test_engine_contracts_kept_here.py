# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""What Chatboo's own files promise the engine: admin-only system skills,
the skipped-capability row on the turn, and no protocol test for the
decision provider.
"""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SYSTEM = _ROOT / 'common' / 'ai' / 'skills' / 'system'


def test_factory_skills_marked_admin_only():
    text = (_SYSTEM / 'users.md').read_text(encoding='utf-8')
    assert 'required_groups: pns_ai_mcp.group_ai_admin' in text


def test_canvas_threads_its_skipped_row_like_the_engine():
    canvas = (_ROOT / 'common' / 'models' / 'chatboo_canvas.py').read_text(
        encoding='utf-8',
    )
    body = canvas.split('def log_no_page', 1)[1].split('\ndef ', 1)[0]
    assert 'CAPABILITY_SKIPPED' in body
    assert '_resolve_log_threading()' in body
    assert 'turn=turn,' in body
    assert 'turn_step=turn_step,' in body


def test_chat_controller_does_not_pick_the_decision_provider():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
        ).read_text(encoding='utf-8')
        assert "'decision'" not in src
