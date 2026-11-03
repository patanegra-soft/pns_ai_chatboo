# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Register the engine's ``engine_params`` under its Odoo import name.

``chatboo_product_icp`` imports it from ``odoo.addons.pns_ai_mcp``. Host
tests have no Odoo, so the real file from the sibling repo is loaded.
A published clone has no sibling: those tests are skipped there.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[2] / 'pns_ai_mcp'
NAME = 'odoo.addons.pns_ai_mcp.utils.engine_params'
PATH = ENGINE / 'common' / 'utils' / 'engine_params.py'


def engine_file(*parts):
    path = ENGINE.joinpath(*parts)
    if not path.is_file():
        pytest.skip('needs the pns_ai_mcp repository next to this one')
    return path


def install():
    if NAME in sys.modules:
        return sys.modules[NAME]
    engine_file('common', 'utils', 'engine_params.py')
    spec = importlib.util.spec_from_file_location(NAME, PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[NAME] = mod
    return mod
