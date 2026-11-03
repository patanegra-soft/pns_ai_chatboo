# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Odoo 14 reads every catalog entry's module from its ``#. module:`` line.

An entry without it stops the registry from loading, not just that msgid.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_CATALOGS = sorted(_ROOT.glob('stacks/*/pns_ai_chatboo/i18n/*.po'))
_MODULE_LINE = re.compile(r'^#\. modules?: \w+', re.M)


def _entries(path):
    text = re.sub(r'\r+\n', '\n', path.read_text(encoding='utf-8'))
    return [b for b in text.split('\n\n') if re.search(r'^msgid "', b, re.M)]


@pytest.mark.parametrize('path', _CATALOGS, ids=lambda p: p.parent.parent.parent.name)
def test_every_entry_names_its_module(path):
    entries = _entries(path)[1:]
    assert entries
    missing = [e.splitlines()[-2] for e in entries if not _MODULE_LINE.search(e)]
    assert not missing, missing
