# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""What the assistant writes says, to a machine, that an AI system wrote it."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_STACKS = ('owl1', 'owl2')


def _js(stack, name):
    return (
        _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js' / name
    ).read_text(encoding='utf-8')


@pytest.mark.parametrize('stack', _STACKS)
def test_every_pdf_is_marked_before_it_is_saved(stack):
    js = _js(stack, 'chatboo_export.js')
    saves = re.findall(r'(\w+)\.save\(filename\)', js)
    assert saves
    for var in set(saves):
        assert js.count(f'{var}.save(filename)') == js.count(f'markAiPdf({var});\n        {var}.save(filename)')


@pytest.mark.parametrize('stack', _STACKS)
def test_every_pdf_blob_is_marked(stack):
    js = _js(stack, 'chatboo_export.js')
    outputs = re.findall(r"( +)return doc\.output\('blob'\);", js)
    assert outputs
    for indent in outputs:
        assert f"{indent}markAiPdf(doc);\n{indent}return doc.output('blob');" in js


@pytest.mark.parametrize('stack', _STACKS)
@pytest.mark.parametrize('builder', ['wrapWordHtml', 'buildHtmlDocument'])
def test_word_and_html_name_their_generator(stack, builder):
    js = _js(stack, 'chatboo_export.js')
    body = js.split('function ' + builder, 1)[1].split('\n    }\n', 1)[0]
    assert 'name="generator"' in body


def test_assistant_bubble_carries_the_mark():
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    owl1 = _js('owl1', 'chatboo_component_v2.js')
    for src in (owl2, owl1):
        assert "t-att-data-ai-generated=\"msg.role === 'assistant' ? 'true' : undefined\"" in src
