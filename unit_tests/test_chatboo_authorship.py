# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Host identity: Chatboo registers its own facts, not other brands."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load():
    path = (
        Path(__file__).resolve().parents[1]
        / 'common' / 'utils' / 'chatboo_authorship.py'
    )
    spec = importlib.util.spec_from_file_location('chatboo_authorship', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_chatboo_registry_is_only_chatboo():
    auth = _load()
    reg = auth.chatboo_host_identity_registry()
    assert list(reg) == ['pns_ai_chatboo']
    assert reg['pns_ai_chatboo']['product_name'] == 'Chatboo'
    assert reg['pns_ai_chatboo']['vendor'] == 'PATANEGRA Soft'
