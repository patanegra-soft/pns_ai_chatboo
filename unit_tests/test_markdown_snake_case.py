# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""ChatbooMarkdown keeps mid-word underscores (module/field snake_case)."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_MD = (_ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_markdown.js').read_text(
    encoding='utf-8',
)


def test_formatters_and_export_use_chatboo_markdown():
    for stack in ('owl1', 'owl2'):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
        formatters = (base / 'chatboo_formatters.js').read_text(encoding='utf-8')
        export = (base / 'chatboo_export.js').read_text(encoding='utf-8')
        assert 'showdown' not in formatters, stack
        assert 'showdown' not in export, stack
        assert formatters.count('ChatbooMarkdown.toHtml') == 1, stack
        assert export.count('ChatbooMarkdown.toHtml') == 2, stack


def test_converter_keeps_midword_underscores():
    assert "c === '_' && !isWord(text.charAt(i - 1))" in _MD
    assert 'function isWord' in _MD
    assert not (_ROOT / 'common' / 'static' / 'src' / 'js' / 'showdown.js').exists()
