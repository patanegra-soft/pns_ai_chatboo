# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Stored chat HTML moves to the engine's ``data-ai-*`` names on ``-u``."""
from pathlib import Path

_MODELS = Path(__file__).resolve().parents[1] / 'common' / 'models'


def _init_of(name):
    src = (_MODELS / name).read_text(encoding='utf-8')
    return src.split('    def init(self):', 1)[1].split('\n    def ', 1)[0]


def test_session_renames_messages_and_canvas():
    body = _init_of('chatboo_session.py')
    assert "rename_stored_markup(self.env.cr, self._table, 'messages')" in body
    assert "rename_stored_markup(self.env.cr, self._table, 'canvas_design')" in body


def test_shared_page_renames_its_design():
    body = _init_of('chatboo_canvas_page.py')
    assert "rename_stored_markup(self.env.cr, self._table, 'design')" in body
