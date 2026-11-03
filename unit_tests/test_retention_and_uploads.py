# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Session retention for every user, upload limit, local voices first."""
from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

from _engine_params import install as install_engine_params

_ROOT = Path(__file__).resolve().parents[1]
_COMMON = _ROOT / 'common'


def _icp_module():
    install_engine_params()
    path = _COMMON / 'utils' / 'chatboo_product_icp.py'
    spec = importlib.util.spec_from_file_location('_chatboo_icp', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Params:
    def __init__(self, values):
        self.values = values

    def sudo(self):
        return self

    def get_param(self, key, default=None):
        return self.values.get(key, default)


def _env(values):
    return {'ir.config_parameter': _Params(values)}


def _data_url(size):
    return 'data:image/png;base64,' + base64.b64encode(b'x' * size).decode()


def test_upload_limit_names_the_first_oversized_upload():
    icp = _icp_module()
    env = _env({icp.ICP_UPLOAD_MAX_BYTES: '1000'})
    assert icp.oversized_upload(env, [_data_url(1000)], []) is None
    assert icp.oversized_upload(
        env, [_data_url(1001)], [], image_names=['foto.png'],
    ) == 'foto.png'
    assert icp.oversized_upload(env, [_data_url(1001)], []) == ''
    files = [{'name': 'big.xlsx', 'data': base64.b64encode(b'x' * 2000).decode()}]
    assert icp.oversized_upload(env, None, files) == 'big.xlsx'


def test_upload_limit_zero_falls_back_to_the_default():
    icp = _icp_module()
    env = _env({icp.ICP_UPLOAD_MAX_BYTES: '0'})
    assert icp.upload_max_bytes(env) == icp.DEFAULT_UPLOAD_MAX_BYTES
    big = 'data:image/png;base64,' + base64.b64encode(
        b'x' * (icp.DEFAULT_UPLOAD_MAX_BYTES + 1)).decode()
    assert icp.oversized_upload(env, [big], []) == ''
    assert icp.upload_max_bytes(_env({})) == icp.DEFAULT_UPLOAD_MAX_BYTES


def test_upload_violation_count_and_total():
    icp = _icp_module()
    env = _env({icp.ICP_UPLOAD_MAX_BYTES: '1000'})
    many = [_data_url(10) for _i in range(icp.MAX_UPLOAD_FILES + 1)]
    out = icp.upload_violation(env, many, [])
    assert out['kind'] == 'count' and out['limit'] == icp.MAX_UPLOAD_FILES
    assert icp.upload_violation(env, [_data_url(10)], []) is None
    out = icp.upload_violation(env, [_data_url(1001)], [])
    assert out['kind'] == 'file' and out['limit'] == 1000
    old_total = icp.MAX_UPLOAD_TOTAL_BYTES
    try:
        icp.MAX_UPLOAD_TOTAL_BYTES = 100
        out = icp.upload_violation(env, [_data_url(60), _data_url(60)], [])
        assert out['kind'] == 'total' and out['limit'] == 100
    finally:
        icp.MAX_UPLOAD_TOTAL_BYTES = old_total


def test_stream_checks_upload_limit_on_both_stacks():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers'
            / 'chatboo.py'
        ).read_text(encoding='utf-8')
        assert 'upload_violation(request.env, images, files, image_names)' in src


def test_sessions_purged_for_every_user_and_survive_user_deletion():
    src = (_COMMON / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
    field = src.split('user_id = fields.Many2one(', 1)[1].split(')', 1)[0]
    assert "ondelete='set null'" in field
    assert 'required=True' not in field
    body = src.split('def _cleanup_old_sessions', 1)[1].split('\n    def ', 1)[0]
    assert "('user_id', '=', self.env.user.id)" not in body
    cron = (_COMMON / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')
    maint = cron.split('def cron_maintenance', 1)[1].split('\n    def ', 1)[0]
    assert '_cleanup_old_sessions()' in maint


def test_unset_retention_keeps_sessions_and_is_not_seeded():
    src = (_COMMON / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
    body = src.split('def _cleanup_old_sessions', 1)[1].split('\n    def ', 1)[0]
    assert 'raw_retention is None or raw_retention is False' in body
    assert 'DEFAULT_HISTORY_RETENTION_DAYS' not in src
    assert not (_COMMON / 'data' / 'chatboo_icp_data.xml').exists()
    for stack in ('owl1', 'owl2'):
        manifest = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / '__manifest__.py'
        ).read_text(encoding='utf-8')
        assert 'chatboo_icp_data.xml' not in manifest
    icp = _icp_module()
    settings = icp.read_product_settings(_env({}))
    assert settings['history_retention_days'] == 0
    settings = icp.read_product_settings(
        _env({icp.ICP_HISTORY_RETENTION_DAYS: '45'}),
    )
    assert settings['history_retention_days'] == 45


def test_speech_prefers_local_voices():
    js = (_COMMON / 'static' / 'src' / 'js' / 'chatboo_tts.js').read_text(encoding='utf-8')
    assert 'v.localService' in js
    assert 'function allowRemoteVoices' in js
    assert 'pns_chatboo_allow_remote_voices' in js
    assert 'if (!voice)' in js
    assert 'return localAny' in js
    icp = _icp_module()
    assert icp.ICP_ALLOW_REMOTE_VOICES == 'pns_ai_chatboo.allow_remote_voices'
    assert icp.read_product_settings(_env({}))['allow_remote_voices'] is False
    assert icp.read_product_settings(
        _env({icp.ICP_ALLOW_REMOTE_VOICES: 'True'}),
    )['allow_remote_voices'] is True
