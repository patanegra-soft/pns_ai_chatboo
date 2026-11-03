# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Health stays quiet, and a copied table does not run as a formula."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _body(src, name, until):
    return src.split('def %s' % name)[1].split(until)[0]


def test_health_and_providers_do_not_leak():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
        ).read_text(encoding='utf-8')
        health = _body(src, 'check_health', '\n    @http.route')
        assert '_chatboo_access_denied()' in health
        assert health.index('_chatboo_access_denied()') < health.index(
            '_resolve_active_provider'
        )
        assert "message': str(e)" not in health
        assert 'self._chatboo_failed()' in health
        providers = _body(src, 'list_providers', '\n    # ')
        assert "Provider.sudo().search" not in providers
        assert 'self._chatboo_failed()' in providers
        stream = _body(src, 'chat_stream', '\n    def _sse_headers')
        assert "{'error': str(e)}" not in stream
        assert 'self._chatboo_failed()' in stream
        reply = _body(src, '_json_response', '\n    def ')
        assert 'response.status_code = status' in reply


def test_tsv_copy_leaves_numbers_and_prefixes_formulas():
    for stack in ('owl1', 'owl2'):
        js = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        cell = js.split('function clipCellText')[1].split('function clipDataToTsv')[0]
        assert "/^[+-]?\\d+(?:\\.\\d+)?$/" in cell
        assert "/^[=+\\-@]/" in cell
        assert "\"'\" + text" in cell
        tsv = js.split('function clipDataToTsv')[1].split('function extractTableSections')[0]
        assert 'clipCellText(c)' in tsv
        assert 'pdfCellText(c)' not in tsv
        assert 'clipExcelFormulas' not in cell
