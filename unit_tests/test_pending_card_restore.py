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
    assert 'chatboo_overlay_show' in tray
    assert '#home' not in tray


def _confirm_handler(src):
    start = src.index("const sendConfirm = function (retried) {")
    return src[start:start + 1500]


def _retry_method(src):
    start = src.index('_retryRefusedCard(evt, card, res, status, enable, again) {')
    return src[start:start + 2600]


def test_badge_peeks_without_rotating_the_card_token():
    for stack in ('owl1', 'owl2', 'owl3'):
        tray = _read('stacks', stack, 'pns_ai_chatboo', 'static', 'src', 'js', 'chatboo_systray.js')
        assert 'peek: true' in tray, stack


def test_refused_card_stays_and_does_not_ask_the_ai():
    files = (
        ('owl1', 'chatboo_component_v2.js'),
        ('owl2', 'chatboo_app.js'),
        ('owl3', 'chatboo_app.js'),
    )
    for stack, name in files:
        src = _read('stacks', stack, 'pns_ai_chatboo', 'static', 'src', 'js', name)
        handler = _confirm_handler(src)
        assert 'self._retryRefusedCard(' in handler, stack
        assert 'evt, card, res, status, enable,' in handler, stack
        retry = _retry_method(src)
        for err in ('too_soon', 'bad_token', 'missing_token'):
            assert err in retry, (stack, err)
        assert '/pns_ai_mcp/verification/pending' in retry, stack
        assert '_runAssistantTurn' not in retry, stack
        assert '_finishVerificationOutcome' not in retry, stack
        # The person already pressed Confirm: the card confirms again by itself, once.
        assert 'setTimeout(again, wait)' in retry, stack
        assert 'retried ? null : function () { sendConfirm(true); }' in src, stack
        assert 'sendConfirm(false)' in src, stack
        assert 'out of date' not in src, stack


def test_painted_cards_are_not_signed_again():
    files = (
        ('owl1', 'chatboo_component_v2.js'),
        ('owl2', 'chatboo_app.js'),
        ('owl3', 'chatboo_app.js'),
    )
    for stack, name in files:
        src = _read('stacks', stack, 'pns_ai_chatboo', 'static', 'src', 'js', name)
        start = src.index('_restorePendingVerifications() {')
        restore = src[start:start + 1400]
        assert 'held: this._heldCardIds()' in restore, stack
        assert 'this._restoringCards' in restore, stack
        assert 'held: this._heldCardIds(evt.verification_id)' in _retry_method(src), stack
        assert '_heldCardIds(except) {' in src, stack


def test_owl1_app_click_opens_overlay_on_14_and_15():
    js = ('stacks', 'owl1', 'pns_ai_chatboo', 'static', 'src', 'js')
    tray = _read(*js, 'chatboo_systray.js')
    v14 = _read(*js, 'chatboo_open_o14.js')
    o15 = _read(*js, 'chatboo_open_o15.js')
    assert 'web.ActionManager' not in tray
    assert '_executeClientAction' in v14
    assert "chatboo_overlay_show" in v14
    assert 'category("actions")' in o15
    assert '"chatboo_overlay_show"' in o15
