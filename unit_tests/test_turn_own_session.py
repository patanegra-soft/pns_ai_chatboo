# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""A user cannot start a turn by RPC, nor aim one at someone else's session."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_MODEL = _ROOT / 'common' / 'models' / 'chatboo_async_request.py'
_JOB = _ROOT / 'common' / 'models' / 'chatboo_job.py'


def _class(path, name):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    return next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name
    )


def _methods(path=_MODEL, name='ChatbooAsyncRequest'):
    cls = _class(path, name)
    return {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}


def _job_methods():
    return _methods(_JOB, 'ChatbooJobMixin')


def test_a_turn_is_a_chatboo_job():
    src = ast.unparse(_class(_MODEL, 'ChatbooAsyncRequest'))
    assert "_inherit = 'chatboo.job.mixin'" in src


def test_queue_and_thread_are_not_rpc_methods():
    methods = _methods()
    job = _job_methods()
    assert 'enqueue' not in methods
    assert 'spawn' not in methods and 'spawn' not in job
    assert '_enqueue' in methods
    assert '_spawn' in job


def test_create_pins_the_user_and_checks_the_session():
    src = ast.unparse(_job_methods()['create'])
    assert "vals['user_id'] = self.env.uid" in src
    assert "('user_id', '=', self.env.uid)" in src
    assert 'AccessError' in src


def test_session_and_user_cannot_be_rewritten():
    src = ast.unparse(_job_methods()['write'])
    assert '_OWNER_FIELDS' in src
    assert 'AccessError' in src


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_the_stream_uses_the_private_queue(stack):
    src = (
        _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
    ).read_text(encoding='utf-8')
    assert "['chatboo.async.request']._enqueue(" in src
    assert 'job._spawn()' in src
