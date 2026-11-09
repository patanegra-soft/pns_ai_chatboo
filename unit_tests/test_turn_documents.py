# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""An attachment's text, kept like the rows of a table and read back by page."""
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / 'common' / 'utils' / 'turn_documents.py'
_spec = importlib.util.spec_from_file_location('turn_documents', _PATH)
docs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(docs)

INVOICE = {'name': 'factura.pdf', 'pages': ['Factura 597970', '', 'Total 9,61 EUR']}


def test_page_three_is_the_third_page_even_after_an_empty_one():
    out = docs.read([INVOICE], 'factura.pdf', page=3)
    assert out == 'factura.pdf, page 3 of 3:\nTotal 9,61 EUR'
    assert '(empty page)' in docs.read([INVOICE], 'factura.pdf', page=2)
    assert docs.read([INVOICE], 'factura.pdf', page=9) == 'factura.pdf has 3 pages.'


def test_find_gives_only_the_pages_that_contain_the_words():
    out = docs.read([INVOICE], 'factura.pdf', find='total')
    assert 'page 3 of 3' in out and 'Factura 597970' not in out
    assert docs.read([INVOICE], 'factura.pdf', find='IBAN') == "No page of factura.pdf contains 'IBAN'."


def test_a_name_is_found_by_case_or_a_unique_piece():
    assert 'page 1 of 3' in docs.read([INVOICE], 'FACTURA.PDF', page=1)
    assert 'page 1 of 3' in docs.read([INVOICE], 'factura', page=1)
    missing = docs.read([INVOICE], 'contrato.pdf')
    assert missing == "No document named 'contrato.pdf'. Documents: factura.pdf."


def test_the_answer_fits_what_the_engine_hands_back_to_the_model():
    long_doc = {'name': 'big.txt', 'pages': ['x' * 50000]}
    assert len(docs.read([long_doc], 'big.txt')) == docs.READ_CHARS


def test_a_new_file_with_the_same_name_replaces_the_old_one():
    newer = {'name': 'factura.pdf', 'pages': ['Factura 600000']}
    kept = docs.merge([INVOICE], [newer])
    assert kept == [newer]


def test_the_oldest_go_first_when_there_are_too_many_or_too_much_text():
    many = [{'name': 'f%d.txt' % i, 'pages': ['text %d' % i]} for i in range(7)]
    kept = docs.merge([], many, kept=5)
    assert [doc['name'] for doc in kept] == ['f2.txt', 'f3.txt', 'f4.txt', 'f5.txt', 'f6.txt']
    heavy = [{'name': 'a', 'pages': ['x' * 60]}, {'name': 'b', 'pages': ['y' * 60]}]
    assert [doc['name'] for doc in docs.merge([], heavy, max_chars=100)] == ['b']


def test_a_file_with_no_text_is_not_kept():
    assert docs.merge([], [{'name': 'blank.pdf', 'pages': ['', '  ']}]) == []


def test_the_note_lists_the_documents_without_their_text():
    note = docs.note([INVOICE])
    assert '- factura.pdf (3 pages)' in note
    assert 'Total 9,61' not in note
    assert "read_document('factura.pdf', page=1)" in note
    assert docs.note([]) == ''


def test_a_photo_kept_as_text_keeps_the_checksum_of_its_file():
    ticket = {'name': 'ticket.jpg', 'pages': ['Total 9,61 EUR'], 'checksum': 'abc123'}
    kept = docs.merge([INVOICE], [ticket])
    assert kept[-1]['checksum'] == 'abc123'
    assert docs.checksums(kept) == {'abc123'}
    assert '- ticket.jpg (1 page)' in docs.note(kept)


def test_the_listing_gives_names_and_page_counts_newest_last():
    ticket = {'name': 'ticket.jpg', 'pages': ['Total 1,00 EUR']}
    assert docs.listing([INVOICE, ticket, 'junk']) == [
        {'name': 'factura.pdf', 'pages': 3},
        {'name': 'ticket.jpg', 'pages': 1},
    ]
    assert docs.listing([]) == []


def test_a_transcription_is_cut_at_its_page_marks():
    text = '=== PAGE 1 ===\nFactura 597970\n=== PAGE 3 ===\nTotal 9,61 EUR'
    assert docs.split_pages(text, 3) == ['Factura 597970', '', 'Total 9,61 EUR']
    assert docs.split_pages('just text', 2) == ['just text']
    assert docs.split_pages('', 2) == []
