# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""A clipped file gives its whole text: every Excel sheet, Word paragraphs, plain text."""
from __future__ import annotations

import base64
import importlib.util
import io
import zipfile
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[1] / 'common' / 'utils' / 'file_text.py'
_spec = importlib.util.spec_from_file_location('chatboo_file_text', _PATH)
ft = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ft)


def _b64(raw):
    return base64.b64encode(raw).decode('ascii')


def test_every_sheet_even_when_the_name_says_xls():
    openpyxl = pytest.importorskip('openpyxl')
    wb = openpyxl.Workbook()
    wb.active.title = 'One'
    wb.active.append(['a', 1])
    wb.create_sheet('Two').append(['b', None, 2])
    buf = io.BytesIO()
    wb.save(buf)
    text = ft.file_text('book.xls', '', _b64(buf.getvalue()))
    assert text.startswith('Excel workbook: 2 sheet(s)')
    assert '===== SHEET 1/2: "One"' in text and '===== SHEET 2/2: "Two"' in text
    assert 'a\t1' in text
    assert 'b\t\t2' in text


def test_word_paragraphs_become_lines():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr(
            'word/document.xml',
            '<w:p><w:t>Fish &amp; chips</w:t></w:p><w:p><w:t>two</w:t></w:p>',
        )
    assert ft.file_text('a.docx', '', _b64(buf.getvalue())) == 'Fish & chips\ntwo\n'


def test_plain_text_drops_the_bom():
    raw = '\ufeffñandú'.encode('utf-8')
    assert ft.file_text('n.txt', 'text/plain', _b64(raw)) == 'ñandú'


def test_an_old_word_file_asks_for_docx():
    raw = b'\xD0\xCF\x11\xE0' + b'\0' * 32
    assert '.docx' in ft.file_text('old.doc', 'application/msword', _b64(raw))


def test_nothing_in_nothing_out():
    assert ft.file_text('x', '', '') == ''
    assert ft.split_data_url('data:image/jpeg;base64,QUJD') == ('image/jpeg', 'QUJD')
    assert ft.split_data_url('QUJD') == ('image/png', 'QUJD')
