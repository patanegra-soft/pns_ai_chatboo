# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The engine hears which files came with the turn, so «this pdf» is not a download."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB = ROOT / 'common' / 'models' / 'chatboo_async_request.py'


def _turn_file_names():
    tree = ast.parse(JOB.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_turn_file_names':
            mod = ast.Module(body=[node], type_ignores=[])
            scope = {'json': json}
            exec(compile(mod, str(JOB), 'exec'), scope)
            return scope['_turn_file_names']
    raise AssertionError('_turn_file_names not found')


class _Job:
    def __init__(self, files):
        self.files = files


def test_engine_context_carries_the_names():
    assert 'turn_file_names=self._turn_file_names(),' in JOB.read_text(encoding='utf-8')


def test_names_come_from_the_turn_files():
    fn = _turn_file_names()
    files = json.dumps([
        {'name': 'acme_99999.pdf', 'data': 'data:application/pdf;base64,AA=='},
        {'name': '', 'data': ''},
        'not a file',
    ])
    assert fn(_Job(files)) == ('acme_99999.pdf',)


def test_no_files_or_bad_json_is_empty():
    fn = _turn_file_names()
    assert fn(_Job(False)) == ()
    assert fn(_Job('{broken')) == ()
