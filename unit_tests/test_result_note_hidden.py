# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The note the chat writes for the AI after Confirm/Cancel is not the user's bubble."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(*parts):
    return ROOT.joinpath(*parts).read_text(encoding='utf-8')


def test_payload_carries_the_flag():
    turn = _read('common', 'static', 'src', 'js', 'chatboo_turn.js')
    assert 'turn.resultNote' in turn
    assert 'payload.result_note = true' in turn


def test_each_stream_route_hands_it_to_the_job():
    for stack in ('owl1', 'owl2', 'owl3'):
        ctrl = _read('stacks', stack, 'pns_ai_chatboo', 'controllers', 'chatboo.py')
        assert "result_note=bool(data.get('result_note'))" in ctrl, stack


def test_the_job_stores_the_user_line_marked():
    job = _read('common', 'models', 'chatboo_async_request.py')
    assert 'result_note = fields.Boolean(' in job
    assert "'result_note': bool(result_note)" in job
    assert "_user_msg['result_note'] = True" in job


def test_owl2_owl3_send_keep_and_skip_it():
    for stack in ('owl2', 'owl3'):
        js = _read('stacks', stack, 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_app.js')
        xml = _read('stacks', stack, 'pns_ai_chatboo', 'static', 'src', 'xml', 'chatboo_app.xml')
        finish = js[js.index('_finishVerificationOutcome(evt, res, action) {'):]
        finish = finish[:finish.index('\n    }\n')]
        assert finish.count('{ resultNote: true }') == 2, stack
        assert 'resultNote: !!opts.resultNote' in js, stack
        assert 'result_note: !!m.result_note' in js, stack
        assert 'out.result_note = true' in js, stack
        assert '<div t-if="!msg.result_note"' in xml, stack


def test_owl1_sends_keeps_and_skips_it():
    js = _read(
        'stacks', 'owl1', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_component_v2.js',
    )
    run = js[js.index('async _runResultTurn(noteText) {'):]
    run = run[:run.index('finally')]
    assert 'null, null, null, true' in run
    assert 'resultNote: !!resultNote' in js
    assert 'out.result_note = true' in js
    assert '<div t-if="!msg.result_note"' in js
