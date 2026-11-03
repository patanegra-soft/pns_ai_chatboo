# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Opening Chatboo rehydrates cards from /verification/pending, not a local queue."""
from pathlib import Path


def _read(*parts):
    return (Path(__file__).resolve().parents[1].joinpath(*parts)).read_text(
        encoding='utf-8'
    )


def test_owl2_restores_from_pending_route_on_show():
    app = _read('stacks', 'owl2', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_app.js')
    overlay = _read(
        'stacks', 'owl2', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_overlay.js',
    )
    assert '_restorePendingVerifications' in app
    assert '/pns_ai_mcp/verification/pending' in app
    assert '_restorePendingVerifications' in overlay
    assert 'localStorage' not in app[app.index('_restorePendingVerifications'):app.index('_restorePendingVerifications') + 600]


def test_owl2_auth_badge_is_warning_not_danger():
    css = _read('stacks', 'owl2', 'pns_ai_chatboo', 'static', 'src', 'css', 'chatboo_systray.css')
    tray = _read('stacks', 'owl2', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_systray.js')
    overlay = _read(
        'stacks', 'owl2', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_overlay.js',
    )
    assert '.o_chatboo_badge.bg-warning' in css
    assert '_showBadge("auth")' in tray or "_showBadge('auth')" in tray
    assert 'Chatboo is waiting for your confirmation' in tray
    assert 'chatboo-auth-cue' in tray
    assert 'forceHidden: true' in overlay
    assert 'forceHidden' in tray
    assert 'openedViaMenu' not in overlay
    assert 'openFromMenu' not in overlay
    assert 'isHidden()' in overlay
    assert 'api.open(ctx)' in overlay
    assert 'requestLooksLikeChatboo' in overlay
    assert 'action.doAction' in overlay
    assert 'act.restore' not in overlay
    assert 'restoreUnderlyingView' not in overlay
    assert 'category("actions")' not in overlay
    assert '#home' not in overlay


def test_owl1_restores_from_pending_route_on_show():
    comp = _read(
        'stacks', 'owl1', 'pns_ai_chatboo', 'static', 'src', 'js',
        'chatboo_component_v2.js',
    )
    tray = _read(
        'stacks', 'owl1', 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_systray.js',
    )
    assert '_restorePendingVerifications' in comp
    assert '/pns_ai_mcp/verification/pending' in comp
    assert 'comp._restorePendingVerifications' in tray
    assert "chatboo_auth_cue" in tray
    assert "_showBadge('auth')" in tray
    assert 'Chatboo is waiting for your confirmation' in tray
    assert 'ChatbooAction' not in comp
    assert 'history_back' not in comp
    assert 'action_registry.add' not in comp
    assert '_executeClientAction' in tray
    assert 'chatboo_overlay_show' in tray
    assert '#home' not in tray
