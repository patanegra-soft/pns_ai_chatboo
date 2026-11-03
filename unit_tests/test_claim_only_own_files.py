# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""A session only takes the files its owner's turn made (PNS-82).

Another user's attachment, or one already hanging on a record, is not moved
here and its chip does not reach the message.
"""
import ast
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
_JOB = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')

_OWNER, _OTHER = 'ana', 'bob'


class _Att:
    def __init__(self, att_id, create_uid, res_model=False, res_id=False):
        self.id = att_id
        self.create_uid = create_uid
        self.res_model = res_model
        self.res_id = res_id

    def exists(self):
        return True

    def write(self, vals):
        self.res_model = vals['res_model']
        self.res_id = vals['res_id']


class _Attachments:
    def __init__(self, rows):
        self.rows = {row.id: row for row in rows}

    def sudo(self):
        return self

    def browse(self, att_id):
        return self.rows[att_id]


class _Session:
    _name = 'chatboo.session'
    id = 7
    user_id = _OWNER

    def __init__(self, rows):
        self.env = {'ir.attachment': _Attachments(rows)}

    def ensure_one(self):
        return self


def _claim():
    tree = ast.parse(_SESSION)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == '_claim_turn_file_chips'
    )
    ns = {'re': re}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'chatboo_session', 'exec'), ns)
    return ns['_claim_turn_file_chips']


def _chip(att_id):
    return {'name': 'f%s' % att_id, 'url': '/pns_ai_mcp/session_file/%s/f' % att_id}


def test_another_users_file_is_not_taken():
    theirs = _Att(1, _OTHER)
    kept = _claim()(_Session([theirs]), [_chip(1)])
    assert kept == []
    assert theirs.res_model is False


def test_a_file_on_another_record_is_not_moved():
    elsewhere = _Att(2, _OWNER, 'chatboo.session', 99)
    kept = _claim()(_Session([elsewhere]), [{'attachment_id': 2}])
    assert kept == []
    assert elsewhere.res_id == 99


def test_the_owners_loose_file_hangs_on_the_session():
    mine = _Att(3, _OWNER)
    kept = _claim()(_Session([mine]), [_chip(3)])
    assert kept == [_chip(3)]
    assert (mine.res_model, mine.res_id) == ('chatboo.session', 7)


def test_a_file_already_here_and_a_pending_export_stay():
    here = _Att(4, _OTHER, 'chatboo.session', 7)
    pending = {'name': 'informe.docx', 'pending': True, 'fulfill': 'docx'}
    kept = _claim()(_Session([here]), [{'attachment_id': 4}, pending])
    assert kept == [{'attachment_id': 4}, pending]


def test_the_chip_methods_are_not_rpc():
    for name in (
        'claim_turn_file_chips',
        'apply_assistant_download_chips',
        'stage_assistant_download_chips',
        'consume_staged_assistant_download_chips',
    ):
        assert '    def %s(' % name not in _SESSION
        assert '    def _%s(' % name in _SESSION


def test_message_files_are_only_the_ones_kept():
    for name in ('_apply_assistant_download_chips', '_stage_assistant_download_chips'):
        body = _SESSION.split('    def %s(' % name, 1)[1].split('\n    def ', 1)[0]
        assert 'chips = self._claim_turn_file_chips(chips)' in body
    assert '_assistant_files = session._claim_turn_file_chips(_assistant_files)' in _JOB
