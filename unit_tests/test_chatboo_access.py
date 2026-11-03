# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Chatboo door: carnet AND conversational group."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_ACCESS = (
    _ROOT / 'common' / 'utils' / 'chatboo_access.py'
).read_text(encoding='utf-8')
_SEED = (
    _ROOT / 'common' / 'data' / 'ai_agent_data.xml'
).read_text(encoding='utf-8')
_STAMP = (
    _ROOT / 'common' / 'data' / 'ai_agent_conversational.xml'
).read_text(encoding='utf-8')


def test_access_needs_carnet_and_conversational():
    assert 'user_is_ai_conversational' in _ACCESS
    assert 'user_has_mcp_api_key' in _ACCESS
    assert 'pns_ai_mcp.utils.conversational' in _ACCESS


def test_chatboo_agent_is_conversational():
    assert 'is_agent_conversational' in _SEED
    assert 'eval="True"' in _SEED
    assert 'noupdate="1"' not in _STAMP
    assert 'ai_agent_chatboo' in _STAMP
    assert 'eval="True"' in _STAMP


def test_manifests_load_the_stamp():
    for stack in ('owl1', 'owl2'):
        text = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / '__manifest__.py'
        ).read_text(encoding='utf-8')
        assert 'ai_agent_conversational.xml' in text


def test_factory_seed_declares_chatboo_conversational():
    src = (
        _ROOT / 'common' / 'models' / 'ai_agent.py'
    ).read_text(encoding='utf-8')
    blob = src.split('def _module_factory_seed')[1].split(
        'return super()',
    )[0]
    assert "'is_agent_conversational': True" in blob
