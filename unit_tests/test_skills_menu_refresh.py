# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Slash menu refreshes when the skill catalog changes."""
import ast
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_chatboo_notifies_bus_on_skill_crud():
    text = (
        _ROOT / 'common' / 'models' / 'ai_skill.py'
    ).read_text(encoding='utf-8')
    assert 'def _chatboo_notify_skills_changed' in text
    assert "'action': 'skills_changed'" in text
    assert 'skip_hardcoded_restrictions' in text
    assert 'chatboo_confirm_op' in text
    assert "'updated'" in text
    assert 'skill_author_usage' in text
    assert '_chatboo_skill_card' in text
    session = (
        _ROOT / 'common' / 'models' / 'chatboo_session.py'
    ).read_text(encoding='utf-8')
    assert 'append_local_ack' in session
    assert 'provider_meta' in session
    assert "meta['usage'] = usage" in session
    wizard = (
        _ROOT / 'common' / 'models' / 'skill_capture_wizard.py'
    ).read_text(encoding='utf-8')
    assert "chatboo_confirm_op" in wizard
    assert "from_chatboo" not in wizard
    assert "'ai_session_ref': self.chatboo_session_id" in wizard


def _method_sources(text):
    tree = ast.parse(text)
    return {
        node.name: ast.get_source_segment(text, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }


def test_capture_wizard_is_chatboo_by_its_own_session():
    wizard = (
        _ROOT / 'common' / 'models' / 'skill_capture_wizard.py'
    ).read_text(encoding='utf-8')
    methods = _method_sources(wizard)
    assert 'if ids or not self.chatboo_session_id:' in methods['_resolve_agent_ids']
    for name in ('_reapply_turn_fetch_wrap', 'action_create_draft'):
        assert 'if not self.chatboo_session_id:' in methods[name], name
    for name in ('action_author_params', 'action_author_help', 'action_adapt_code'):
        assert 'if self.chatboo_session_id:' in methods[name], name
    assert 'warn_incomplete_capture' in wizard
    session = (
        _ROOT / 'common' / 'models' / 'chatboo_session.py'
    ).read_text(encoding='utf-8')
    assert session.count("'default_from_chat': True,") == 2
    assert 'from_chatboo' not in session
    for stack in ('owl1', 'owl2'):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
        assert not (base / 'models' / 'skill_capture_wizard.py').exists()
        views = (base / 'views' / 'skill_capture_wizard_views.xml').read_text(encoding='utf-8')
        assert 'ref="pns_ai_mcp.view_ai_skill_capture_wizard_form"' in views
        assert '<field name="chatboo_session_id" invisible="1"/>' in views
        manifest = (base / '__manifest__.py').read_text(encoding='utf-8')
        assert "'views/skill_capture_wizard_views.xml'" in manifest


def test_slash_js_refetches_and_handles_bus():
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo'
        / 'static' / 'src' / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    for js in (owl2, owl1):
        assert 'async _ensureSkills(force)' in js
        assert '_ensureSkills(true)' in js
        assert 'action === "skills_changed"' in js or "action === 'skills_changed'" in js
        assert 'payload.confirm' in js
        assert 'hasUsage' in js or 'msg.local_ack && !msg.usage' in js
        assert 'session_id: this.state.currentSessionId' in js
        assert 'code: "reload-skills"' not in js
        assert "code: 'reload-skills'" not in js
    assert "function _busNotificationList" in owl2
    assert "notif.payload" in owl2
    assert "raw.detail" in owl2
    assert "const opening = !this.state.slashOpen" in owl2
    assert 'subscribe("pns_chatboo_sync"' in owl2
    assert "this._skillsListInflight" in owl2
