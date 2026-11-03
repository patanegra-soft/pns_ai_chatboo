# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""What a user can reach over RPC is what the routes already check."""
import base64
import importlib.util
import io
import re
import zipfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_MODELS = _ROOT / 'common' / 'models'
_SESSION = (_MODELS / 'chatboo_session.py').read_text(encoding='utf-8')
_PAGE = (_MODELS / 'chatboo_canvas_page.py').read_text(encoding='utf-8')
_JOB = (_MODELS / 'chatboo_async_request.py').read_text(encoding='utf-8')
_STACKS = ('owl1', 'owl2')


def _method(src, name):
    return src.split('def %s(' % name, 1)[1].split('\n    def ', 1)[0]


def test_a_session_cannot_be_handed_to_someone_else():
    write = _method(_SESSION, 'write')
    assert 'not self.env.su' in write
    assert "'user_id' in vals" in write
    assert "vals['user_id'] != self.env.uid" in write
    assert 'raise AccessError' in write


def test_session_work_that_spends_a_provider_is_not_public():
    for name in ('page_url', 'page_html', 'page_edit', 'paint_canvas',
                 'fulfill_client_export'):
        assert not re.search(r'\n    def %s\(' % name, _SESSION), name
        assert '\n    def _%s(' % name in _SESSION, name


def test_a_shared_page_is_only_made_by_the_share_route():
    create = _method(_PAGE, 'create')
    assert create.index('if not self.env.su:') < create.index('super(')
    write = _method(_PAGE, 'write')
    assert write.index('_SYSTEM_FIELDS.intersection(vals)') < write.index('super()')
    assert "frozenset({'design', 'owner_id'})" in _PAGE


def test_portal_users_do_not_list_internal_people():
    matching = _method(_PAGE, 'people_matching')
    assert matching.index('self.env.user.share') < matching.index('.search(')


def test_maintenance_runs_only_as_the_system():
    maint = _method(_JOB, 'cron_maintenance')
    gate = 'if not (self.env.su or self.env.user._is_system()):'
    assert maint.index(gate) < maint.index('_reclaim_stuck')


def test_canvas_job_rows_are_read_only_for_their_owner():
    security = (_ROOT / 'common' / 'security' / 'security.xml').read_text(encoding='utf-8')
    rule = security.split('chatboo_canvas_job_user_rule', 1)[1].split('</record>', 1)[0]
    assert '<field name="perm_read" eval="True"/>' in rule
    for perm in ('write', 'create', 'unlink'):
        assert '<field name="perm_%s" eval="False"/>' % perm in rule


@pytest.mark.parametrize('stack', _STACKS)
def test_the_page_cannot_call_out_or_post_anywhere(stack):
    ctrl = (_ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers'
            / 'chatboo.py').read_text(encoding='utf-8')
    csp = ctrl.split('_PAGE_CSP = (', 1)[1].split('\n    )', 1)[0]
    for part in ("default-src 'none'", "connect-src 'self'",
                 "form-action 'none'", "frame-ancestors 'self'"):
        assert part in csp
    assert 'http' not in csp
    for route in ("'/chatboo/canvas/<int:session_id>', type='http'",
                  "'/chatboo/page/<int:page_id>', type='http'"):
        body = ctrl.split(route, 1)[1].split('@http.route', 1)[0]
        assert 'headers=self._page_headers()' in body
    people = ctrl.split('def chatboo_shared_page_people', 1)[1].split('\n    def ', 1)[0]
    assert people.index('user_has_chatboo_access') < people.index('_readable_page')


def test_the_owl1_stats_window_escapes_the_model_name():
    js = (_ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'static' / 'src'
          / 'js' / 'chatboo_component_v2.js').read_text(encoding='utf-8')
    assert '${modelLabel}' not in js
    assert js.count('${this._escapeHtml(modelLabel)}') == 2


def test_speech_reads_html_in_an_inert_document():
    js = (_ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_tts.js').read_text(encoding='utf-8')
    body = js.split('function extractFullText', 1)[1].split('\n    function ', 1)[0]
    assert 'document.implementation.createHTMLDocument' in body
    assert 'document.createElement' not in body


def _file_text():
    spec = importlib.util.spec_from_file_location(
        'chatboo_file_text', _ROOT / 'common' / 'utils' / 'file_text.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_word_body_that_unpacks_too_far_is_refused_not_read(monkeypatch):
    mod = _file_text()
    monkeypatch.setattr(mod, 'DOCX_BODY_MAX_BYTES', 1024)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('word/document.xml', '<w:p>' + 'a' * 4096 + '</w:p>')
    b64 = base64.b64encode(buf.getvalue()).decode()
    out = mod.file_text('big.docx', '', b64)
    assert out.startswith('[Word big.docx: could not be read')
    assert 'a' * 100 not in out
