# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Odoo 20+ runs stacks/owl3: the owl2 module, with the screen written for Owl 3."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The module name is the folder inside stacks/owl2, not the clone's folder:
# publish.sh runs these tests on a copy of the tree under another name.
MODULE = next(
    p.name for p in sorted((ROOT / 'stacks' / 'owl2').iterdir())
    if p.is_dir() and (p / '__manifest__.py').is_file()
)
OWL2 = ROOT / 'stacks' / 'owl2' / MODULE
OWL3 = ROOT / 'stacks' / 'owl3' / MODULE


def test_both_stacks_exist():
    # Without this, a wrong path makes every other test here pass on empty sets.
    assert (OWL2 / '__manifest__.py').is_file()
    assert (OWL3 / '__manifest__.py').is_file()


def _files(base):
    return {
        p.relative_to(base).as_posix()
        for p in base.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts
    }


def test_owl3_has_the_same_files_as_owl2():
    assert _files(OWL3) == _files(OWL2)


def test_only_the_screen_differs_from_owl2():
    for rel in sorted(_files(OWL2)):
        if rel.startswith('static/src/'):
            continue
        assert (OWL2 / rel).read_bytes() == (OWL3 / rel).read_bytes(), rel


def _owl3_js():
    for path in sorted((OWL3 / 'static' / 'src').rglob('*.js')):
        yield path.relative_to(OWL3).as_posix(), path.read_text(encoding='utf-8')


def test_owl3_has_no_static_props():
    for rel, text in _owl3_js():
        assert not re.search(r'static\s+(props|defaultProps)\s*=', text), rel


def test_owl3_imports_nothing_owl3_dropped():
    gone = ('useState', 'useRef', 'useExternalListener', 'useComponent', 'useChildSubEnv')
    for rel, text in _owl3_js():
        for block in re.findall(r'import\s*\{([^}]*)\}\s*from\s*"@odoo/owl"', text):
            names = {n.strip() for n in block.split(',')}
            assert not names & set(gone), (rel, names & set(gone))


def _owl3_templates():
    for path in sorted((OWL3 / 'static' / 'src').rglob('*')):
        if path.suffix in ('.xml', '.js'):
            yield path.name, path.read_text(encoding='utf-8')


def test_owl3_templates_use_t_out():
    for name, text in _owl3_templates():
        assert 't-esc=' not in text, name


def test_owl3_refs_are_signals_on_the_component():
    for name, text in _owl3_templates():
        for ref in re.findall(r't-ref="([^"]*)"', text):
            assert ref.startswith('this.'), (name, ref)
