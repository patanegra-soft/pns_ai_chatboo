# -*- coding: utf-8 -*-
"""A finished PDF turn must stay on screen and in the session.

The job was done and the model had answered. The client then reloaded the
session because the stream always said authored=True. The row did not have
the bubbles, so prompt, file card and answer vanished.
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_JOB = (
    _ROOT / 'common' / 'models' / 'chatboo_async_request.py'
).read_text(encoding='utf-8')
_OWL1_CTRL = (
    _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
).read_text(encoding='utf-8')
_OWL2_CTRL = (
    _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
).read_text(encoding='utf-8')
_OWL1_JS = (
    _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
    / 'chatboo_component_v2.js'
).read_text(encoding='utf-8')
_OWL2_JS = (
    _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
    / 'chatboo_app.js'
).read_text(encoding='utf-8')


def test_the_worker_commits_the_session_before_it_asks_the_model():
    process = _JOB.split('def _process(')[1].split('\n    def ')[0]
    after = process.split('remember_documents(turn_docs)')[1]
    assert 'self.env.cr.commit()' in after.split('self._start_heartbeat')[0]


def test_authored_is_only_true_when_the_session_has_the_turn():
    finalize = _JOB.split('def _finalize(')[1].split('\n    def ')[0]
    assert "_merged['session_saved'] = True" in finalize
    for src in (_OWL1_CTRL, _OWL2_CTRL):
        stream = src.split('def generate_stream(')[1].split('return Response')[0]
        assert "'authored': bool(done_evt.get('session_saved'))" in stream
        assert "'authored': True" not in stream


def test_the_client_does_not_eat_the_live_turn_when_the_row_is_empty():
    owl1 = _OWL1_JS.split('if (__meta.authored)')[1].split('// 3. Add Assistant')[0]
    assert 'this.messages.length < kept.length' in owl1
    owl2 = _OWL2_JS.split('const _authored = !!(lastMeta && lastMeta.authored)')[1].split(
        'await this._refreshSessions()',
    )[0]
    assert '(this.state.messages || []).length < kept.length' in owl2


def test_the_client_does_not_write_live_chips_over_the_session():
    owl1_done = _OWL1_JS.split('if (__meta.authored)')[0]
    assert 'this._skipTurnSave = true' in owl1_done[-400:]
    owl2 = _OWL2_JS.split('const _authored = !!(lastMeta && lastMeta.authored)')[1].split(
        'await this._refreshSessions()',
    )[0]
    assert 'await this._persist()' not in owl2
