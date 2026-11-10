# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""A file's text for the model: a PDF in the clip or an attachment of a record.

Printed text, or a scan read by this agent's own vision. One reading
(``document_reading``) serves both ways in.
"""
import base64
import importlib
import sys
import types
from pathlib import Path

from _engine_params import install as install_engine_params

_ROOT = Path(__file__).resolve().parents[1]
_UTILS = _ROOT / 'common' / 'utils'
_JOB = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')
_READING = (_UTILS / 'document_reading.py').read_text(encoding='utf-8')
_CONTEXT = (
    _ROOT / 'common' / 'ai' / 'contexts' / 'domain' / 'record_attachments'
    / 'record_attachments.xml'
).read_text(encoding='utf-8')


def _body(source, name):
    return source.split('def %s' % name)[1].split('\n    def ')[0]


def _reading():
    """``document_reading`` loaded as part of its package, pns_base stubbed."""
    install_engine_params()
    pkg = sys.modules.get('_chatboo_utils')
    if pkg is None:
        pkg = types.ModuleType('_chatboo_utils')
        pkg.__path__ = [str(_UTILS)]
        sys.modules['_chatboo_utils'] = pkg
    return importlib.import_module('_chatboo_utils.document_reading')


class _PdfIo:
    """pns_base's pdf_io as the test needs it: a printed PDF or a scan."""

    def __init__(self, texts=None, pictures=None):
        self.texts = texts or []
        self.pictures = pictures or []

    def is_pdf(self, raw):
        return raw[:5] == b'%PDF-'

    def pdf_page_texts(self, raw, pages=None):
        return list(self.texts)

    def pdf_pictures(self, raw, pages=None):
        return list(self.pictures)


def _install_pdf_io(fake):
    for name in ('odoo', 'odoo.addons', 'odoo.addons.pns_base', 'odoo.addons.pns_base.utils'):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules['odoo.addons.pns_base.utils.pdf_io'] = fake


class _Agents:
    def resolve_inference_agent_code(self, code):
        return code


class _Engine:
    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def sudo(self):
        return self

    def _chat_completion(self, code, messages, **kwargs):
        self.calls.append((code, kwargs.get('images')))
        return {'choices': [{'message': {'content': self.answer}}]}


def _env(answer):
    engine = _Engine(answer)
    return {'ai.agent': _Agents(), 'ai.execution.engine': engine}, engine


def test_the_pdf_is_read_with_pns_base_not_another_agent():
    assert 'ocr.service' not in _READING and 'ocr.service' not in _JOB
    assert 'pns_ocr' not in _READING and 'pns_ocr' not in _JOB
    assert 'is_pdf, pdf_page_texts, pdf_pictures,' in _READING.split('def pdf_reading')[1]
    for stack in ('owl1', 'owl2', 'owl3'):
        manifest = (_ROOT / 'stacks' / stack / 'pns_ai_chatboo' / '__manifest__.py').read_text(encoding='utf-8')
        assert 'ocr' not in manifest.lower()


def test_a_printed_pdf_gives_its_pages_without_a_vision_call():
    reading = _reading()
    _install_pdf_io(_PdfIo(texts=['Invoice 1001', 'Total 9.61']))
    env, engine = _env('')
    assert reading.pdf_reading(env, b'%PDF-1.4 x') == (['Invoice 1001', 'Total 9.61'], [])
    assert reading.pdf_reading(env, b'PK not a pdf') is None
    assert engine.calls == []


def test_a_scan_is_transcribed_once_by_the_agent_own_vision_chain():
    reading = _reading()
    _install_pdf_io(_PdfIo(pictures=[b'jpeg-1', b'jpeg-2']))
    env, engine = _env('=== PAGE 1 ===\nACME ticket\n=== PAGE 2 ===\nTotal 9.61')
    pages, pictures = reading.pdf_reading(env, b'%PDF-1.4 scan', agent_code='pns_ai_chatboo')
    assert pages == ['ACME ticket', 'Total 9.61'] and pictures == []
    assert len(engine.calls) == 1 and engine.calls[0][0] == 'pns_ai_chatboo'
    assert engine.calls[0][1] == [
        'data:image/jpeg;base64,' + base64.b64encode(b'jpeg-1').decode(),
        'data:image/jpeg;base64,' + base64.b64encode(b'jpeg-2').decode(),
    ]


def test_without_a_transcription_the_scan_still_goes_with_the_turn_pictures():
    reading = _reading()
    _install_pdf_io(_PdfIo(pictures=[b'jpeg-1']))
    env, _engine = _env('')
    pages, pictures = reading.pdf_reading(env, b'%PDF-1.4 scan')
    assert pages == [] and len(pictures) == 1
    assert 'images = images + pdf_pages' in _JOB
    assert 'document_reading.pdf_reading(' in _body(_JOB, '_pdf_reading')
    assert 'self.agent_code or CHATBOO_AGENT_CODE' in _body(_JOB, '_transcribe_pages')


def test_file_pages_reads_a_picture_a_pdf_or_a_data_file():
    reading = _reading()
    _install_pdf_io(_PdfIo(texts=['Printed page']))
    env, engine = _env('Photo of a letter')
    assert reading.file_pages(env, 'a.pdf', 'application/pdf', b'%PDF-1.4') == ['Printed page']
    assert reading.file_pages(env, 'a.jpg', 'image/jpeg', b'\xff\xd8 bytes') == ['Photo of a letter']
    assert reading.file_pages(env, 'a.txt', 'text/plain', b'hello world') == ['hello world']
    assert reading.file_pages(env, 'a.pdf', 'application/pdf', b'') == []
    # Only the vision rasters go to the vision chain; an SVG is plain text.
    assert len(engine.calls) == 1
    env, _engine = _env(reading.NO_TEXT)
    assert reading.file_pages(env, 'cat.png', 'image/png', b'\x89PNG') == []


def test_the_text_stays_on_the_session_and_later_turns_get_a_note():
    assert 'self.session_id.remember_documents(turn_docs)' in _JOB
    assert 'turn_documents.note(earlier)' in _JOB
    assert '_sandbox_helper_provider = True' in _SESSION
    helpers = _SESSION.split('def sandbox_helpers', 1)[1].split('\n    def ', 1)[0]
    assert "'read_document': read_document" in helpers
    assert "'read_attachment': read_attachment" in helpers


def test_an_attachment_of_a_record_is_read_as_the_user_and_kept_on_the_session():
    body = _body(_SESSION, '_read_attachment')
    # Odoo's own attachment check, as the asking user: no sudo on the file.
    assert "self.env['ir.attachment'].with_user(self.env.uid)" in body
    assert 'self._check_attachment_read(att)' in body
    assert '.sudo()' not in body
    # Same reading as the clip, kept once by checksum, written on its own cursor.
    assert 'document_reading.file_pages(' in _body(_SESSION, '_attachment_pages')
    assert 'self._kept_attachment(documents, checksum)' in body
    assert 'session._store_documents([kept])' in body
    assert 'session.remember_documents(documents)' in _body(_SESSION, '_store_documents')
    assert 'new_cr.commit()' in _body(_SESSION, '_store_documents')
    # A sentence, never an exception, when there is nothing to read.
    assert 'except AccessError:' in body
    assert 'has no text that could be read' in body
    # The model is told the helper exists.
    assert 'read_attachment(' in _CONTEXT
    assert 'read_attachment' in (
        _ROOT / 'common' / 'ai' / 'contexts' / 'domain' / 'self_chatboo' / 'self_chatboo.xml'
    ).read_text(encoding='utf-8')


def test_a_skill_slash_gets_its_own_words_without_the_note():
    assert 'if documents_note and not self._prompt_runs_a_skill():' in _JOB
    body = _body(_JOB, '_prompt_runs_a_skill')
    assert 'parse_slash_command(self.prompt)' in body
    assert 'self._command_resolves_skill(parsed[0])' in body


def test_a_photo_of_a_document_is_kept_as_text_and_not_sent_again():
    body = _body(_JOB, '_image_documents')
    assert 'self._transcribe_pages([shot[2] for shot in shots], photos=True)' in body
    assert 'text == NO_TEXT or not usable(text)' in body
    assert "'checksum': hashlib.sha1(raw).hexdigest()" in body
    assert 'turn_docs = turn_docs + self._image_documents()' in _JOB
    recall = _body(_JOB, '_recall_prior_images')
    assert 'seen = turn_documents.checksums(self.session_id.get_documents())' in recall


def test_the_photo_keeps_the_same_name_as_its_attachment():
    assert 'att_name = self._image_name(idx, mimetype, names)' in _body(_JOB, '_persist_turn_images')


def test_pictures_are_prepared_by_pns_base():
    assert 'shrink_picture(raw, cls._RECALL_MAX_SIDE)' in _body(_JOB, '_downscale_image_to_data_url')
    assert 'from PIL' not in _JOB
    assert 'from PIL' not in _READING


def test_only_the_owner_of_the_session_reads_its_documents():
    body = _body(_SESSION, '_session_of_this_turn')
    assert "self.env.context.get('ai_session_ref')" in body
    assert 'session.user_id.id != self.env.uid' in body
    for helper in ('_documents_of_this_turn(', '_read_attachment('):
        assert 'self._session_of_this_turn()' in _body(_SESSION, helper)
    for helper in ('_read_document(', '_documents('):
        assert 'self._documents_of_this_turn()' in _body(_SESSION, helper)


def test_a_skill_slash_does_not_get_the_file_text_as_arguments():
    body = _body(_JOB, '_process')
    assert 'if turn_docs and self._prompt_runs_a_skill():' in body
