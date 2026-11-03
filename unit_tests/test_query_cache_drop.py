# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""A finished turn with no rows must drop the previous dataset cache."""
from __future__ import annotations

from pathlib import Path

_SRC = (
    Path(__file__).resolve().parents[1]
    / 'common' / 'models' / 'chatboo_async_request.py'
).read_text(encoding='utf-8')


def test_success_without_rows_drops_the_dataset_cache():
    assert 'drop_query_cache=(last_query_data is None)' in _SRC
    save = _SRC.split('def _save_to_session')[1].split('def ')[0]
    assert 'drop_query_cache' in save
    assert "'last_query_data': False" in save
    assert "'last_query_code': False" in save
    assert 'not reclaim' in save
