# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Both clients send a turn through one core: chatboo_turn.js."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_JS_DIR = _ROOT / 'common' / 'static' / 'src' / 'js'
_TURN = _JS_DIR / 'chatboo_turn.js'
_SSE = _JS_DIR / 'chatboo_sse.js'
_CLIENT = {'owl1': 'chatboo_component_v2.js', 'owl2': 'chatboo_app.js'}

_SCRIPT = r'''
const fs = require('fs');
const vm = require('vm');
const sandbox = { console, TextDecoder, TextEncoder };
sandbox.globalThis = sandbox;
vm.runInNewContext(fs.readFileSync(process.env.SSE_JS, 'utf8'), sandbox);
vm.runInNewContext(fs.readFileSync(process.env.TURN_JS, 'utf8'), sandbox);
const T = sandbox.ChatbooTurn;
const enc = new TextEncoder();

function streamOf(chunks) {
    let i = 0;
    return { body: { getReader() { return { read: async () => (
        i < chunks.length ? { done: false, value: enc.encode(chunks[i++]) } : { done: true }
    ) }; } } };
}

(async () => {
    const out = {};
    out.url = T.streamUrl('a b/+');
    out.urlEmpty = T.streamUrl(undefined);

    let spent = [{ model: 'res.partner', id: 7 }];
    sandbox.ChatbooRowMarks = { take() { const r = spent; spent = []; return r; } };
    out.payload = T.buildPayload({
        sessionId: 3, message: 'hola', history: [], providerId: false,
        screenContext: { model: 'crm.lead' }, images: [], imageNames: ['a.png'],
        files: [{ name: 'f' }],
    });
    out.payloadAgain = T.buildPayload({ sessionId: undefined, message: 'x', history: [] });
    delete sandbox.ChatbooRowMarks;
    out.payloadNoMarks = T.buildPayload({ sessionId: null, message: 'x', history: [] });

    const json = (status, body) => ({ status, json: async () => body });
    const html = (status) => ({ status, json: async () => { throw new Error('html'); } });
    out.refusedOwn = await T.refusal(json(403, { error: 'No access' }), 'RELOAD');
    out.refusedCsrf = await T.refusal(html(400), 'RELOAD');
    out.refusedOther = await T.refusal(html(502), 'RELOAD');

    const events = [];
    let data = 0;
    await T.readEvents(
        streamOf(['event: token\ndata: {"content":"Ho', 'la"}\n\n\n\nevent: done\n',
                  'data: {"compose":"compose-model"}\n\n', 'event: status\n']),
        (e) => events.push(e), () => { data += 1; });
    out.events = events;
    out.dataCalls = data;

    const msgs = [
        { role: 'system', content: 's' },
        { role: 'user', content: 'u1' },
        { role: 'assistant', content: 'off', offtopic: true },
        { role: 'assistant', content: 'ack', meta: { local_ack: true } },
        { role: 'assistant', content: 'ok', local_ack: true, verification_ack: true },
        { role: 'user', content: 'tail' },
    ];
    out.turns = T.modelTurns(msgs).map((m) => m.content);
    out.turnsTail = T.modelTurns(msgs, 1).map((m) => m.content);
    out.turnsNone = T.modelTurns(null);

    out.clipShort = T.clipForLlm('abc', 10);
    out.clipLong = T.clipForLlm('abcd  efgh', 7);
    out.clipNull = T.clipForLlm(null, 0);

    out.plainKept = T.contentForLlm('<b>x</b>');
    out.plainStripped = T.contentForLlm(' <b>x</b> ', (h) => h.replace(/<[^>]*>/g, ''));
    out.fat = T.contentForLlm('<table><tr><td>1</td></tr></table>', () => 'never');
    out.stub = T.contentForLlm('[On-screen artifact | kind=table | ~9 characters]');
    process.stdout.write(JSON.stringify(out));
})().catch((e) => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
'''


@pytest.fixture(scope='module')
def run():
    proc = subprocess.run(
        ['node', '-e', _SCRIPT],
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=False,
        env={**os.environ, 'SSE_JS': str(_SSE), 'TURN_JS': str(_TURN)},
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_the_url_carries_the_csrf_token(run):
    assert run['url'] == '/chatboo/stream?csrf_token=a%20b%2F%2B'
    assert run['urlEmpty'] == '/chatboo/stream?csrf_token='


def test_the_payload_spends_the_marks_and_drops_empty_lists(run):
    assert run['payload'] == {
        'session_id': 3,
        'message': 'hola',
        'history': [],
        'provider_id': None,
        'screen_context': {'model': 'crm.lead'},
        'refs': [{'model': 'res.partner', 'id': 7}],
        'image_names': ['a.png'],
        'files': [{'name': 'f'}],
    }
    assert run['payloadAgain'] == {'message': 'x', 'history': [], 'provider_id': None}
    assert run['payloadNoMarks'] == {
        'session_id': None, 'message': 'x', 'history': [], 'provider_id': None,
    }


def test_a_refusal_is_said_in_words(run):
    assert run['refusedOwn'] == 'No access'
    assert run['refusedCsrf'] == 'RELOAD'
    assert run['refusedOther'] == 'HTTP 502'


def test_frames_split_across_chunks_arrive_whole_and_in_order(run):
    assert run['events'] == [
        {'content': 'Hola', 'event': 'token'},
        {'compose': 'compose-model', 'event': 'done'},
    ]
    assert run['dataCalls'] == 4


def test_the_model_does_not_see_system_or_offtopic_lines(run):
    assert run['turns'] == ['u1', 'ok', 'tail']
    assert run['turnsTail'] == ['u1', 'ok']
    assert run['turnsNone'] == []


def test_clip_and_content_for_the_model(run):
    assert run['clipShort'] == 'abc'
    assert run['clipLong'] == 'abcd…'
    assert run['clipNull'] == ''
    assert run['plainKept'] == '<b>x</b>'
    assert run['plainStripped'] == 'x'
    assert run['fat'].startswith('[On-screen artifact | kind=table | ~')
    assert 'Do not reprint the rows.' in run['fat']
    assert run['stub'] == '[On-screen artifact | kind=table | ~9 characters]'


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_each_client_uses_the_core_and_keeps_its_own_header(stack):
    src = (
        _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js' / _CLIENT[stack]
    ).read_text(encoding='utf-8')
    for call in ('ChatbooTurn.buildPayload(', 'ChatbooTurn.streamUrl(odoo.csrf_token)',
                 'ChatbooTurn.readEvents(resp,', 'ChatbooTurn.refusal(resp,',
                 'ChatbooTurn.modelTurns(', 'ChatbooTurn.contentForLlm('):
        assert call in src, call
    assert 'getReader()' not in src
    assert 'marks.take()' not in src
    if stack == 'owl1':
        assert "'Content-Type': 'text/plain;charset=UTF-8'" in src
        assert "credentials: 'same-origin'" in src
        assert 'formatters.textOfHtml(html)' in src
    else:
        assert '"Content-Type": "application/json"' in src
        assert 'const ChatbooTurn = globalThis.ChatbooTurn;' in src


def test_both_stacks_load_the_core_right_after_sse():
    owl2 = (_ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / '__manifest__.py').read_text(encoding='utf-8')
    assert ("'pns_ai_chatboo/static/src/js/chatboo_sse.js',\n"
            "            'pns_ai_chatboo/static/src/js/chatboo_turn.js',") in owl2.replace('\r\n', '\n')
    owl1 = (_ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'views' / 'assets.xml').read_text(encoding='utf-8')
    sse = owl1.index('static/src/js/chatboo_sse.js')
    turn = owl1.index('static/src/js/chatboo_turn.js')
    app = owl1.index('static/src/js/chatboo_component_v2.js')
    assert sse < turn < app
