# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Factory financial skills: the closing reads the table, the balance
stops at the period, and the collection date is the payment."""
from datetime import date
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[1]
_SKILLS = _ROOT / 'common' / 'ai' / 'skills' / 'system'


def _slice(path, start_mark, end_mark):
    src = path.read_text(encoding='utf-8')
    start = src.index(start_mark)
    end = src.index(end_mark, start)
    ns = {}
    exec(src[start:end], ns)  # noqa: S102 — pure helpers, no Odoo
    return ns


def test_closing_reads_the_metric_column():
    ns = _slice(
        _SKILLS / 'financial_health.py',
        '_LEDGER_GROUPS = (',
        '\ndef financial_situation_report',
    )
    label = ns['_row_label']
    assert label({'Metric': 'Overdue AR', 'Value': 40000}) == 'Overdue AR'
    assert label({'Indicator': 'Cartera vencida'}) == 'Cartera vencida'
    assert ns['_ledger_group']('572000') == ('57',)
    assert ns['_ledger_group']('430000') == ('430', '431', '432')
    assert ns['_ledger_group']('600000') is None
    src = (_SKILLS / 'financial_health.py').read_text(encoding='utf-8')
    assert "('date', '<=', str(end_d))" in src
    assert "('company_id', '=', cid)" in src
    assert 'def bal_prefix' not in src
    assert src.count("account.move.line'].search(domain)") == 1


def test_collection_date_is_the_counterpart():
    ns = {}
    src = (_SKILLS / 'customer_risk_analysis.py').read_text(encoding='utf-8')
    start = src.index('def payment_dates_of_line')
    end = src.index('\ntoday = date.today()', start)
    exec(src[start:end], ns)  # noqa: S102
    fn = ns['payment_dates_of_line']
    invoice_line = SimpleNamespace(
        id=1,
        date=date(2026, 1, 1),
        matched_credit_ids=[SimpleNamespace(
            credit_move_id=SimpleNamespace(id=9, date=date(2026, 3, 15)),
        )],
        matched_debit_ids=[],
    )
    assert fn(invoice_line) == [date(2026, 3, 15)]
    body = src[end:]
    assert 'pay_lines.date' not in body
    assert 'invoice_date_due si está pagada' not in body
