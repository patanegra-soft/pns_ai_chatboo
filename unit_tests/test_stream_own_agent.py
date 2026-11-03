# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""A Chatboo turn always runs on Chatboo's agent; the browser cannot name another."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_stream_and_slash_list_ignore_client_agent_code():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers'
            / 'chatboo.py'
        ).read_text(encoding='utf-8')
        assert "data.get('agent_code')" not in src
        assert "kwargs.get('agent_code')" not in src
        assert 'agent_code=resolved_code, provider_id=provider_id' in src
