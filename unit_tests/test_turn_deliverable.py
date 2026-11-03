# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""A session file or clip rows still count as a turn when the bubble is empty."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = _ROOT / 'common' / 'utils' / 'turn_deliverable.py'
    spec = importlib.util.spec_from_file_location('turn_deliverable', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_empty_done_is_not_deliverable():
    fn = _load().done_meta_has_deliverable
    assert fn(None) is False
    assert fn({}) is False
    assert fn({'assistant_files': []}) is False
    assert fn({'clip_data': {'rows': []}}) is False
    assert fn({'clip_data': 'nope'}) is False


def test_session_chip_or_clip_rows_are_deliverable():
    fn = _load().done_meta_has_deliverable
    assert fn({
        'assistant_files': [{'name': 'mejores_clientes_cordoba.pdf', 'url': '/web/content/1'}],
    }) is True
    assert fn({
        'clip_data': {'rows': [{'Name': 'Acme'}], 'title': 'Top customers'},
    }) is True
    assert fn({
        'assistant_files': [{'name': 'x.pdf'}],
        'clip_data': {'rows': [{'Name': 'Acme'}]},
    }) is True


def test_finalize_skips_empty_content_error_when_deliverable():
    src = (
        _ROOT / 'common' / 'models' / 'chatboo_async_request.py'
    ).read_text(encoding='utf-8')
    assert 'from ..utils.turn_deliverable import done_meta_has_deliverable' in src
    assert "source_channel='chatboo'" in src
    assert 'CHATBOO_AGENT_CODE' in src
    assert 'done_meta_has_deliverable(done_meta)' in src
    assert 'The model returned no content' in src
    guard = src.split('def _finalize', 1)[1]
    assert guard.find('done_meta_has_deliverable') < guard.find(
        'The model returned no content'
    )
