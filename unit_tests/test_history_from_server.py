# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The turn history is rebuilt from the saved session (PNS-61).

/chatboo/stream ignores any history the browser sends. What the model
sees is what the server saved, minus system lines and off-topic turns.
"""
import ast
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
_CTRLS = [
    (_ROOT / 'stacks' / s / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py').read_text(
        encoding='utf-8')
    for s in ('owl1', 'owl2')
]


def _load_method():
    tree = ast.parse(_SESSION)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'get_model_history':
            module = ast.Module(body=[node], type_ignores=[])
            ns = {}
            exec(compile(module, 'chatboo_session.py', 'exec'), ns)
            return ns['get_model_history']
    raise AssertionError('get_model_history missing')


class _FakeSession:
    def __init__(self, messages):
        self._messages = messages

    def get_messages(self):
        return list(self._messages)


def test_model_history_filters_like_the_client_did():
    fn = _load_method()
    fake = _FakeSession([
        {'role': 'system', 'content': 'secret instructions'},
        {'role': 'user', 'content': 'hola'},
        {'role': 'assistant', 'content': 'qué tal'},
        {'role': 'user', 'content': 'off', 'offtopic': True},
        {'role': 'assistant', 'content': 'ack', 'meta': {'local_ack': True}},
        {'role': 'assistant', 'content': 'verify', 'meta': {'verification_ack': True}},
        'garbage',
    ])
    out = fn(fake)
    assert [m['content'] for m in out] == ['hola', 'qué tal', 'verify']


def test_stream_controllers_ignore_body_history():
    for src in _CTRLS:
        assert "data.get('history'" not in src
        assert 'history = session.get_model_history()' in src
