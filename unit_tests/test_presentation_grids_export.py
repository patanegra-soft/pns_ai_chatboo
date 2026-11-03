# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Always-on Chatboo export contract lives in presentation_grids, not discovery."""
from __future__ import annotations

from pathlib import Path

_GRIDS = (
    Path(__file__).resolve().parents[1]
    / 'common' / 'ai' / 'contexts' / 'domain'
    / 'presentation_grids' / 'presentation_grids.xml'
)
_SELF = (
    Path(__file__).resolve().parents[1]
    / 'common' / 'ai' / 'contexts' / 'domain' / 'self_chatboo' / 'self_chatboo.xml'
)
_OLD_SELF_DIR = (
    Path(__file__).resolve().parents[1]
    / 'common' / 'ai' / 'contexts' / 'domain' / 'self'
)
_DISCOVERY = (
    Path(__file__).resolve().parents[1]
    / 'common' / 'ai' / 'contexts' / 'discovery'
)


def test_a_file_alone_does_not_ask_for_the_listing():
    """PQEC: «pásamelo a pdf» set __show_table__ and the bubble kept the table."""
    text = _GRIDS.read_text(encoding='utf-8')
    assert 'The file is built from `data` even when the chat does not show' in text
    assert 'Do not set it so that the file has a table.' in text
    assert 'A turn that only names a file type gets the card alone.' in text
    assert "Do not copy\n`__show_table__` from an earlier turn's code." in text


def test_the_client_file_falls_back_to_the_turn_rows():
    js = (
        Path(__file__).resolve().parents[1]
        / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
        / 'chatboo_export.js'
    ).read_text(encoding='utf-8')
    body = js.split('function extractTableSections', 1)[1].split('\n    }\n', 1)[0]
    assert 'return clipDataToSections(clipData, opts);' in body


def test_the_card_file_waits_for_the_photos():
    """«pdf con fotos»: /web/image cells became blank boxes in the card PDF."""
    for stack in ('owl1', 'owl2'):
        js = (
            Path(__file__).resolve().parents[1]
            / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
            / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        body = js.split('function fulfillPendingSessionDocuments', 1)[1]
        body = body.split('\n    }\n', 1)[0]
        assert 'var chain = resolveSectionImages(sections);' in body, stack
        assert body.index('resolveSectionImages') < body.index('buildDocument'), stack


def test_presentation_grids_names_pdf_excel_and_word():
    text = _GRIDS.read_text(encoding='utf-8')
    assert '<code>presentation_grids</code>' in text
    assert 'Client file export' in text
    assert 'download card' in text.lower()
    assert 'PDF' in text
    assert 'Excel' in text
    assert 'Word is a session download' in text
    assert '__rich_doc__' in text
    assert 'Word is not a downloadable format' not in text
    assert 'does not call tools' in text
    assert 'previous_result' in text
    assert 'Markdown' in text
    assert 'self' in text
    assert 'Locale' in text
    assert 'mostrar' not in text
    assert 'ir.attachment' in text
    assert 'reportlab' in text
    assert 'openpyxl' in text
    assert 'safe_plan_request' in text
    assert 'caja B' in text
    assert 'landscape' in text.lower()
    assert 'session file' in text
    assert 'Sesame' not in text
    assert '__show_table__' in text
    assert 'assembled by the Chatboo client' in text
    assert 'mirror this turn' in text
    assert 'Excel and Markdown stay tables' in text
    assert '__landscape__' in text
    assert 'other orientation keys' in text
    assert '__title__' in text
    assert '__filename_stem__' in text
    assert '__sheet_caption__' in text
    assert '__column_labels__' in text
    assert '__excel_formulas__' in text
    assert 'Derived columns (xlsx formulas)' in text
    assert 'does not infer' in text
    assert "{'c': '={a}-{b}'}" in text
    assert 'Bootstrap' in text
    assert '"stem"' not in text
    assert 'JSON' not in text.split('Client file export')[1].split('## Soft')[0]
    assert 'apaisado' not in text
    assert 'orizzontale' not in text
    assert '横' not in text
    assert 'espectacular' not in text
    assert 'bonita' not in text
    assert 'impress' not in text


def test_ui_focus_covers_chat_chrome():
    path = (
        Path(__file__).resolve().parents[1]
        / 'common' / 'ai' / 'contexts' / 'domain' / 'ui_focus' / 'ui_focus.xml'
    )
    text = path.read_text(encoding='utf-8')
    assert '<code>ui_focus</code>' in text
    assert 'Chat chrome' in text
    assert 'decode' in text
    assert 'image bytes' in text


def test_old_self_folder_is_gone():
    assert not _OLD_SELF_DIR.exists()


def test_self_does_not_promise_generic_exports():
    text = _SELF.read_text(encoding='utf-8')
    assert '<code>self_chatboo</code>' in text
    assert '<agent_codes>pns_ai_chatboo</agent_codes>' in text
    assert '<product_name>' not in text
    assert '<display_name>' not in text
    assert '<vendor>' not in text
    assert 'PDF' in text and 'Excel' in text and 'Word' in text
    assert 'exports when the user asks for reports' not in text
    assert 'not a self-introduction' in text
    assert 'scope list' in text
    assert 'greeting one-liner' in text
    assert 'At most once per conversation' in text
    assert 'never a self-introduction' in text
    assert 'system://info' not in text
    assert 'qué puedes' not in text
    assert 'vendor facts from the host-resolved vendor block' not in text
    assert 'mention vendor' in text
    assert 'who created you' in text
    assert 'who made you' in text
    assert 'vendor block only' in text


def test_report_delivery_paints_tables_and_keeps_prose():
    text = _GRIDS.read_text(encoding='utf-8')
    assert 'report_outline' in text
    assert 'do not push a server table' not in text
    assert 'inspect_result` for that final delivery' in text
    assert 'cite the figures already in' in text


def test_no_discovery_row_for_presentation_grids():
    if not _DISCOVERY.is_dir():
        return
    for path in _DISCOVERY.glob('*.json'):
        raw = path.read_text(encoding='utf-8')
        assert '"presentation_grids"' not in raw, path.name


def test_chatboo_factory_ai_names_no_tenant_apis():
    root = Path(__file__).resolve().parents[1] / 'common' / 'ai'
    hits = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ('.py', '.md', '.xml', '.json'):
            continue
        text = path.read_text(encoding='utf-8').lower()
        for needle in ('sesame', 'cdmon', 'sesametime'):
            if needle in text:
                hits.append('%s: %s' % (path.name, needle))
    assert hits == [], 'Chatboo factory ai/ names tenant APIs: %s' % hits


def test_grids_teach_svg_cards_and_presentation_axes():
    grids = _GRIDS.read_text(encoding='utf-8')
    assert 'kind: clock' in grids
    assert "'instant'" in grids
    assert 'yyyy-mm-dd' in grids
    assert 'any app' in grids
    assert 'compose-agent' in grids
    assert 'compose-model' in grids
    assert 'foot-verbose' in grids
    assert 'foot-laconic' in grids
    assert 'show-table' in grids
    assert 'show-chart' in grids
    assert "result = {'card'" in grids or "'card':" in grids
    assert 'apply_pajama_coloring' in grids
    assert 'Table vs list' in grids
    assert 'Presentation axes' in grids


def test_grids_teach_excel_formulas():
    grids = _GRIDS.read_text(encoding='utf-8')
    assert '__excel_formulas__' in grids
    assert "={'c': '={a}-{b}'}" in grids or "{'c': '={a}-{b}'}" in grids
    assert 'does not infer' in grids
