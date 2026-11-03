# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""An HTML table written inside a paragraph is lifted before Markdown."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

_JS = Path(__file__).resolve().parents[1] / 'common' / 'static' / 'src' / 'js' / 'chatboo_sse.js'


def _prepare(md: str) -> str:
    script = r'''
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync(process.env.SSE_JS, 'utf8');
const sandbox = { console };
sandbox.globalThis = sandbox;
vm.runInNewContext(src, sandbox);
const out = sandbox.ChatbooSse.prepareMarkdownForDisplay(process.env.SSE_MD);
process.stdout.write(out.markdown);
'''
    proc = subprocess.run(
        ['node', '-e', script],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, 'SSE_JS': str(_JS), 'SSE_MD': md},
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_table_inside_a_paragraph_starts_on_its_own_line():
    raw = (
        'Analysis\n\n'
        'The year was fine. <table class="x" onclick="alert(1)">'
        '<tr><td>Base neta</td><td>1</td></tr></table> More text.'
    )
    out = _prepare(raw)
    assert '\n\n<table class="table table-sm table-striped">' in out
    assert 'onclick' not in out
    assert 'alert' not in out
    assert '<td>Base neta</td>' in out
    assert 'More text.' in out


def test_on_screen_stub_is_not_shown():
    raw = (
        'Here is the forecast.\n\n'
        '[On-screen artifact | kind=table | 7 rows × 8 columns | '
        'columns: Día, Semana]\n\n'
        'Have a good week.'
    )
    out = _prepare(raw)
    assert 'On-screen artifact' not in out
    assert 'Here is the forecast.' in out
    assert 'Have a good week.' in out
