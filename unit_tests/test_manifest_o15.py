# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Odoo 15 runs the owl1 module with ``__manifest_o15__.py``.

Odoo 15 has Owl 1 and the old views, like 14, but it reads the assets from
the manifest and has no ``web.assets_backend`` template to inherit. The two
manifests differ only there. A ``*_o14.js`` hook needs a piece Odoo 15 does
not have (old ActionManager / WebClient); its ``*_o15.js`` pair loads instead.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWL1 = next(p for p in (ROOT / 'stacks' / 'owl1').iterdir()
            if (p / '__manifest__.py').is_file())
MODULE = OWL1.name

# Old web modules that Odoo 14 has and Odoo 15 does not.
_GONE_IN_15 = ('web.ActionManager', 'web.Notification', 'web.WebClient')


def _manifest(name):
    return ast.literal_eval((OWL1 / name).read_text(encoding='utf-8'))


def _backend_from_assets_xml():
    xml = (OWL1 / 'views' / 'assets.xml').read_text(encoding='utf-8')
    paths = []
    for body in re.findall(
            r'<template[^>]*inherit_id="web\.assets_backend"[^>]*>(.*?)</template>', xml, re.S):
        paths += [m[1:] for m in re.findall(r'\s(?:src|href)="(/[^"]+)"', body)]
    return paths


def test_o15_manifest_matches_14_except_assets():
    m14 = _manifest('__manifest__.py')
    m15 = _manifest('__manifest_o15__.py')
    assert 'views/assets.xml' in m14['data']
    assert 'views/assets.xml' not in m15['data']
    assert 'qweb' not in m15
    assert 'assets' not in m14
    rest14 = {k: v for k, v in m14.items() if k != 'qweb'}
    rest14['data'] = [f for f in m14['data'] if f != 'views/assets.xml']
    rest15 = {k: v for k, v in m15.items() if k != 'assets'}
    assert rest15 == rest14


def test_o15_assets_are_assets_xml_without_o14_hooks():
    m14 = _manifest('__manifest__.py')
    assets = _manifest('__manifest_o15__.py')['assets']
    js = OWL1 / 'static' / 'src' / 'js'
    o15 = ['%s/static/src/js/%s' % (MODULE, p.name) for p in sorted(js.glob('*_o15.js'))]
    want = [p for p in _backend_from_assets_xml() if not p.endswith('_o14.js')] + o15
    assert assets['web.assets_backend'] == want
    qweb = ['%s/%s' % (MODULE, p) for p in m14.get('qweb', [])]
    assert assets.get('web.assets_qweb', []) == qweb


def test_o15_loads_no_old_web_module_it_lacks():
    for path in _manifest('__manifest_o15__.py')['assets']['web.assets_backend']:
        rel = path.split('/', 1)[1]
        src = OWL1 / rel
        if not src.is_file():
            src = ROOT / 'common' / rel
        assert src.is_file(), path
        if not path.endswith('.js'):
            continue
        text = src.read_text(encoding='utf-8')
        for name in _GONE_IN_15:
            assert "require('%s')" % name not in text, (path, name)
            assert 'from "%s"' % name not in text, (path, name)
