# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""History shows the first prompt as the session name until it is renamed by hand."""
import ast
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
_CTRLS = [
    (_ROOT / 'stacks' / s / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py').read_text(
        encoding='utf-8')
    for s in ('owl1', 'owl2', 'owl3')
]


def _functions():
    tree = ast.parse(_SESSION)
    wanted = {'first_prompt', 'title_of', 'title_from_messages'}
    nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            node.decorator_list = []
            nodes.append(node)
    assert {n.name for n in nodes} == wanted
    ns = {'re': re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'chatboo_session.py', 'exec'), ns)

    class _Cls:
        TITLE_LENGTH = 48
        first_prompt = staticmethod(ns['first_prompt'])

    _Cls.title_of = classmethod(ns['title_of'])
    return ns, _Cls


def _title():
    ns, cls = _functions()
    return lambda messages: ns['title_from_messages'](cls, messages)


def test_first_prompt_is_whole_plain_text():
    ns, _cls = _functions()
    prompt = 'facturas pendientes de ACME Ejemplo del último trimestre por comercial'
    assert ns['first_prompt']([{'role': 'user', 'content': '<p>%s</p>' % prompt}]) == prompt


def test_first_user_prompt_cut_at_48_with_ellipsis():
    title = _title()
    prompt = 'facturas pendientes de ACME Ejemplo del último trimestre por comercial'
    out = title([
        {'role': 'system', 'content': 'hello'},
        {'role': 'user', 'content': '<p>%s</p>' % prompt},
        {'role': 'user', 'content': 'second'},
    ])
    assert out.endswith('…')
    assert len(out) <= 49
    assert out.startswith('Facturas pendientes')


def test_short_prompt_stays_whole_and_no_prompt_is_empty():
    title = _title()
    assert title([{'role': 'user', 'content': 'hola'}]) == 'Hola'
    assert title([{'role': 'assistant', 'content': 'x'}]) == ''


def test_controllers_keep_a_hand_typed_name():
    for src in _CTRLS:
        assert "if not session.name_custom:" in src
        assert "'name_custom': True" in src
        assert "startswith('Session ')" not in src
        assert "history_rows()" in src
        assert 'get_messages' not in src.split('def list_sessions', 1)[1].split('@http.route', 1)[0]


def test_history_lists_every_session_from_short_columns():
    assert 'def get_user_sessions(self):' in _SESSION
    assert 'limit=' not in _SESSION.split('def get_user_sessions', 1)[1].split('\n\n', 1)[0]
    rows = _SESSION.split('def history_rows', 1)[1].split('\n    def ', 1)[0]
    assert 'sessions.read(list(self._HISTORY_FIELDS))' in rows
    assert 'get_messages' not in rows
    assert "'messages'" not in _SESSION.split('_HISTORY_FIELDS = (', 1)[1].split(')', 1)[0]
