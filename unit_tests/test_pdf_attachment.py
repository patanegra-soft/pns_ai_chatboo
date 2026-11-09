# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""A PDF in the clip: its printed text, or its scan read by this agent's own vision."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_JOB = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(encoding='utf-8')
_SESSION = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(encoding='utf-8')


def _body(source, name):
    return source.split('def %s' % name)[1].split('\n    def ')[0]


def test_the_pdf_is_read_with_pns_base_not_another_agent():
    assert 'ocr.service' not in _JOB
    assert 'pns_ocr' not in _JOB
    assert 'is_pdf, pdf_page_texts, pdf_pictures,' in _body(_JOB, '_pdf_reading')
    for stack in ('owl1', 'owl2'):
        manifest = (_ROOT / 'stacks' / stack / 'pns_ai_chatboo' / '__manifest__.py').read_text(encoding='utf-8')
        assert 'ocr' not in manifest.lower()


def test_a_scan_is_transcribed_once_by_chatboo_own_vision_chain():
    body = _body(_JOB, '_transcribe_pages')
    assert 'self.agent_code or CHATBOO_AGENT_CODE' in body
    assert 'images=pictures' in body
    assert 'turn_documents.split_pages(content, len(pictures))' in body


def test_without_a_transcription_the_scan_still_goes_with_the_turn_pictures():
    assert 'return (pages, []) if pages else ([], pictures)' in _body(_JOB, '_pdf_reading')
    assert 'images = images + pdf_pages' in _JOB


def test_the_text_stays_on_the_session_and_later_turns_get_a_note():
    assert 'self.session_id.remember_documents(turn_docs)' in _JOB
    assert 'turn_documents.note(earlier)' in _JOB
    assert '_sandbox_helper_provider = True' in _SESSION
    helpers = _SESSION.split('def sandbox_helpers', 1)[1].split('\n    def ', 1)[0]
    assert "'read_document': read_document" in helpers


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


def test_only_the_owner_of_the_session_reads_its_documents():
    body = _body(_SESSION, '_documents_of_this_turn')
    assert "self.env.context.get('ai_session_ref')" in body
    assert 'session.user_id.id != self.env.uid' in body
    for helper in ('_read_document(', '_documents('):
        assert 'self._documents_of_this_turn()' in _body(_SESSION, helper)


def test_a_skill_slash_does_not_get_the_file_text_as_arguments():
    body = _body(_JOB, '_process')
    assert 'if turn_docs and self._prompt_runs_a_skill():' in body
