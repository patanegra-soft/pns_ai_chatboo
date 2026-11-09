# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""/bill-draft reads the attachment and proposes a form; it never writes."""
from __future__ import annotations

from pathlib import Path

_SRC = (
    Path(__file__).resolve().parents[1] / 'common' / 'ai' / 'skills' / 'system' / 'bill_draft.py'
).read_text(encoding='utf-8')

_BILL = (
    'ACME Supplies\n'
    'Tax id: ES-B12.345.674\n'
    'Invoice 2026-A-17 of 10/03/2026\n'
    'Phone 600 123 456\n'
    'Base 1 020,25\n'
    'TOTAL 1 234,50 EUR\n'
)


class _Records(list):
    id = 0

    def __bool__(self):
        return len(self) > 0


class _Partner:
    def __init__(self, ids=()):
        self.ids = list(ids)
        self.id = self.ids[0] if self.ids else False
        self.display_name = 'ACME Supplies'

    def __bool__(self):
        return bool(self.ids)

    def search_read(self, domain, fields):
        return [{'id': 1, 'vat': 'ESB12345674'}, {'id': 2, 'vat': 'ESA99999999'}]

    def fields_get(self, names):
        return {}

    def browse(self, ids):
        return _Partner(ids)


class _Lang:
    date_format = '%d/%m/%Y'

    def search(self, domain, limit=None):
        return self


class _Moves:
    def search(self, domain, limit=None, order=None):
        return []

    def fields_get(self, names):
        return {'state': {'selection': [('draft', 'Draft')]}}


class _Company:
    vat = 'ESB00000000'


class _Env(dict):
    company = [_Company()]

    class user:
        lang = 'es_ES'

    def __init__(self):
        super().__init__({'res.partner': _Partner(), 'res.lang': _Lang(), 'account.move': _Moves()})


def _run(docs, text=_BILL, **extra):
    scope = {
        'env': _Env(),
        'documents': lambda: docs,
        'read_document': lambda name, page=None, find=None: text,
        'format_amount': lambda value, decimals=2: '%.2f' % value,
    }
    scope.update(extra)
    exec(compile(_SRC, '<bill_draft>', 'exec'), scope, scope)
    return scope['result']


def test_the_card_opens_the_vendor_bill_form_with_vendor_and_date():
    result = _run([{'name': 'old.pdf', 'pages': 1}, {'name': 'bill.pdf', 'pages': 1}])
    card = result['card']
    assert card['kind'] == 'form'
    assert card['action'] == 'account.action_move_in_invoice_type'
    assert card['title'] == 'Vendor bill from bill.pdf'
    assert card['values'] == {'partner_id': 1, 'invoice_date': '2026-03-10'}
    assert 'Largest amount in the document: 1234.50 (check it against the total)' in card['lines']
    assert 'propose_steps' not in result


def test_a_named_attachment_wins_over_the_newest():
    result = _run([{'name': 'bill.pdf', 'pages': 1}, {'name': 'other.pdf', 'pages': 1}], document='bill')
    assert result['card']['title'] == 'Vendor bill from bill.pdf'


def test_no_attachment_says_how_to_attach_one():
    result = _run([])
    assert 'Attach the supplier bill' in result['formatted_text']
    assert 'card' not in result


def test_a_month_first_language_reads_the_date_the_other_way():
    _Lang.date_format = '%m/%d/%Y'
    try:
        result = _run([{'name': 'bill.pdf', 'pages': 1}])
    finally:
        _Lang.date_format = '%d/%m/%Y'
    assert result['card']['values']['invoice_date'] == '2026-10-03'


def test_an_unknown_tax_id_leaves_the_vendor_empty():
    result = _run([{'name': 'bill.pdf', 'pages': 1}], text='Tax id: X0000000Z\nTOTAL 5,00')
    assert 'partner_id' not in result['card']['values']
    assert result['card']['lines'][0].startswith('Vendor: not found')
