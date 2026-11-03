# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Card width follows each Odoo user (server field), not the browser."""
from __future__ import annotations

import re
from pathlib import Path
from _deployed import deployed

_ROOT = Path(__file__).resolve().parents[1]


def _normalize():
    src = (_ROOT / 'common' / 'models' / 'res_users.py').read_text(encoding='utf-8')
    start = src.index('def normalize_card_width_ratio')
    end = src.index('\nclass ')
    ns = {}
    exec(src[start:end], ns)  # noqa: S102 — isolated helper, no Odoo import
    return ns['normalize_card_width_ratio']


def test_normalize_card_width_ratio():
    fn = _normalize()
    assert fn(None) == 0.0
    assert fn('') == 0.0
    assert fn(0) == 0.0
    assert fn(-1) == 0.0
    assert fn('nope') == 0.0
    assert fn(0.5) == 0.5
    assert fn(2) == 1.0
    assert fn('0.8') == 0.8


def test_user_field_and_prefs_route_both_stacks():
    model = (_ROOT / 'common' / 'models' / 'res_users.py').read_text(encoding='utf-8')
    assert "chatboo_card_width_ratio = fields.Float" in model
    assert 'SELF_READABLE_FIELDS' in model
    assert 'SELF_WRITEABLE_FIELDS' in model
    assert 'chatboo_set_own_card_width_ratio' in model
    assert 'self.env.user' in model
    assert 'localStorage' not in model
    for stack in ('owl1', 'owl2'):
        ctrl = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'controllers' / 'chatboo.py'
        ).read_text(encoding='utf-8')
        assert "/chatboo/prefs" in ctrl
        assert 'card_width_ratio' in ctrl
        assert '_with_user_prefs' in ctrl
        assert ctrl.count("data['card_width_ratio']") == 1
        assert ctrl.count("data['show_series_stats']") == 1
        assert 'if card_width_ratio is not None' in ctrl
        assert 'if show_series_stats is not None' in ctrl
        assert ctrl.count('_with_user_prefs(') >= 3
        users = (
            deployed(stack, 'models', 'res_users.py')
        ).read_text(encoding='utf-8')
        if stack == 'owl2':
            assert users == model
        else:
            assert 'def __init__(self, pool, cr)' in users
            assert 'chatboo_card_width_ratio' in users
            assert 'chatboo_show_series_stats' in users


def test_client_helper_has_no_local_storage():
    common = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_card_width.js'
    ).read_text(encoding='utf-8')
    assert 'localStorage.getItem' not in common
    assert 'localStorage.setItem' not in common
    assert 'DEFAULT_RATIO = 2 / 3' in common
    assert 'MIN_PX = 100' in common
    assert 'canvasCapPx' in common
    assert 'visualViewport' in common
    assert 'ChatbooCardWidth' in common
    assert 'function relayoutSoon' in common
    assert 'softResize' in common
    assert 'function previewGuide' in common
    assert 'function hideGuide' in common
    assert 'ratioFromRoot' not in common
    assert '_chatbooCardWidthRatio' not in common
    assert 'shouldDeferResize' not in common
    assert 'HEAVY_CANVAS_ROWS' not in common
    assert 'shouldUseResizeGuide' not in common
    for stack in ('owl1', 'owl2'):
        js = (
            deployed(stack, 'static', 'src', 'js', 'chatboo_card_width.js')
        ).read_text(encoding='utf-8')
        assert js == common


def test_chart_card_css_and_resize_handle_both_stacks():
    for stack in ('owl1', 'owl2', 'common'):
        if stack == 'common':
            css_path = _ROOT / 'common' / 'static' / 'src' / 'css' / 'chatboo_dashboard.css'
        else:
            css_path = (
                deployed(stack, 'static', 'src', 'css', 'chatboo_dashboard.css')
            )
        css = css_path.read_text(encoding='utf-8')
        assert 'min-width: min(100px, 100%)' in css
        assert 'min(var(--o-chatboo-card-width' in css
        assert 'overflow-x: auto' in css
        assert 'overflow-x: hidden' in css
        assert '.o_chatboo_card_resize' in css
        assert '.o_chatboo_card_resize_guide' in css
        assert 'o_chatboo_message--chart' in css


def test_restore_button_and_rpc_both_stacks():
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    owl2_xml = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    assert "_t('Restore default width')" in owl1
    assert '_t("Restore default width")' in owl2
    for blob in (owl1, owl2_xml):
        assert 'o_chatboo_card_resize' in blob
        assert 'o_chatboo_card_width_reset' in blob
        bar = blob.split('o_ai_export_bar', 1)[1]
        assert bar.find('o_chatboo_card_width_reset') < bar.find('tipDownloadPdf')
    for fn in (owl1, owl2):
        wide = fn.split('messageWantsWideCanvas', 1)[1].split(
            '_fileBannerCardClass', 1
        )[0]
        assert 'show-table' in wide
        assert 'include_table' in wide
        assert 'o_chatboo_file_banner' not in wide
    for stack in ('owl1', 'owl2', 'common'):
        if stack == 'common':
            charts = _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
        else:
            charts = (
                deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js')
            )
        expand = charts.read_text(encoding='utf-8').split(
            'function expandChartMessageCanvas', 1
        )[1]
        assert 'bubble.style.width = "100%"' not in expand
        assert 'removeProperty("width")' in expand
    assert "/chatboo/prefs" in owl1
    assert '/chatboo/prefs' in owl2
    assert 'card_width_ratio' in owl1
    assert 'card_width_ratio' in owl2
    owl1_resize = owl1.split('_onCardResizeStart')[1].split('messageWantsWideCanvas')[0]
    owl2_resize = owl2.split('_onCardResizeStart')[1].split('_initTtsUi')[0]
    for blob in (owl1_resize, owl2_resize):
        assert 'previewGuide' in blob
        assert 'hideGuide' in blob
        assert 'applyPx' in blob
        drag = blob.split('onMove', 1)[1].split('onUp', 1)[0]
        assert 'applyPx' not in drag
        assert 'relayoutSoon(root)' not in drag
        assert 'shouldDeferResize' not in blob
        assert 'localStorage' not in blob
    assert 'ir.config_parameter' not in owl1
    assert 'ir.config_parameter' not in owl2


def test_export_strips_resize_chrome():
    for stack in ('owl1', 'owl2'):
        js = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        sanitize = js.split('function sanitizeWordClone', 1)[1]
        assert 'o_chatboo_card_resize' in sanitize
        assert 'o_chatboo_card_resize_guide' in sanitize
        assert 'o_chatboo_card_width_reset' in sanitize
        host = js.split('function buildPdfCaptureHost', 1)[1].split(
            'function saveCanvasAsPdf', 1
        )[0]
        assert 'o_chatboo_card_resize' in host
        assert 'o_chatboo_card_resize_guide' in host
        assert 'o_chatboo_card_width_reset' in host


def test_i18n_restore_width_both_stacks():
    files = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'i18n' / 'es.po',
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'i18n' / 'es_ES.po',
    )
    for path in files:
        text = path.read_text(encoding='utf-8')
        assert 'msgid "Restore default width"' in text
        assert 'msgid "Chatboo card width"' in text
        assert 'Restaurar ancho por defecto' in text


def test_overlay_open_focuses_prompt_both_stacks():
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_overlay.js'
    ).read_text(encoding='utf-8')
    show = owl2.split('async show(', 1)[1].split('\n    hide() {', 1)[0]
    assert 'comp._focusInput' in show
    owl1_systray = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_systray.js'
    ).read_text(encoding='utf-8')
    assert 'afterOverlayPaint' not in owl1_systray
    after = owl1_systray.split('_afterOverlayShown:', 1)[1].split('_onClick:', 1)[0]
    assert '_focusChatInput' in after
    assert 'querySelector' not in after
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    assert 'preventScroll' in owl1
    assert 'preventScroll' in (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')


def test_systray_and_composer_have_no_hover_noise():
    owl1_tray = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_systray.xml'
    ).read_text(encoding='utf-8')
    assert 'href=' not in owl1_tray
    assert 'title="Chatboo"' in owl1_tray
    assert '<button' not in owl1_tray
    assert 'dropdown-toggle o-no-caret' in owl1_tray
    assert 'aria-label="Open Chatboo AI"' in owl1_tray
    owl2_tray = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_systray.xml'
    ).read_text(encoding='utf-8')
    assert 'title="Chatboo"' in owl2_tray
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    footer = owl1.split('o_chatboo_main_footer', 1)[1].split(
        'Session Modal', 1,
    )[0]
    prefs1 = footer.split('o_chatboo_footer_prefs', 1)[1].split(
        'o_chatboo_tts_toggle', 1
    )[0]
    assert 't-att-data-tip="_screenFocusTitle()"' in prefs1
    assert 't-att-data-tip="_seriesStatsTitle()"' in prefs1
    assert 't-att-title=' not in prefs1
    assert 't-att-title=' not in footer.split('o_chatboo_tts_toggle', 1)[1]
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    footer2 = owl2.split('o_chatboo_main_footer', 1)[1]
    prefs2 = footer2.split('o_chatboo_footer_prefs', 1)[1].split(
        'o_chatboo_tts_toggle', 1
    )[0]
    assert 't-att-data-tip="screenFocusTitle"' in prefs2
    assert 't-att-data-tip="seriesStatsTitle"' in prefs2
    assert 't-att-title=' not in prefs2
    assert 't-att-title=' not in footer2.split('o_chatboo_tts_toggle', 1)[1]
    assert 't-att-title="tipDownloadPdf"' in owl1
    assert 't-att-title="tipDownloadPdf"' in owl2


def _normalize_stats():
    src = (_ROOT / 'common' / 'models' / 'res_users.py').read_text(encoding='utf-8')
    start = src.index('def normalize_show_series_stats')
    end = src.index('\nclass ')
    ns = {}
    exec(src[start:end], ns)  # noqa: S102 — isolated helper, no Odoo import
    return ns['normalize_show_series_stats']


def test_normalize_show_series_stats():
    fn = _normalize_stats()
    assert fn(None) is False
    assert fn(False) is False
    assert fn(0) is False
    assert fn('') is False
    assert fn('false') is False
    assert fn(True) is True
    assert fn(1) is True
    assert fn('true') is True
    assert fn('1') is True
    assert fn('on') is True


def test_show_series_stats_pref_and_ui_both_stacks():
    model = (_ROOT / 'common' / 'models' / 'res_users.py').read_text(encoding='utf-8')
    assert 'chatboo_show_series_stats = fields.Boolean' in model
    assert 'default=False' in model
    assert 'chatboo_set_own_show_series_stats' in model
    assert 'self.env.user' in model.split('chatboo_set_own_show_series_stats', 1)[1]
    assert 'localStorage' not in model
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    owl2_xml = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'xml' / 'chatboo_app.xml'
    ).read_text(encoding='utf-8')
    for blob in (owl1, owl2):
        assert 'show_series_stats' in blob
        assert 'setShowSeriesStats' in blob
        assert "_t('Stats')" not in blob
        assert '_t("Stats")' not in blob
        assert 'Statistics ON' in blob
        assert 'Statistics OFF' in blob
        assert 'Covered view ON' in blob
        assert 'Covered view OFF' in blob
        assert 'Include statistics on the next chart' not in blob
        assert 'Screen context active' not in blob
        apply_fn = blob.split('_applyShowSeriesStats(value)', 1)[1].split(
            '_applyCardWidthRatio', 1
        )[0]
        assert 'localStorage' not in apply_fn
        assert '/chatboo/prefs' in apply_fn
    footer1 = owl1.split('o_chatboo_main_footer', 1)[1]
    footer2 = owl2_xml.split('o_chatboo_main_footer', 1)[1]
    for footer in (footer1, footer2):
        assert 'o_chatboo_footer_prefs' in footer
        assert 'o_chatboo_show_series_stats' in footer
        assert 'o_chatboo_directive_chip--off' in footer
        chip = footer.split('o_chatboo_show_series_stats', 1)[1].split('</span>', 1)[0]
        assert 'stats' in chip
        assert 'fa-bar-chart' in chip
        assert 't-att-data-tip=' in chip
        assert 't-att-title=' not in chip
        assert 't-att-aria-label=' in chip
        assert 'type="checkbox"' not in chip
        assert 't-if="state.screenFocusLabel"' not in footer.split(
            'o_chatboo_footer_prefs', 1
        )[0][-80:]
    for stack in ('owl1', 'owl2'):
        css = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'css' / 'chatboo_floating.css'
        ).read_text(encoding='utf-8')
        prefs_css = css.split('.o_chatboo_footer_prefs', 1)[1].split(
            '.o_chatboo_prompt_wrap', 1
        )[0]
        assert 'gap: 12px' in prefs_css
        assert 'margin-inline-start: auto' not in prefs_css
        assert 'ml-auto' not in prefs_css
        assert 'float:' not in prefs_css
        assert 'o_chatboo_directive_chip--off' in prefs_css
        assert 'box-sizing: border-box' in prefs_css
        assert 'content: attr(data-tip)' in prefs_css
        assert 'translate(-50%, calc(-100% - 6px))' in prefs_css
        assert 'border: 1px solid transparent' in prefs_css
        assert 'border-color: var(--chatboo-border' in prefs_css
        assert 'border: 1px solid var(--chatboo-border' not in prefs_css
        assert 'color: var(--chatboo-text-muted' in prefs_css
        assert 'background-color: transparent' in prefs_css
        assert 'opacity: 0.58' in prefs_css
    es1 = (_ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'i18n' / 'es.po').read_text(
        encoding='utf-8'
    )
    es2 = (_ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'i18n' / 'es_ES.po').read_text(
        encoding='utf-8'
    )
    for po in (es1, es2):
        assert 'msgid "Stats"' not in po
        assert 'msgid "Include statistics on the next chart"' not in po
        assert 'msgid "Screen context active — click to ignore this chat"' not in po
        assert 'msgid "Screen context off — click to re-enable"' not in po
        assert 'msgid "Statistics ON"' in po
        assert 'msgid "Statistics OFF"' in po
        assert 'msgid "Covered view ON"' in po
        assert 'msgid "Covered view OFF"' in po
        assert 'msgstr "Estadísticas ON"' in po
        assert 'msgstr "Estadísticas OFF"' in po
        assert 'msgstr "Vista tapada ON"' in po
        assert 'msgstr "Vista tapada OFF"' in po
        assert 'msgid "Chatboo chart statistics"' in po


def test_series_stats_gate_and_export_both_stacks():
    for stack in ('owl1', 'owl2', 'common'):
        if stack == 'common':
            charts_path = _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
        else:
            charts_path = (
                deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js')
            )
        charts = charts_path.read_text(encoding='utf-8')
        assert 'var showSeriesStats = false' in charts
        assert 'function setShowSeriesStats' in charts
        assert 'function maybeMountSeriesStats' in charts
        assert 'localStorage' not in charts
        setter = charts.split('function setShowSeriesStats', 1)[1].split(
            'function getShowSeriesStats', 1
        )[0]
        assert 'querySelectorAll' not in setter
        gate = charts.split('function mountToolbarOrFallback', 1)[1].split(
            'function _t', 1
        )[0]
        assert 'if (showSeriesStats)' in gate
        assert 'mountSeriesStats(block, meta)' in gate
        hydrate = charts.split('function hydrateRoot', 1)[1].split(
            'function destroyInRoot', 1
        )[0]
        assert 'maybeMountSeriesStats(block, rows, null)' in hydrate
        assert 'maybeMountSeriesStats(block, rows, meta)' in hydrate
        helper = charts.split('function maybeMountSeriesStats', 1)[1].split(
            'function mountSeriesStats', 1
        )[0]
        assert 'analyzeForStats(rows)' in helper
        if stack != 'common':
            common = (
                _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
            ).read_text(encoding='utf-8')
            assert charts == common
    for stack in ('owl1', 'owl2'):
        export = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'js' / 'chatboo_export.js'
        ).read_text(encoding='utf-8')
        resolve = export.split('function resolveExportStatsAoa', 1)[1].split(
            'function resolveExportStatsHtml', 1
        )[0]
        assert "querySelector('.o_chatboo_series_stats')" in resolve
        assert 'if (!painted)' in resolve


def test_series_stats_use_analyze_for_stats_not_money_regex():
    """Ranking like ZMEB (Cliente + Base imponible) has no time axis and
    the money regex does not match 'imponible'. Stats still use analyzeForStats.
    """
    charts = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
    ).read_text(encoding='utf-8')
    helper = charts.split('function maybeMountSeriesStats', 1)[1].split(
        'function mountSeriesStats', 1
    )[0]
    assert 'analyzeForStats(rows)' in helper
    assert 'metricsOnly' not in helper
    assert 'imponible' not in charts.split('var MONEY_KEY_RE', 1)[1].split(
        'var COUNT_KEY_RE', 1
    )[0]


def test_both_stacks_ship_the_same_version():
    """A version pinned by hand goes stale on the next bump: compare instead."""
    seen = set()
    for stack in ('owl1', 'owl2'):
        manifest = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / '__manifest__.py'
        ).read_text(encoding='utf-8')
        version = re.search(r"'version':\s*'([\d.]+)'", manifest)
        assert version, stack
        seen.add(version.group(1))
    assert len(seen) == 1, seen


def test_chart_toolbar_appends_after_table():
    charts = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
    ).read_text(encoding='utf-8')
    mount = charts.split('function mountToolbar(block, meta)', 1)[1].split(
        'function categoryAxisIsTemporal', 1
    )[0]
    assert 'block.appendChild(toolbar)' in mount
    assert 'block.appendChild(host)' in mount
    assert mount.index('block.appendChild(host)') < mount.index('block.appendChild(toolbar)')
    assert 'insertBefore(toolbar' not in mount
    gate = charts.split('function shouldOfferChart', 1)[1].split(
        'function mountToolbarOrFallback', 1
    )[0]
    assert 'categoryAxisIsTemporal' not in gate
    assert 'isChartMetricKey' in gate
    grids = (
        _ROOT / 'common' / 'ai' / 'contexts' / 'domain'
        / 'presentation_grids' / 'presentation_grids.xml'
    ).read_text(encoding='utf-8')
    assert 'Toolbar **below** the table' in grids


def test_chart_series_follow_table_column_order():
    """Legend/series stay in table column order; categories follow visible rows."""
    charts = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
    ).read_text(encoding='utf-8')
    order = charts.split('function orderSeriesKeys', 1)[1].split(
        'function isRatioLikeKey', 1
    )[0]
    assert 'pickDominantMetric' not in order
    assert 'seriesKeys.slice()' in order
    assert 'orderPeriodSeriesKeys' in order
    assert 'function applyVisibleRowOrder' in charts
    render = charts.split('function renderChart', 1)[1].split(
        'function hideChart', 1
    )[0]
    assert 'applyVisibleRowOrder(block, meta)' in render
    sort = charts.split('function applyTableSort', 1)[1].split(
        'function cycleSortOnHeader', 1
    )[0]
    assert 'refreshOpenChart(table)' in sort
    assert 'secondary.col' in sort
    refresh = charts.split('function refreshOpenChart', 1)[1].split(
        'function applyTableSort', 1
    )[0]
    assert 'data-chatboo-chart-open' in refresh
    assert 'renderChart(' in refresh
    axis = charts.split('function resolveAxisIds', 1)[1].split(
        'function resolveYTitles', 1
    )[0]
    assert 'meta.dominantKey' in axis
    assert 'idx === 0' not in axis


def test_table_secondary_sort_and_column_drag():
    charts = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
    ).read_text(encoding='utf-8')
    cycle = charts.split('function cycleSortOnHeader', 1)[1].split(
        'var COL_DRAG_THRESHOLD', 1
    )[0]
    assert 'state.secondary = { col: state.col, dir: state.dir }' in cycle
    assert 'state.secondary = null' in cycle
    assert 'state.dir === "none"' in cycle
    bind = charts.split('function bindHeaderPointer', 1)[1].split(
        'function bindSortableTables', 1
    )[0]
    assert 'COL_DRAG_THRESHOLD' in bind
    assert 'moveTableColumn' in bind
    assert 'reindexSortCols' in bind
    assert 'rewriteDatasetColumnOrder' in bind
    assert 'cycleSortOnHeader' in bind
    assert 'if (dragged)' in bind
    assert 'click' not in bind
    assert 'function moveTableColumn' in charts
    assert 'o_chatboo_col_reorder_guide' in charts
    assert 'o_ai_ficha_title' in charts.split('function tableSectionRows', 1)[1]
    for stack in ('owl1', 'owl2'):
        js = (
            deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js')
        ).read_text(encoding='utf-8')
        assert js == charts
        css = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
            / 'static' / 'src' / 'css' / 'chatboo_floating.css'
        ).read_text(encoding='utf-8')
        assert '.o_chatboo_col_reorder_guide' in css
        assert 'cursor: grabbing' in css
