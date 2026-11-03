# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Assistant HTML cannot run code or call out when Chatboo paints it."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_STACKS = ('owl1', 'owl2')


def _js(stack: str, name: str) -> str:
    path = _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js' / name
    return path.read_text(encoding='utf-8')


def _all_js(stack: str) -> dict:
    base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
    return {
        p.name: p.read_text(encoding='utf-8')
        for p in base.glob('chatboo_*.js')
    }


def _jsdom_available() -> bool:
    node = shutil.which('node')
    if not node:
        return False
    probe = subprocess.run(
        [node, '-e', "require.resolve('jsdom')"],
        capture_output=True, cwd=str(_ROOT / 'unit_tests'),
    )
    return probe.returncode == 0


@pytest.mark.skipif(not _jsdom_available(), reason='node + jsdom not installed')
def test_assistant_html_cannot_run_code_or_call_out():
    out = subprocess.run(
        [shutil.which('node'), str(_ROOT / 'unit_tests' / 'sanitize_html_corpus.js'), str(_ROOT)],
        capture_output=True, text=True, encoding='utf-8', check=True,
        cwd=str(_ROOT / 'unit_tests'),
    )
    failures = json.loads(out.stdout)
    assert failures == [], json.dumps(failures, indent=2, ensure_ascii=False)


def test_owl1_paints_message_html_only_through_the_sanitizer():
    src = _js('owl1', 'chatboo_component_v2.js')
    sinks = re.findall(r't-raw="([^"]+)"', src)
    assert sinks, 'owl1 template no longer paints message HTML'
    assert all(s.startswith('_safeHtml(') for s in sinks), sinks


def test_owl2_paints_message_html_only_through_the_sanitizer():
    src = _js('owl2', 'chatboo_app.js')
    assert 'this.root.el.innerHTML = html;' not in src
    for call in re.findall(r'markup\(([^;]*)\);', src):
        assert call.startswith(('sharedFormatContent(', 'sharedFormatMarkdown(', 'sanitizeHtml(')), call


def test_message_text_is_never_read_by_parsing_in_the_live_page():
    raw_parse = re.compile(
        r'innerHTML\s*=\s*(?:String\()?(?:msg|userMsg|m)\.(?:content|raw|htmlSrc)'
        r'|innerHTML\s*=\s*String\(raw\)'
        r'|innerHTML\s*=\s*(?:text|s);'
    )
    for stack in _STACKS:
        for name, src in _all_js(stack).items():
            assert not raw_parse.search(src), (stack, name, raw_parse.search(src).group(0))


def test_formatters_never_parse_html_in_the_live_page():
    for stack in _STACKS:
        src = _js(stack, 'chatboo_formatters.js')
        live = re.findall(r"document\.createElement\('div'\);\s*\n\s*(\w+)\.innerHTML\s*=", src)
        assert live == [], (stack, live)
