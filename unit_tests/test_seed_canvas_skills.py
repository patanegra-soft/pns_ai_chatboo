# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Seed page skills bring their own page and the server fills it each run."""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SKILLS = _ROOT / 'common' / 'ai' / 'skills' / 'system'
_PAGE_SKILLS = sorted(
    path.stem for path in _SKILLS.glob('*.py')
    if '_page_template' in path.read_text(encoding='utf-8')
)


def _canvas():
    odoo = types.ModuleType('odoo')
    odoo._ = lambda text: text
    sys.modules.setdefault('odoo', odoo)
    spec = importlib.util.spec_from_file_location(
        'chatboo_canvas_seed_pages',
        _ROOT / 'common' / 'models' / 'chatboo_canvas.py',
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _assigned(src, name):
    for node in ast.walk(ast.parse(src)):
        if (
            isinstance(node, ast.Assign)
            and any(getattr(t, 'id', '') == name for t in node.targets)
            and isinstance(node.value, ast.Constant)
        ):
            return node.value.value
    return None


def _block_titles(src):
    """Titles the Code gives its blocks: ``_T_* = '...'``."""
    titles = []
    for node in ast.parse(src).body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and getattr(node.targets[0], 'id', '').startswith('_T_')
            and isinstance(node.value, ast.Constant)
        ):
            titles.append(node.value.value)
    return titles


def test_there_are_seed_page_skills():
    assert {'pipeline', 'customer_360'} <= set(_PAGE_SKILLS)


@pytest.mark.parametrize('stem', _PAGE_SKILLS)
def test_page_skill_has_its_card(stem):
    md = (_SKILLS / (stem + '.md')).read_text(encoding='utf-8')
    head = md.split('---', 2)[1]
    assert 'agent_codes: pns_ai_chatboo' in head
    assert 'args_policy:' in head
    schema = [line for line in head.splitlines() if line.startswith('param_schema:')]
    assert schema and json.loads(schema[0].split(':', 1)[1])


@pytest.mark.parametrize('stem', _PAGE_SKILLS)
def test_page_skill_fills_its_template(stem):
    src = (_SKILLS / (stem + '.py')).read_text(encoding='utf-8')
    html = _assigned(src, '_page_template')
    assert html and 'const DATA = ' in html and 'const TITLE = ' in html
    assert 'id="pns-page-rows"' in html
    assert 'page_html(_page_template, _blocks, _page_title)' in src
    assert 'except NameError' in src.split('page_html(_page_template', 1)[1][:200]
    assert '<script src=' not in html and '<link ' not in html

    mod = _canvas()
    assert mod.has_night_theme(html), stem
    assert 'prefers-color-scheme' not in html, stem
    titles = _block_titles(src)
    for title in titles:
        assert "'" + title + "'" in html, (stem, title)
    blocks = [
        {'title': title, 'data': [{'Label': 'ROW-%s-%d' % (stem, i), 'Value': i}]}
        for i, title in enumerate(titles)
    ]
    out = mod.place_rows_on_page(
        html, mod._blocks_for_page(blocks), captured=True, title='Seed page',
    )
    data = mod._const_data_value(out)
    assert [b['title'] for b in data] == titles
    assert 'const TITLE = "Seed page"' in out
    assert '<section id="pns-page-rows" hidden' in out
    assert 'pns-page-rows-watch' in out
