# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""PNS-54: Chatboo sends the card token with confirm and execute."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _read(*parts):
    return _ROOT.joinpath(*parts).read_text(encoding='utf-8')


def test_both_stacks_send_the_card_token():
    owl1 = _read(
        'stacks', 'owl1', 'pns_ai_chatboo', 'static', 'src', 'js',
        'chatboo_component_v2.js',
    )
    owl2 = _read(
        'stacks', 'owl2', 'pns_ai_chatboo', 'static', 'src', 'js',
        'chatboo_app.js',
    )
    for src in (owl1, owl2):
        assert 'dataset.confirmToken' in src
        assert 'existing.dataset.confirmToken' in src
        assert src.count("verification/confirm") >= 1
        confirm = src.split("_callJsonRoute") 
        calls = [c[:600] for c in confirm if 'verification/confirm' in c[:200] or 'verification/execute' in c[:200]]
        joined = '\n'.join(calls)
        assert 'confirm_token' in joined
        assert 'verification/execute' in src
        execute = src.split('verification/execute')[1][:500]
        assert 'confirm_token' in execute
