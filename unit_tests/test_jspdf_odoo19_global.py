# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Odoo 19: jsPDF UMD must land on globalThis, not only the AMD graph."""
from __future__ import annotations

from pathlib import Path

_OWL2 = (
    Path(__file__).resolve().parents[1]
    / 'stacks' / 'owl2' / 'pns_ai_chatboo'
)


def test_owl2_jspdf_load_order_forces_global():
    loader = (_OWL2 / 'static' / 'src' / 'js' / 'chatboo_heavy_libs.js').read_text(
        encoding='utf-8',
    )
    pre = '/pns_ai_chatboo/static/src/js/jspdf_umd_pre.js'
    umd = '/pns_ai_chatboo/static/src/js/jspdf.umd.min.js'
    auto = '/pns_ai_chatboo/static/src/js/jspdf.plugin.autotable.min.js'
    post = '/pns_ai_chatboo/static/src/js/jspdf_umd_post.js'
    shim = '/pns_ai_chatboo/static/src/js/jspdf_shim.js'
    for token in (pre, umd, auto, post, shim):
        assert token in loader, token
    assert loader.index(pre) < loader.index(umd) < loader.index(auto)
    assert loader.index(auto) < loader.index(post) < loader.index(shim)
    manifest = (_OWL2 / '__manifest__.py').read_text(encoding='utf-8')
    assert 'jspdf.umd.min.js' not in manifest
    assert 'chart.umd.min.js' not in manifest
    assert 'echarts.min.js' not in manifest

    pre_src = (_OWL2 / 'static' / 'src' / 'js' / 'jspdf_umd_pre.js').read_text(
        encoding='utf-8',
    )
    post_src = (_OWL2 / 'static' / 'src' / 'js' / 'jspdf_umd_post.js').read_text(
        encoding='utf-8',
    )
    assert '@odoo-module ignore' in pre_src
    assert 'g.define = undefined' in pre_src
    assert '@odoo-module ignore' in post_src
    assert '__pnsJspdfSaved' in post_src

    umd_head = (_OWL2 / 'static' / 'src' / 'js' / 'jspdf.umd.min.js').read_text(
        encoding='utf-8',
    )[:80]
    auto_head = (
        _OWL2 / 'static' / 'src' / 'js' / 'jspdf.plugin.autotable.min.js'
    ).read_text(encoding='utf-8')[:80]
    assert umd_head.startswith('/** @odoo-module ignore */')
    assert auto_head.startswith('/** @odoo-module ignore */')


def test_owl2_export_reads_jspdf_from_globalthis():
    src = (_OWL2 / 'static' / 'src' / 'js' / 'chatboo_export.js').read_text(
        encoding='utf-8',
    )
    assert 'function jspdfCtor()' in src
    assert 'g.jspdf' in src
    assert src.count('window.jspdf') == 0
    assert "Error: jsPDF is not available" in src
