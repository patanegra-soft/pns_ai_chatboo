# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""PNS-60 (part): escaped text also lands inside HTML attributes.

A slash command whose name carries quotes used to break out of
data-slash-code because escapeHtml left the quotes alone. Both formatter
copies escape them now.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_escape_html_escapes_quotes_in_both_stacks():
    for stack in ('owl1', 'owl2'):
        src = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'static' / 'src'
            / 'js' / 'chatboo_formatters.js'
        ).read_text(encoding='utf-8')
        assert ".replace(/\"/g, '&quot;')" in src
        assert ".replace(/'/g, '&#39;')" in src
