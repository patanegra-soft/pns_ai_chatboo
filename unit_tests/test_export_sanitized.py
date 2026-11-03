# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Export and chart stats never hand raw HTML to innerHTML."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from _deployed import deployed

_ROOT = Path(__file__).resolve().parents[1]
_JS = Path('pns_ai_chatboo') / 'static' / 'src' / 'js'
_SANITIZER = {'owl1': 'formatters.sanitizeHtml(', 'owl2': 'sanitizeHtml('}


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_every_export_innerhtml_goes_through_the_sanitizer(stack):
    src = (_ROOT / 'stacks' / stack / _JS / 'chatboo_export.js').read_text(encoding='utf-8')
    sites = re.findall(r'\.innerHTML = (.+);', src)
    assert sites
    raw = [s for s in sites if not s.startswith(_SANITIZER[stack])]
    assert raw == []


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_markdown_to_html_returns_sanitized_html(stack):
    src = (_ROOT / 'stacks' / stack / _JS / 'chatboo_export.js').read_text(encoding='utf-8')
    body = src.split('function markdownToHTML(markdown)', 1)[1].split('\n    }\n', 1)[0]
    returns = re.findall(r'return (.+);', body)
    assert returns
    assert all(r == "''" or r.startswith(_SANITIZER[stack]) for r in returns)


@pytest.mark.parametrize('stack', ['owl1', 'owl2'])
def test_stats_table_escapes_the_series_name(stack):
    src = deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js').read_text(
        encoding='utf-8',
    )
    assert 'escapeText(model[i].name' in src
    assert 'String(model[i].name' not in src
