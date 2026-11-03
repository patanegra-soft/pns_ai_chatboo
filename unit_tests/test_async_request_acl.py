# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Chatboo jobs: users read their own, the server creates them (PNS-55)."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CSV = (_ROOT / 'common' / 'security' / 'ir.model.access.csv').read_text(encoding='utf-8')
_RULES = (_ROOT / 'common' / 'security' / 'security.xml').read_text(encoding='utf-8')
_JOB = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')


def test_async_request_acl_is_read_only_for_users():
    line = [l for l in _CSV.splitlines() if 'model_chatboo_async_request' in l][0]
    assert line.rstrip().endswith(',1,0,0,0')


def test_async_request_rule_is_read_only():
    rule = _RULES.split('chatboo_async_request_user_rule', 1)[1].split('</record>', 1)[0]
    assert '<field name="perm_write" eval="False"/>' in rule
    assert '<field name="perm_create" eval="False"/>' in rule


def test_jobs_are_created_by_the_server():
    body = _JOB.split('def _enqueue', 1)[1].split('def _on_crash', 1)[0]
    assert 'self.sudo().create({' in body


def test_the_worker_writes_jobs_as_the_server():
    process = _JOB.split('    def _process(self):', 1)[1].split('\n    def ', 1)[0]
    assert "self.sudo().write({'state': 'running'" in process
    finalize = _JOB.split('    def _finalize(', 1)[1].split('\n    def ', 1)[0]
    assert 'job.sudo().write(vals)' in finalize
    assert 'job.sudo().write(_write)' in finalize
    assert "job.sudo().write({'state': 'error', 'error': error})" in finalize
    assert 'job.write(' not in finalize.replace('job.sudo().write(', '')
    cancel = _JOB.split('    def _cancel_pending(', 1)[1].split('\n    def ', 1)[0]
    reclaim = _JOB.split('    def _reclaim_one(', 1)[1].split('\n    def ', 1)[0]
    assert 'self.sudo().write({' in cancel
    assert 'self.sudo().write({' in reclaim


def test_recover_chips_checks_the_owner():
    body = _SESSION.split('def recover_orphan_download_chips', 1)[1].split(
        'def append_local_ack', 1)[0]
    assert 'self.user_id.id != self.env.uid' in body
    assert 'return []' in body
