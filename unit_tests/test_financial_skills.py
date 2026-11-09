# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The factory financial report reads invoices and journal types, not one
country's chart of accounts, and stays on the active company."""
from pathlib import Path

_SKILL = Path(__file__).resolve().parents[1] / 'common' / 'ai' / 'skills' / 'system'


def test_financial_health_needs_no_chart_of_accounts():
    src = (_SKILL / 'financial_health.py').read_text(encoding='utf-8')
    assert "account_id.code" not in src
    assert "('type', 'in', ['bank', 'cash'])" in src
    assert "('company_id', '=', _cid)" in src


def test_financial_health_is_a_written_report():
    head = (_SKILL / 'financial_health.md').read_text(encoding='utf-8').split('---', 2)[1]
    assert 'compose: compose-model' in head
    src = (_SKILL / 'financial_health.py').read_text(encoding='utf-8')
    assert "'report_outline'" in src
    assert "'closing_required'" in src
