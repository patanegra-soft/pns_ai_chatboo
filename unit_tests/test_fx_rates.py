# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""USD FX helper delegates to ai.fx.source."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load():
    path = Path(__file__).resolve().parents[1] / 'common' / 'utils' / 'fx_rates.py'
    spec = importlib.util.spec_from_file_location('chatboo_fx_rates', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_get_usd_fx_delegates_to_engine():
    fx = _load()
    payload = {'base': 'USD', 'rates': {'EUR': 0.92}, 'as_of': '2026-08-15'}
    env = {
        'ai.fx.source': SimpleNamespace(get_usd_fx=lambda: payload),
    }
    assert fx.get_usd_fx(env) == payload


def test_get_usd_fx_reports_the_error_if_model_missing():
    fx = _load()

    class _Missing(dict):
        def __getitem__(self, key):
            raise KeyError(key)

    payload = fx.get_usd_fx(_Missing())
    assert payload['base'] == 'USD'
    assert payload['rates'] == {}
    assert 'ai.fx.source' in payload['error']
