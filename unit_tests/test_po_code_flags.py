# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Odoo 16+ only loads a code term whose entry says odoo-python / odoo-javascript."""
import re
from pathlib import Path

PO = Path(__file__).resolve().parents[1] / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'i18n' / 'es_ES.po'


def test_owl2_code_terms_carry_the_loader_flag():
    po = PO.read_text(encoding='utf-8').replace('\r\n', '\n')
    missing = []
    for block in po.split('\n\n'):
        lines = block.split('\n')
        need = []
        if any(re.match(r'#: code:\S+\.py', l) for l in lines):
            need.append('#. odoo-python')
        if any(re.match(r'#: code:\S+\.(js|xml)', l) for l in lines):
            need.append('#. odoo-javascript')
        if any(flag not in lines for flag in need) or '#. openerp-web' in lines:
            missing.append(next(l for l in lines if l.startswith('msgid')))
    assert not missing, missing
