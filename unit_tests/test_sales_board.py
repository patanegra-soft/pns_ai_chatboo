# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""/sales-board is the factory example of movable cards in the chat."""
from pathlib import Path

_SYSTEM = Path(__file__).resolve().parents[1] / 'common' / 'ai' / 'skills' / 'system'


def _code():
    return (_SYSTEM / 'sales_board.py').read_text(encoding='utf-8')


def test_cards_are_painted_by_the_engine_not_a_page():
    src = _code()
    assert "'show_mode': 'dashboard'" in src
    assert "'groups':" in src
    assert "'dashboard_id': 'sales-board'" in src
    assert 'canvas' not in src.lower() and 'design' not in src.lower()


def test_cards_mix_tables_charts_and_a_wide_card():
    src = _code()
    assert "'show_mode': 'table'" in src
    assert "'show_mode': 'show-chart'" in src
    assert "'span': 2" in src


def test_stays_on_the_active_company_and_its_currency():
    src = _code()
    assert 'env.company.id' in src
    assert "('company_id', '=', _cid)" in src
    assert 'env.company.currency_id' in src


def test_rows_open_their_record():
    src = _code()
    assert "'__model': 'sale.order'" in src
    assert "'__model': 'res.partner'" in src
    assert "'__hide_columns__': ['id']" in src


def test_sheet_takes_no_arguments_and_is_english():
    md = (_SYSTEM / 'sales_board.md').read_text(encoding='utf-8')
    head = md.split('---', 2)[1]
    assert 'skill: sales-board' in head
    assert 'args_policy: none' in head
    assert 'agent_codes: pns_ai_chatboo' in head
