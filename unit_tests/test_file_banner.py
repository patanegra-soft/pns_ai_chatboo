# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Download cards: both stacks paint msg.files as o_chatboo_file_banner_*."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from _deployed import deployed

_ROOT = Path(__file__).resolve().parents[1]


def test_owl2_template_and_css_have_file_banner():
    xml = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    css = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'css' / 'chatboo_floating.css'
    ).read_text(encoding='utf-8')
    js = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    assert 'o_chatboo_file_banner_list' in xml
    assert '_fileBannerCardClass' in xml
    assert 'tipDownloadFile' in xml
    assert 'o_chatboo_file_banner_card' in js
    assert '.o_chatboo_file_banner_card' in css
    assert '.o_chatboo_file_banner_pdf' in css
    assert '.o_chatboo_file_banner_excel' in css
    assert '.o_chatboo_file_banner_word' in css
    assert '_t("Download")' in js


def test_owl1_template_and_css_have_file_banner():
    js = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    css = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'css' / 'chatboo_floating.css'
    ).read_text(encoding='utf-8')
    assert 'o_chatboo_file_banner_card' in js
    assert '_fileBannerCardClass' in js
    assert "_t('Download')" in js
    assert '.o_chatboo_file_banner_excel' in css
    assert '.o_chatboo_file_banner_word' in css


def test_async_save_reads_done_meta_assistant_files():
    src = (
        _ROOT / 'common' / 'models' / 'chatboo_async_request.py'
    ).read_text(encoding='utf-8')
    assert "get('assistant_files')" in src
    assert 'coalesce_download_chips' in src
    assert "get('clip_data')" in src


def test_export_js_uses_turn_card_before_clip_data():
    for stack in ('owl1', 'owl2'):
        js = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        assert 'clipDataToSections' in js
        assert 'msg.clip_data' in js
        assert 'downloadAsPDFLegacy' in js
        extract = js.split('function extractTableSections', 1)[1]
        assert extract.find('sectionsFromRenderedHtml') < extract.find(
            'clipDataToSections'
        )
        assert 'o_ai_block_title' in js
        assert 'function cardHtmlForExport' in js
        assert 'function exportProseFromMessage' in js
        assert 'blockTitleFromEl' in js
        pdf = js.split('function downloadAsPDF(', 1)[1]
        assert 'prose: extras.prose' in pdf
        word = js.split('function downloadAsWord', 1)[1]
        assert 'prose: prose' in word.split('buildDocument', 1)[1][:400]
        # Dual output, same rows: icons must not fall back to the bubble phrase.
        copy_md = js.split('function copyToClipboard', 1)[1]
        assert copy_md.find('clipDataToMarkdown(msg.clip_data)') < copy_md.find(
            'resolveExportHtml(msg)'
        )
        assert copy_md.find('clipDataToTsv(msg.clip_data)') < copy_md.find(
            'htmlToPlainExportText'
        )
        pdf = js.split('function downloadAsPDF(', 1)[1]
        assert pdf.find('downloadAsPDFLegacy') < pdf.find('generateWysiwygPDF')
        assert 'resolveExportSections(exportHtml, msg.clip_data, { images: true })' in pdf
        assert 'collectPaintedChartPngs' in js
        assert 'pdfShouldBeLandscape' in js
        assert "rowPageBreak: 'avoid'" in js
        excel = js.split('function downloadAsExcel', 1)[1]
        assert 'extractTableSections(exportHtml, msg.clip_data)' in excel
        assert 'sectionsForServer(sections, msg.clip_data)' in excel
        assert 'clipExcelFormulas' in js
        assert 'excel_formulas' in js
        assert '/chatboo/export/xlsx' in excel
        assert "typeof cell === 'number'" in js
        assert 'XLSX.writeFile' not in excel
        assert 'writeExcelWorkbook' not in js
        assert 'freezeHeaderInXlsx' not in js


def test_session_keeps_clip_data_for_icons_after_reload():
    session = (
        _ROOT / 'common' / 'models' / 'chatboo_session.py'
    ).read_text(encoding='utf-8')
    keys = session.split('_PRESERVED_ASSISTANT_KEYS', 1)[1]
    assert "'clip_data'" in keys.split(')', 1)[0]
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    load = owl1.split('async _loadSession', 1)[1].split('_resumeRunningTurn', 1)[0]
    assert 'msg.clip_data =' not in load
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    assert 'clip_data: m.clip_data || null' in owl2
    persist = (
        _ROOT / 'common' / 'models' / 'chatboo_async_request.py'
    ).read_text(encoding='utf-8')
    assert persist.count("clip_data': _clip_data") >= 2
    assert 'done_meta_has_deliverable' in persist


def test_banner_download_uses_chip_name_not_attachment_id():
    persist = (
        _ROOT / 'common' / 'models' / 'chatboo_session.py'
    ).read_text(encoding='utf-8')
    assert 'content_download_url' in persist
    for stack in ('owl1', 'owl2'):
        export = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        assert 'function sessionFileHref' in export
        assert 'download=true' in export
        href = export.split('function sessionFileHref')[1].split('function ')[0]
        assert '/^(blob:|data:)/i.test(url)' in href
        gen = export.split('function generateFilename', 1)[1]
        assert gen.find('clipDataTitle(msg.clip_data)') < gen.find(
            'contentFilename(userPrompt'
        )
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    assert 't-att-href="_fileDownloadHref(mfile)"' in owl1
    assert 't-att-href="mfile.url" target="_blank"' not in owl1
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    assert 't-att-href="_fileDownloadHref(mfile)"' in owl2
    assert 't-att-href="mfile.url" target="_blank"' not in owl2


def test_pdf_card_opens_in_the_viewer_both_stacks():
    """A PDF card says type=application/pdf; the click goes to Chatboo's PDF viewer."""
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    owl2_js = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    owl2_xml = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    for js, tpl in ((owl1, owl1), (owl2_js, owl2_xml)):
        assert tpl.count('t-att-type="_fileLinkType(mfile)"') == 2
        assert "=== 'pdf' ? 'application/pdf'" in js or '=== "pdf" ? "application/pdf"' in js
        assert 'this._openViewer(ev)' in js
        assert 'window.chatbooPdfViewer' in js
        assert '_openImageViewer' not in js
        assert 'URL.createObjectURL(file)' in js
    assets = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'views' / 'assets.xml'
    ).read_text(encoding='utf-8')
    manifest = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / '__manifest__.py'
    ).read_text(encoding='utf-8')
    for name in ('js/chatboo_pdf_viewer.js', 'css/chatboo_pdf_viewer.css'):
        assert '/pns_ai_chatboo/static/src/' + name in assets
        assert "'pns_ai_chatboo/static/src/" + name + "'," in manifest


_PDF_VIEWER = _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_pdf_viewer.js'

_PDF_SCRIPT = r"""
global.window = { location: { href: 'https://odoo.example/web', origin: 'https://odoo.example' } };
require(process.argv[2]);
function anchor(href, attrs, words) {
  attrs = attrs || {};
  return {
    href: href, textContent: words || '',
    getAttribute: function (n) { return n in attrs ? attrs[n] : null; },
    closest: function () { return this; },
  };
}
function inside(a) { return { closest: function () { return a; } }; }
var v = window.chatbooPdfViewer;
console.log(JSON.stringify({
  card: v.optionsFor(inside(anchor('https://odoo.example/web/content/7?download=true',
                                    { type: 'application/pdf', title: 'Invoice' }, 'Invoice'))),
  blob: v.optionsFor(inside(anchor('blob:https://odoo.example/abc',
                                    { type: 'application/pdf', title: 'Drop' }, 'Drop'))),
  path: v.optionsFor(inside(anchor('https://odoo.example/files/report.PDF', {}, 'report'))),
  name: v.optionsFor(inside(anchor('https://odoo.example/web/content/8', { download: 'a.pdf' }, 'a'))),
  away: v.optionsFor(inside(anchor('https://cdn.example/report.pdf', {}, 'report'))),
  other: v.optionsFor(inside(anchor('https://odoo.example/web/content/9', { type: 'text/csv' }, 'x'))),
  none: v.optionsFor(inside(null)),
}));
"""


@pytest.mark.skipif(not shutil.which('node'), reason='no node here')
def test_what_a_pdf_link_offers(tmp_path):
    script = tmp_path / 'run.js'
    script.write_text(_PDF_SCRIPT, encoding='utf-8')
    out = json.loads(subprocess.run(
        ['node', str(script), str(_PDF_VIEWER)], capture_output=True, text=True, check=True,
    ).stdout)
    assert out['card'] == {
        'pdf': 'https://odoo.example/web/content/7?download=true',
        'tab': 'https://odoo.example/web/content/7?download=true',
        'alt': 'Invoice',
    }
    assert out['blob']['pdf'].startswith('blob:')
    assert out['path']['pdf'].endswith('/report.PDF')
    assert out['name']['pdf'].endswith('/web/content/8')
    # pdf.js cannot read another site; that link keeps its tab.
    assert out['away'] is None
    assert out['other'] is None
    assert out['none'] is None


def test_pdf_opens_in_odoo_pdfjs():
    text = _PDF_VIEWER.read_text(encoding='utf-8')
    assert '"/web/static/lib/pdfjs/web/viewer.html?file="' in text
    assert 'encodeURIComponent(opts.pdf)' in text


def test_word_icon_after_excel_both_stacks():
    for stack in ('owl1', 'owl2'):
        js = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        assert 'function downloadAsWord' in js
        assert 'xmlns:w="urn:schemas-microsoft-com:office:word"' in js
        assert 'bubbleLooksLikeRichDoc' in js
        assert 'espectacular' not in js
        sanitize = js.split('function sanitizeWordClone', 1)[1]
        assert 'o_ai_export_bar' in sanitize
        assert 'o_ai_chart_host' in sanitize
        assert 'echarts-tooltip' in sanitize
        word_fn = js.split('function downloadAsWord', 1)[1]
        assert word_fn.find('extractTableSections') < word_fn.find(
            'bubbleLooksLikeRichDoc'
        )
        assert 'function buildDocument' in js
        assert 'function ensureChartPngs' in js
        assert 'function fulfillPendingSessionDocuments' in js
        assert 'o_ai_word_figure' in js
        assert 'fulfill_export' in js
        assert 'client_fulfill' not in js
        excel = js.find('_downloadAsExcel') if '_downloadAsExcel' in js else js.find('downloadAsExcel')
        word = js.find('downloadAsWord')
        assert word > 0
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    assert owl1.find('_downloadAsExcel') < owl1.find('_downloadAsWord')
    assert "_t('Download as Word')" in owl1
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    assert owl2.find('_downloadAsExcel') < owl2.find('_downloadAsWord')
    app = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    assert '_t("Download as Word")' in app


def test_pdf_export_is_structured_keeps_painted_chart():
    """Icon PDF is AutoTable + painted canvas; toolbar out; no locale lexicon."""
    for stack in ('owl1', 'owl2'):
        js = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        assert 'apaisado' not in js
        assert 'orizzontale' not in js
        assert 'function collectStandaloneImageFigures' in js
        assert 'function figuresFromHtmlOrEl' in js
        assert 'figure: true' in js
        assert 'function collectPaintedChartPngs' in js
        assert 'chartHostIsPainted' in js
        assert 'snapshotPng' in js
        assert 'getDataURL' in js
        assert "backgroundColor: '#ffffff'" in js
        assert 'function pdfShouldBeLandscape' in js
        assert "rowPageBreak: 'avoid'" in js
        host = js.split('function buildPdfCaptureHost', 1)[1].split(
            'function saveCanvasAsPdf', 1
        )[0]
        kill = host.split('querySelectorAll', 1)[1].split(')', 1)[0]
        assert 'o_ai_chart_toolbar' in kill
        assert 'o_ai_export_bar' in kill
        assert 'o_ai_chart_host' not in kill
        assert 'canvas' not in kill
        pdf = js.split('function downloadAsPDF(', 1)[1].split(
            'function inferNumericColumnStyles', 1
        )[0]
        assert pdf.find('downloadAsPDFLegacy') < pdf.find('generateWysiwygPDF')
        charts = (
            deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js')
        ).read_text(encoding='utf-8')
        assert 'snapshotPng: snapshotBlockPng' in charts
        assert 'getDataURL' in charts
        assert 'backgroundColor: "#ffffff"' in charts


def test_client_export_fulfill_is_the_session_source():
    session = (
        _ROOT / 'common' / 'models' / 'chatboo_session.py'
    ).read_text(encoding='utf-8')
    assert 'def _fulfill_client_export' in session
    for stack in ('owl1', 'owl2'):
        ctrl = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'controllers' / 'chatboo.py'
        ).read_text(encoding='utf-8')
        assert '/chatboo/sessions/fulfill_export' in ctrl
        assert '/chatboo/export/xlsx' in ctrl
        assert 'icon_xlsx_payload' in ctrl
        app = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / (
                'chatboo_app.js' if stack == 'owl2' else 'chatboo_component_v2.js'
            )
        ).read_text(encoding='utf-8')
        assert '_fulfillChipClick' in app
        assert 'fulfillPendingSessionDocuments' in app


def test_owl1_load_keeps_pending_export_chips():
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    load = owl1.split("if (msg.role === 'assistant')", 1)[1].split(
        '_rebuildContextInfo', 1,
    )[0]
    assert 'f.url || f.pending' in load
    assert 'f && f.url)' not in load


def test_export_mirrors_turn_and_keeps_chart_width():
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    xml = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    app = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    assert 'messageWantsWideCanvas' in owl1
    assert 'messageWantsWideCanvas' in app
    assert 'max-width: 80%' not in owl1
    assert 'max-width:85%' not in xml
    for stack in ('owl1', 'owl2'):
        js = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        charts = (
            deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js')
        ).read_text(encoding='utf-8')
        assert 'function resolveExportSections' in js
        assert 'function resolveExportCharts' in js
        assert 'include_table' in js
        assert 'include_chart' in js
        assert '@page' in js
        assert 'mso-page-orientation' in js
        assert 'function statsAoaToWordHtml' in js
        assert 'function resolveExportRows' in js
        assert 'function analyzeForStats' in charts
        assert 'o_ai_word_figure' in js
        assert 'width="' in js.split('function chartFiguresHtml', 1)[1]
        style = js.split('var WORD_STYLE', 1)[1].split('function escapeWordText', 1)[0]
        assert 'table.o_ai_word_figure td img' in style
        assert 'max-height:none' in style
        assert 'max-width:72px' in style
        pdf = js.split("if (kind === 'pdf')", 1)[1]
        assert 'statsAoa: spec.statsAoa' in pdf
        icon = js.split('function downloadAsPDF(', 1)[1].split(
            'function inferNumericColumnStyles', 1
        )[0]
        assert 'statsAoa: extras.statsAoa' in icon
        assert 'composeHtmlBody(title, sections, charts, rich, statsHtml, landscape, proseHtml)' in js
        assert 'width:680' in js or "width:' + width" in js
        assert 'apaisado' not in js
        assert 'statsTableHtml: statsTableHtml' in charts
        assert 'mountSeriesStats' in charts
        assert '_t("Statistics")' in charts
        assert '_t("Mean")' in charts
        assert '_t("Median")' in charts
        assert "Tabla " not in js
        assert "_t('Table')" in js
        assert "_t('Statistics')" in js
        assert "_t('Chart')" not in js
        assert "_t('Export')" not in js
        assert "|| 'Export'" not in js
        assert 'function isTurnDocumentTitle' not in js
        assert 'exportGroupHtml(_STAT_I18N.title' not in js
        assert 'o_chatboo_export_group' in js
        assert 'function drawPdfGroupTitle' in js


def test_financial_health_skill_asks_for_judgment_not_inventory():
    en = (
        _ROOT / 'common' / 'ai' / 'skills' / 'system' / 'financial_health.md'
    ).read_text(encoding='utf-8')
    assert 'version: 2.17' in en
    assert 'estado financiero' in en
    assert 'informe financiero' in en
    assert 'Cover every JSON table' not in en
    assert 'material facts' in en
    assert 'analisis-financiero' not in en
    assert 'Spanish twin' not in en
    assert not (
        _ROOT / 'common' / 'ai' / 'skills' / 'system' / 'analisis_financiero.md'
    ).is_file()
    assert not (
        _ROOT / 'common' / 'ai' / 'skills' / 'system' / 'analisis_financiero.py'
    ).is_file()
