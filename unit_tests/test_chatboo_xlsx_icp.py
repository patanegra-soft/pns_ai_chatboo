# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Excel ICP defaults and clamp for Chatboo XLSX export."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from _engine_params import install as install_engine_params


def _load():
    install_engine_params()
    path = (
        Path(__file__).resolve().parents[1]
        / 'common' / 'utils' / 'chatboo_product_icp.py'
    )
    spec = importlib.util.spec_from_file_location('chatboo_product_icp', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_xlsx_icp_defaults_and_clamp():
    icp = _load()
    engine = install_engine_params()
    assert engine.DEFAULT_XLSX_FLOAT_DECIMALS == 2
    assert engine.DEFAULT_XLSX_THOUSANDS is True
    assert icp.ICP_XLSX_FLOAT_DECIMALS == 'pns_ai.xlsx_float_decimals'
    assert icp.ICP_XLSX_THOUSANDS == 'pns_ai.xlsx_thousands'
    assert icp.normalize_xlsx_float_decimals(None) == 2
    assert icp.normalize_xlsx_float_decimals('4') == 4
    assert icp.normalize_xlsx_float_decimals(99) == 10
    assert icp.normalize_xlsx_float_decimals(-3) == 0


def test_read_product_settings_xlsx_defaults():
    icp = _load()

    class Env:
        def __getitem__(self, name):
            return self

        def sudo(self):
            return self

        def get_param(self, key, default=None):
            return default

    settings = icp.read_product_settings(Env())
    assert settings['xlsx_float_decimals'] == 2
    assert settings['xlsx_thousands'] is True
    # Unset retention keeps everything.
    assert settings['history_retention_days'] == 0
    assert settings['download_max_mb'] == 15
    assert settings['dataset_cache_max_bytes'] == icp.DEFAULT_DATASET_CACHE_BYTES
    assert settings['dataset_cache_max_mb'] == 8
    assert settings['allow_remote_voices'] is False


def test_saving_the_currency_decimals_keeps_following_the_currency():
    icp = _load()

    class Env:
        company = type('C', (), {
            'currency_id': type('Cur', (), {'decimal_places': 3})(),
        })()

        def __init__(self):
            self.written = {}

        def __getitem__(self, name):
            return self

        def sudo(self):
            return self

        def set_param(self, key, value):
            self.written[key] = value

    env = Env()
    icp.write_product_settings(env, xlsx_float_decimals=3)
    assert env.written[icp.ICP_XLSX_FLOAT_DECIMALS] is False
    icp.write_product_settings(env, xlsx_float_decimals=4)
    assert env.written[icp.ICP_XLSX_FLOAT_DECIMALS] == '4'


def test_read_product_settings_dataset_cache_unlimited():
    icp = _load()

    class Env:
        def __getitem__(self, name):
            return self

        def sudo(self):
            return self

        def get_param(self, key, default=None):
            if key == icp.ICP_DATASET_CACHE_MAX_BYTES:
                return '0'
            return default

    settings = icp.read_product_settings(Env())
    assert settings['dataset_cache_max_bytes'] == 0
    assert settings['dataset_cache_max_mb'] == 0
    assert icp.ICP_HISTORY_RETENTION_DAYS == 'pns_ai_chatboo.history_retention_days'
    assert icp.ICP_DOWNLOAD_MAX_BYTES == 'pns_ai.download_max_bytes'
