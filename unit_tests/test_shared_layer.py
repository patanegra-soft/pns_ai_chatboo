# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Chatboo shares the full-screen layer through pns_base, and names no other panel."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_JS = _ROOT / 'stacks'


def _read(*parts):
    return _JS.joinpath(*parts).read_text(encoding='utf-8')


def test_both_stacks_claim_and_release_the_layer():
    owl1 = _read('owl1', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_systray.js')
    owl2 = _read('owl2', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_overlay.js')
    for text in (owl1, owl2):
        assert "pnsLayer.claim(" in text and "pnsLayer.release(" in text
        # The navbar click that closes the panel lives in pns_base now.
        assert 'navbar.addEventListener' not in text
    for stack in ('owl1', 'owl2'):
        xml = _read(stack, 'pns_ai_chatboo', 'static', 'src', 'xml', 'chatboo_systray.xml')
        assert 'data-pns-layer-toggle="1"' in xml
        manifest = _read(stack, 'pns_ai_chatboo', '__manifest__.py')
        assert "'pns_base'" in manifest
