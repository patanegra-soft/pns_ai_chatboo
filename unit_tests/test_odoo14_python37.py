# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Odoo 14 runs on Python 3.7: what the newer interpreters accept and 3.7 does not."""
from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SHIPPED = [
    p for p in sorted((ROOT / 'common').rglob('*.py')) + sorted((ROOT / 'stacks').rglob('*.py'))
    if '__pycache__' not in p.parts
]


def _old_node(kind, **fields):
    """A node class as Python 3.7 builds it: Str(s), Index(value)."""
    cls = type(kind, (ast.AST,), {'_fields': tuple(fields)})
    node = cls()
    for key, value in fields.items():
        setattr(node, key, value)
    return node


@pytest.mark.parametrize('path', _SHIPPED, ids=lambda p: str(p.relative_to(ROOT)))
def test_parses_as_python37(path):
    ast.parse(path.read_text(encoding='utf-8'), str(path), feature_version=(3, 7))


@pytest.mark.parametrize('path', _SHIPPED, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_literal_check_against_constant_alone(path):
    """``isinstance(node, ast.Constant)`` is False for every literal on 3.7."""
    src = path.read_text(encoding='utf-8')
    assert not re.search(r',\s*ast\.Constant\s*\)', src)


@pytest.mark.parametrize('path', _SHIPPED, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_37_literal_class_by_attribute(path):
    """``ast.Str`` / ``ast.Num``… are gone in 3.14; tell them apart by type name."""
    src = path.read_text(encoding='utf-8')
    assert not re.search(r'\bast\.(Str|Num|Bytes|NameConstant)\b', src)


def test_model_name_read_from_a_37_subscript():
    path = ROOT / 'common' / 'utils' / 'skill_capture_compose.py'
    spec = importlib.util.spec_from_file_location('skill_capture_compose_37', path)
    compose = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compose)
    index = _old_node('Index', value=ast.Constant(value='res.partner'))
    assert compose._static_str(index) == 'res.partner'
    assert compose._static_str(ast.Constant(value='res.partner')) == 'res.partner'
    assert compose._static_str(ast.Name(id='x', ctx=ast.Load())) is None
