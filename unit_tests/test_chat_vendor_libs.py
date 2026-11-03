# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Vendor chart/PDF libs load when the chat opens; Chart is a local ref."""
from pathlib import Path
from _deployed import deployed

_ROOT = Path(__file__).resolve().parents[1]
_VENDORS = (
    'jspdf.umd.min.js',
    'html2canvas.min.js',
    'chart.umd.min.js',
    'echarts.min.js',
)


def test_vendor_libs_are_not_in_backend_assets():
    assets = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'views' / 'assets.xml'
    ).read_text(encoding='utf-8')
    manifest = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / '__manifest__.py'
    ).read_text(encoding='utf-8')
    for name in _VENDORS:
        assert name not in assets, name
        assert name not in manifest, name
    assert 'chatboo_heavy_libs.js' in assets
    assert 'chatboo_heavy_libs.js' in manifest


def test_charts_use_local_engine_refs():
    for stack in ('owl1', 'owl2'):
        js = (
            deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js')
        ).read_text(encoding='utf-8')
        assert 'function bindEngines' in js
        assert 'new ChartLib(' in js
        assert 'global.Chart' not in js
        assert 'new global.Chart' not in js


def test_systray_does_not_call_check_health_on_boot():
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_systray.js'
    ).read_text(encoding='utf-8')
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_systray.js'
    ).read_text(encoding='utf-8')
    start = owl1.split('start: function', 1)[1].split('_enableSystray: function', 1)[0]
    assert '/chatboo/check_health' not in start
    assert 'pns_chatboo_show_systray' in start
    mounted = owl2.split('onMounted(async () => {', 1)[1].split('if (this.state.visible)', 1)[0]
    assert '/chatboo/check_health' not in mounted
    assert 'pns_chatboo_show_systray' in mounted
    http = (_ROOT / 'common' / 'models' / 'ir_http.py').read_text(encoding='utf-8')
    assert "info['pns_chatboo_show_systray']" in http
