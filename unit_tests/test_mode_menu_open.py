# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Picking /mode opens the mode list immediately, same as /skills."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _apply_block(src: str) -> str:
    marker = '_applySlashSelection(item) {'
    return src.split(marker, 1)[1].split('_isHelpArg', 1)[0]


def test_owl2_pick_mode_opens_menu():
    js = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    apply = _apply_block(js)
    assert 'item.code === "skills"' in apply
    assert 'this._openSkillsMenu()' in apply
    assert 'item.code === "mode"' in apply
    assert 'this._openModeMenu()' in apply


def test_owl1_pick_mode_opens_menu():
    js = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    apply = _apply_block(js)
    assert "item.code === 'skills'" in apply
    assert 'this._openSkillsMenu()' in apply
    assert "item.code === 'mode'" in apply
    assert 'this._openModeMenu()' in apply
