# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Structured PDF: rasterize non-WinAnsi glyphs; Helvetica keeps Latin labels."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_OWL1_JS = (
    _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
    / 'static' / 'src' / 'js' / 'chatboo_export.js'
)
_OWL2_JS = (
    _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
    / 'static' / 'src' / 'js' / 'chatboo_export.js'
)
_FORECAST = (
    _ROOT / 'common' / 'ai' / 'skills' / 'system' / 'forecast.py'
)
_HELPERS = (
    'pdfWinAnsiOk',
    'pdfSplitTextRuns',
    'pdfGlyphPng',
    'pdfPrepareCell',
    'pdfDrawRichLine',
)


def _export_sources():
    return (
        ('owl1', _OWL1_JS.read_text(encoding='utf-8')),
        ('owl2', _OWL2_JS.read_text(encoding='utf-8')),
    )


def test_both_stacks_define_winansi_glyph_helpers():
    for label, src in _export_sources():
        for name in _HELPERS:
            assert 'function %s' % name in src, '%s missing %s' % (label, name)


def test_generate_report_prepares_cells_and_draws_glyphs():
    for label, src in _export_sources():
        report = src.split('function generateReportPDF', 1)[1]
        assert 'pdfPrepareCell' in report, label
        assert '_pdfGlyphs' in report, label
        draw = report.split('didDrawCell', 1)[1]
        assert '_pdfGlyphs' in draw, label


def test_titles_prose_and_text_pdf_use_rich_line():
    for label, src in _export_sources():
        title_fn = src.split('function drawPdfGroupTitle', 1)[1]
        assert 'pdfDrawRichLine' in title_fn.split('function drawPdfStats', 1)[0], label
        prose = src.split('function drawProseBlocks', 1)[1]
        assert 'pdfDrawRichLine' in prose.split('function extractProseBlocks', 1)[0], label
        text_pdf = src.split('function generateTextPDF', 1)[1]
        assert 'pdfDrawRichLine' in text_pdf.split('function resolveExportHtml', 1)[0], label


def test_forecast_skill_still_emits_sky_emoji():
    text = _FORECAST.read_text(encoding='utf-8')
    assert "function _cielo" in text or "def _cielo" in text
    assert r"\u2600\ufe0f" in text
    assert r"\u26c5" in text
    assert 'pdfPrepareCell' not in text
    assert 'helvetica' not in text
