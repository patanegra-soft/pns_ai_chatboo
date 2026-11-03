# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Chatboo brings its own door to the engine's log and change journal."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_chatboo_adds_its_door():
    door = (_ROOT / 'common' / 'models' / 'ai_log_door.py').read_text(encoding='utf-8')
    assert "DOOR = ('chatboo', 'Chatboo')" in door
    assert door.count('selection_add=[DOOR]') == 2
    assert door.count('ondelete={DOOR[0]: _keep_rows}') == 2
    assert "_inherit = 'ai.log'" in door
    assert "_inherit = 'ai.change.journal'" in door
    for init in (
        _ROOT / 'common' / 'models' / '__init__.py',
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'models' / '__init__.py',
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'models' / '__init__.py',
    ):
        assert 'from . import ai_log_door' in init.read_text(encoding='utf-8')


def test_chatboo_stamps_its_door_and_filters_it():
    for stack in ('owl1', 'owl2'):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
        controller = (base / 'controllers' / 'chatboo.py').read_text(encoding='utf-8')
        assert "request.mcp_source_channel = 'chatboo'" in controller
        views = (base / 'views' / 'ai_log_door_views.xml').read_text(encoding='utf-8')
        assert 'ref="pns_ai_mcp.view_ai_log_search"' in views
        assert "domain=\"[('origin', '=', 'chatboo')]\"" in views
        manifest = (base / '__manifest__.py').read_text(encoding='utf-8')
        assert "'views/ai_log_door_views.xml'" in manifest
