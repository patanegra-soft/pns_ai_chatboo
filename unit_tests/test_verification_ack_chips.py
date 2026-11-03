# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Verification ack carries records + history; offtopic skip excludes that ack."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_OWL1_JS = (
    _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
    / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
)
_OWL2_JS = (
    _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
    / 'static' / 'src' / 'js' / 'chatboo_app.js'
)
_OWL1_XML = _OWL1_JS  # records live in the same OWL1 component template
_OWL2_XML = (
    _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
    / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
)


def test_append_verification_ack_takes_records_and_history():
    for label, src in (('owl1', _OWL1_JS.read_text(encoding='utf-8')),
                       ('owl2', _OWL2_JS.read_text(encoding='utf-8'))):
        fn = src.split('_appendVerificationAck', 1)[1]
        assert 'records' in fn.split('_finishVerificationOutcome', 1)[0], label
        assert 'backend_history' in fn or 'history' in fn, label
        assert 'verification_ack' in fn.split('_finishVerificationOutcome', 1)[0], label
        off = src.split('_isOfftopicMessage(m) {', 1)[1]
        assert 'ChatbooTurn.isOfftopic(m)' in off.split('}', 1)[0], label
        finish = src.split('_finishVerificationOutcome', 1)[1]
        assert 'res.records' in finish, label


def test_offtopic_skip_keeps_the_verification_ack():
    core = (_ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_turn.js').read_text(encoding='utf-8')
    off = core.split('function isOfftopic(m) {', 1)[1].split('\n    }\n', 1)[0]
    assert 'verification_ack' in off
    assert off.index('verification_ack') < off.index('local_ack')


def test_templates_paint_document_card_not_related_chips():
    owl1 = _OWL1_XML.read_text(encoding='utf-8')
    owl2 = _OWL2_XML.read_text(encoding='utf-8')
    for label, src in (('owl1', owl1), ('owl2', owl2)):
        assert 'o_chatboo_ack_doc_card' in src, label
        assert "role" in src and 'document' in src, label
        assert 'o_chatboo_ack_chip' not in src, label
        assert 'o_chatboo_ack_related' not in src, label
