# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""A turn never leaves the session row locked for the cursor that finishes it.

The turn runs on its own cursor in a thread. ``_finalize`` writes the session
on a second cursor in the same thread. If the first one still holds the row,
the second waits forever: the job never ends and each reload holds a worker.
"""
import ast
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_JOB = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
_CTRLS = [
    (_ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py').read_text(encoding='utf-8')
    for stack in ('owl1', 'owl2')
]


def _method(src, name):
    return src.split('    def %s(' % name, 1)[1].split('\n    def ', 1)[0]


def test_the_turn_cursor_is_released_before_every_finalize():
    process = _method(_JOB, '_process')
    calls = process.count('self._finalize(')
    assert calls == 3
    assert process.count('self._release_turn_cursor()\n') == calls
    for before in process.split('self._finalize(')[:-1]:
        assert before.rstrip().endswith('self._release_turn_cursor()')


def test_releasing_is_a_rollback_and_not_in_tests():
    release = _method(_JOB, '_release_turn_cursor')
    assert 'if _is_test_mode(self.env):\n            return' in release
    assert 'self.env.cr.rollback()' in release
    assert 'commit' not in release.split('"""')[2]


def test_the_screen_is_kept_on_a_short_cursor():
    process = _method(_JOB, '_process')
    assert "'last_screen_context'" not in process
    assert 'self._store_last_screen(raw_sc)' in process
    store = _method(_JOB, '_store_last_screen')
    assert '_get_registry(self.env.cr.dbname).cursor() as cr' in store
    assert "SET LOCAL lock_timeout" in store
    assert 'UPDATE chatboo_session SET last_screen_context' in store


def test_a_failed_commit_before_the_model_ends_the_turn():
    process = _method(_JOB, '_process')
    branch = process.split("could not commit the session writes'")[1].split('self._start_heartbeat')[0]
    assert 'self._release_turn_cursor()' in branch
    assert 'self._finalize(' in branch
    assert re.search(r'\)\)\n\s+return\n', branch)


def test_finalize_bounds_the_wait_and_keeps_the_job_state():
    finalize = _method(_JOB, '_finalize')
    fresh = finalize.split('with _get_registry(dbname).cursor() as cr:', 1)[1]
    assert fresh.lstrip().startswith('cr.execute("SET LOCAL lock_timeout')
    assert 'with cr.savepoint():\n                            _chips = job._save_to_session(' in fresh
    assert "job.sudo().write({'state': 'error', 'error': error})" in fresh
    raw = finalize.split('_finalize fresh-cursor failed', 1)[1]
    assert 'SET LOCAL lock_timeout' in raw
    assert 'UPDATE chatboo_async_request' in raw
    assert "vals['state'] = 'error'" in finalize


def _waited_for_lock():
    tree = ast.parse(_JOB)
    scope = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, 'id', '') == '_LOCK_NOT_AVAILABLE' for t in node.targets):
            exec(compile(ast.Module([node], []), 'job', 'exec'), scope)
        if isinstance(node, ast.FunctionDef) and node.name == '_waited_for_lock':
            exec(compile(ast.Module([node], []), 'job', 'exec'), scope)
    return scope['_waited_for_lock']


def test_a_lock_timeout_is_told_apart_from_other_errors():
    waited = _waited_for_lock()

    class _PgError(Exception):
        def __init__(self, code):
            super().__init__(code)
            self.pgcode = code

    assert waited(_PgError('55P03'))
    assert not waited(_PgError('40001'))
    assert not waited(ValueError('x'))
    try:
        try:
            raise _PgError('55P03')
        except _PgError as inner:
            raise RuntimeError('wrapped') from inner
    except RuntimeError as outer:
        assert waited(outer)


def test_a_reload_does_not_wait_for_a_busy_row():
    stamp = _method(_SESSION, 'update_last_used')
    assert 'FOR UPDATE SKIP LOCKED' in stamp
    assert stamp.index('SKIP LOCKED') < stamp.index('self.last_used_date =')


def test_saving_the_session_from_the_browser_has_a_lock_limit():
    for src in _CTRLS:
        save = src.split('def save_session(', 1)[1].split('\n    @http.route', 1)[0]
        assert "request.env.cr.execute(\"SET LOCAL lock_timeout = '10s'\")" in save
        assert save.index('SET LOCAL lock_timeout') < save.index('session.set_messages(')
