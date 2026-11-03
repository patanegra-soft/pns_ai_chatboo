# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Clicking a row answers "which one?" without spelling the name again."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SESS = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(
    encoding='utf-8',
)
_JOB = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(
    encoding='utf-8',
)
_MARKS_JS = (
    _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_row_marks.js'
).read_text(encoding='utf-8')
_CSS = (
    _ROOT / 'common' / 'static' / 'src' / 'css' / 'chatboo_row_marks.css'
).read_text(encoding='utf-8')
_SELF = (
    _ROOT / 'common' / 'ai' / 'contexts' / 'domain' / 'self_chatboo'
    / 'self_chatboo.xml'
).read_text(encoding='utf-8')


def _stack(name, *parts):
    return (_ROOT / 'stacks' / name / 'pns_ai_chatboo').joinpath(
        *parts,
    ).read_text(encoding='utf-8')


def test_the_session_keeps_what_the_user_pointed_at():
    assert 'marked_refs = fields.Text(' in _SESS
    assert 'def remember_marks' in _SESS
    assert 'def forget_marks' in _SESS
    # What a mark is lives in the engine, shared with the other clients.
    assert 'from odoo.addons.pns_ai_mcp.utils import record_marks' in _SESS
    assert 'record_marks.clean_marks(refs)' in _SESS
    assert 'record_marks.marks_sentence(self.get_marks())' in _SESS
    assert 'record_marks.narrow_rows(self.get_marks(), rows)' in _SESS


def test_the_turn_says_the_pick_out_loud_and_narrows_the_dataset():
    """A silently shrunken dataset left the model free to search the name."""
    assert 'marked = self.session_id.marks_sentence()' in _JOB
    assert "message_for_engine = '%s\\n\\n%s' % (message_for_engine, marked)" in _JOB
    assert 'self.session_id.narrow_query_data(' in _JOB
    # Spent by the sentence that carried it.
    assert 'self.session_id.forget_marks()' in _JOB
    assert _JOB.index('marks_sentence()') < _JOB.index('forget_marks()')


def test_the_marks_reach_the_server_with_the_message():
    for stack in ('owl1', 'owl2'):
        ctrl = _stack(stack, 'controllers', 'chatboo.py')
        assert "session.remember_marks(data.get('refs'))" in ctrl


def test_a_row_is_marked_by_the_record_its_link_names():
    """No new server field: the deep link already says model and id."""
    assert "a.o_ai_namelink[href*='/web#']" in _MARKS_JS
    rec = _MARKS_JS.split('function rowRecord')[1].split('\n    function ')[0]
    assert 'URLSearchParams(hash)' in rec
    assert 'params.get("id")' in rec
    assert 'params.get("model")' in rec
    # The link still opens the record; only the rest of the row picks it.
    click = _MARKS_JS.split('function onClick')[1].split('\n    function ')[0]
    assert 'target.closest(NO_MARK)' in click
    assert 'NO_MARK = "a, button, input, select, textarea, label"' in _MARKS_JS
    # Copying a cell is not picking a row.
    assert 'getSelection' in click


def test_a_row_that_left_the_screen_is_not_a_pick_any_more():
    take = _MARKS_JS.split('function take')[1].split('\n    function ')[0]
    assert 'rec.row.isConnected' in take
    assert 'forget();' in take


def test_both_clients_send_the_marks_and_spend_them():
    owl2 = _stack('owl2', 'static', 'src', 'js', 'chatboo_app.js')
    owl1 = _stack('owl1', 'static', 'src', 'js', 'chatboo_component_v2.js')
    for src in (owl1, owl2):
        assert 'ChatbooTurn.buildPayload(' in src
    core = (_ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_turn.js').read_text(encoding='utf-8')
    assert 'global.ChatbooRowMarks' in core
    assert 'marks ? marks.take() : []' in core
    assert 'payload.refs = refs;' in core


def test_the_marking_files_are_served_by_both_stacks():
    owl2 = _stack('owl2', '__manifest__.py')
    assert 'static/src/js/chatboo_row_marks.js' in owl2
    assert 'static/src/css/chatboo_row_marks.css' in owl2
    owl1 = _stack('owl1', 'views', 'assets.xml')
    assert 'static/src/js/chatboo_row_marks.js' in owl1
    assert 'static/src/css/chatboo_row_marks.css' in owl1


def test_a_marked_row_looks_marked_over_the_renderer_tint():
    """The row tint is inline, so the mark paints the cells instead."""
    assert 'tr.o_chatboo_marked > td' in _CSS
    assert '!important' not in _CSS


def test_the_turn_tells_the_user_the_row_can_be_clicked():
    """The prompt has no UI copy of its own: the answer says it, translated."""
    assert 'clicked to pick it' in _SELF
    assert 'click the row or tell you' in _SELF
    assert 'do not' in _SELF.split('Picking a record from a table')[1][:900]
