# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Compose a slash skill from a Chatboo turn (fetch plan + presentation)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SNIPPET = (
    "src = previous_result\n"
    "rows = get_safe_plan_steps(src)\n"
    "result = {'formatted_text': 'ok'}\n"
)
_FETCH = [
    {
        'op': 'api_call',
        'server': 'ext',
        'tool': 'ListX',
        'arguments': {'from': '2026-08-31', 'to': '2026-08-31'},
        'extra_noise': 'drop-me',
    },
    {
        'op': 'api_call',
        'server': 'ext',
        'tool': 'ListY',
        'arguments': {'limit': 100},
    },
]


def _load():
    path = _ROOT / 'common' / 'utils' / 'skill_capture_compose.py'
    spec = importlib.util.spec_from_file_location('skill_capture_compose', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_snippet_without_propose_needs_prior_plan():
    compose = _load()
    assert compose.code_needs_prior_plan(_SNIPPET)
    assert not compose.code_needs_prior_plan('')
    assert not compose.code_needs_prior_plan(
        "result = {'propose_steps': [], 'continue': True}",
    )


def test_sanitize_drops_non_fetch_and_extra_keys():
    compose = _load()
    clean = compose.sanitize_fetch_steps(_FETCH)
    assert [step['tool'] for step in clean] == ['ListX', 'ListY']
    assert 'extra_noise' not in clean[0]
    assert clean[0]['arguments']['from'] == '2026-08-31'
    mixed = list(_FETCH) + [{'op': 'write', 'model': 'res.partner'}]
    assert compose.sanitize_fetch_steps(mixed) == []


def test_wrap_replays_turn_fetch_then_presentation():
    compose = _load()
    out = compose.wrap_presentation_with_turn_fetch(_SNIPPET, _FETCH)
    assert 'propose_steps' in out
    assert "'continue': True" in out
    assert 'ListX' in out
    assert '2026-08-31' in out
    assert 'formatted_text' in out
    assert 'get_safe_plan_steps' in out
    assert 'extra_noise' not in out
    compile(out, '<skill>', 'exec')
    unchanged = compose.wrap_presentation_with_turn_fetch(
        "result = {'propose_steps': _X, 'continue': True}\n"
        "src = previous_result\n",
        _FETCH,
    )
    assert unchanged.startswith('result =')


def test_plan_steps_from_nested_arguments():
    compose = _load()
    raw = (
        '{"arguments": {"plan_steps": ['
        '{"op": "fetch_url", "url": "https://example.test"}]}}'
    )
    steps = compose.plan_steps_from_operation_data(raw)
    assert steps[0]['op'] == 'fetch_url'


def test_slash_from_skill_turn_prompt():
    compose = _load()
    assert compose.slash_from_skill_turn_prompt('') == ''
    assert compose.slash_from_skill_turn_prompt(None) == ''
    assert compose.slash_from_skill_turn_prompt({'arguments': ''}) == ''
    assert compose.slash_from_skill_turn_prompt(
        {'skill': 'acme-cuentas-analiticas-facturas', 'arguments': ''},
    ) == 'acme-cuentas-analiticas-facturas'
    assert compose.slash_from_skill_turn_prompt(
        '{\n  "skill": "/sample-topic",\n  "arguments": ""\n}',
    ) == 'sample-topic'
    assert compose.slash_from_skill_turn_prompt('not-json') == ''


def test_a_new_slash_does_not_bind_the_catalog_turn():
    compose = _load()
    assert compose.same_invoke_slash('/acme-foo', 'acme_foo')
    assert not compose.same_invoke_slash('an-rentabilidad', 'acme-rentabilidad-areas-de-negocio')
    assert compose.capture_binds_catalog_slash(
        '', 'acme-rentabilidad-areas-de-negocio',
    )
    assert compose.capture_binds_catalog_slash(
        'acme-rentabilidad-areas-de-negocio',
        'acme-rentabilidad-areas-de-negocio',
    )
    assert compose.capture_binds_catalog_slash(
        'rentabilidad-areas-de-negocio',
        'acme-rentabilidad-areas-de-negocio',
        name_command='acme-rentabilidad-areas-de-negocio',
        catalog_command='acme-rentabilidad-areas-de-negocio',
    )
    assert not compose.capture_binds_catalog_slash(
        'an-rentabilidad',
        'acme-rentabilidad-areas-de-negocio',
        name_command='acme-an-rentabilidad',
        catalog_command='acme-rentabilidad-areas-de-negocio',
    )


def test_slash_from_skill_turn_logs_picks_catalog_tool():
    compose = _load()
    assert compose.is_catalog_skill_turn_tool('skill_fast_path')
    assert compose.is_catalog_skill_turn_tool('skill_report_handoff')
    assert not compose.is_catalog_skill_turn_tool('relaxaicode')
    rows = [
        ('relaxaicode', {'skill': 'ignore-me'}),
        ('skill_fast_path', {
            'skill': 'acme-cuentas-analiticas-facturas',
            'arguments': '',
        }),
    ]
    assert compose.slash_from_skill_turn_logs(rows) == (
        'acme-cuentas-analiticas-facturas'
    )
    assert compose.slash_from_skill_turn_logs([
        ('llm_response', {'skill': 'nope'}),
    ]) == ''


def test_catalog_skill_body_does_not_need_fetch_wrap():
    compose = _load()
    catalog = (
        "Move = env['account.move']\n"
        "result = {'data': [], 'propose_steps': []}\n"
        "src = previous_result\n"
    )
    assert not compose.code_needs_prior_plan(catalog)
    wrapped = compose.wrap_presentation_with_turn_fetch(catalog, _FETCH)
    assert wrapped == catalog


def test_empty_previous_result_stub_loses_to_presentable_table():
    compose = _load()
    stub = (
        "try:\n"
        "    src = previous_result\n"
        "except NameError:\n"
        "    src = None\n"
        "result = {}\n"
    )
    table = (
        "rows = [{'id': 1, 'name': 'A'}]\n"
        "result = {'data': rows, '__return_direct__': True}\n"
    )
    assert compose.snippet_is_empty_result(stub)
    assert not compose.snippet_is_empty_result(table)
    assert compose.score_capture_snippet(table) > compose.score_capture_snippet(stub)


def test_session_wires_turn_fetch_wrap():
    src = (
        _ROOT / 'common' / 'models' / 'chatboo_session.py'
    ).read_text(encoding='utf-8')
    assert 'compose_capture_code' in src
    assert 'compose_capture_pipeline' in src
    assert 'capture_is_incomplete' in src
    assert '_relaxaicode_codes_for_turn' in src
    assert '_fetch_steps_for_turn' in src
    assert 'previous_result' in src
    assert '_catalog_slash_for_turn' in src
    assert '_catalog_skill_for_capture' in src
    assert 'slash_from_skill_turn_logs' in src
    assert 'catalog_slash' in src
    assert 'capture_binds_catalog_slash' in src
    assert 'active_test=False' in src
    assert '_wrap_open_page(code_body, corr)' in src
    assert 'score_capture_snippet' in src


_PARSE = (
    "result = {}\n"
    "steps = get_safe_plan_steps(previous_result)\n"
    "rows = [{'Modelo': 'demo', 'Input $/MTok': 1.0}]\n"
    "result = {'rows': rows}\n"
)
_FORMAT = (
    "result = {}\n"
    "src = []\n"
    "if previous_result:\n"
    "    src = previous_result.get('rows') or previous_result.get('data') or []\n"
    "rows = list(src or [])\n"
    "result = {'data': rows, '__show_table__': True}\n"
)
_FETCH_URL = [
    {
        'op': 'fetch_url',
        'url': 'https://example.test/pricing.md',
        'method': 'GET',
    },
]


def test_merge_fetch_steps_deduplicates():
    compose = _load()
    first = [{'op': 'fetch_url', 'url': 'https://a.test', 'method': 'GET'}]
    second = list(first) + [
        {'op': 'fetch_url', 'url': 'https://b.test', 'method': 'GET'},
    ]
    merged = compose.merge_fetch_steps([first, second])
    assert len(merged) == 2
    assert merged[0]['url'] == 'https://a.test'
    assert merged[1]['url'] == 'https://b.test'


def test_formatter_only_loses_when_turn_has_multiple_snippets():
    compose = _load()
    assert compose.snippet_is_formatter_only(_FORMAT)
    assert compose.score_capture_snippet(_FORMAT, relaxaicode_count=2) < (
        compose.score_capture_snippet(_PARSE, relaxaicode_count=2)
    )


def test_compose_capture_pipeline_multi_phase_starts_with_fetch():
    compose = _load()
    out, incomplete = compose.compose_capture_pipeline(
        [_PARSE, _FORMAT], _FETCH_URL,
    )
    assert not incomplete
    assert '_TURN_FETCH_STEPS' in out
    assert 'propose_steps' in out
    assert '_pipeline_rows' in out
    compile(out, '<skill>', 'exec')


def test_compose_capture_pipeline_formatter_only_without_fetch_is_incomplete():
    compose = _load()
    out, incomplete = compose.compose_capture_pipeline([_FORMAT], [])
    assert incomplete
    assert '_TURN_FETCH_STEPS' not in out


def test_wizard_reapplies_wrap_after_onchange():
    src = (
        _ROOT / 'common' / 'models' / 'skill_capture_wizard.py'
    ).read_text(encoding='utf-8')
    assert '_reapply_turn_fetch_wrap' in src
    assert 'compose_capture_code' in src
    assert 'warn_incomplete_capture' in src
    assert '_onchange_source_log_id' in src
    assert 'action_create_draft' in src
    assert "skill_compose_fixed'] = 'compose-agent'" in src
    assert 'action_author_params' in src
    assert 'action_author_help' in src
    assert 'action_adapt_code' in src
    assert '_page_has_param_rows' in src
    assert 'not self._page_has_param_rows()' in src
    assert 'keep_query=True' in src
    author = src.split('def action_author_params', 1)[1].split('\n    def ', 1)[0]
    adapt = src.split('def action_adapt_code', 1)[1].split('\n    def ', 1)[0]
    create = src.split('def action_create_draft', 1)[1].split('\n    def ', 1)[0]
    assert 'keep_query=True' in author
    assert '_reapply_turn_fetch_wrap()' not in author
    assert 'keep_query=True' in adapt
    assert '_reapply_turn_fetch_wrap()' not in adapt.split('keep_query=True', 1)[0]
    assert 'keep_query=True' in create
    assert (
        'if self._opens_saved_page() and self._page_has_param_rows():'
    ) in create
    assert '_assert_captured_page_reusable' in create


def test_capture_help_comes_from_the_turn_not_the_slash():
    src = (
        _ROOT / 'common' / 'models' / 'chatboo_session.py'
    ).read_text(encoding='utf-8')
    assert 'capture_help_text' in src
    assert '_turn_user_prompt' in src
    assert 'description = capture_help_text(' in src


def test_a_catalogue_peek_is_not_part_of_the_captured_query():
    compose = _load()
    query = (
        "rows = env['account.move'].search([])\n"
        "result = {'data': [{'n': len(rows)}]}\n"
    )
    peek = "env['ai.skill'].search([])\nresult = []\n"
    out, _incomplete = compose.compose_capture_pipeline([peek, query], [])
    assert "ai.skill" not in out
    assert "account.move" in out
    page = (
        "result = {'data': []}\n"
        "_page = \"see env['ai.skill'] in the text\"\n"
    )
    assert not compose.snippet_reads_catalogue(page)


def test_a_self_contained_last_round_is_the_whole_skill():
    """Earlier rounds that only looked around do not go in, and no warning."""
    compose = _load()
    probe = (
        "Team = env['crm.team']\n"
        "result = {'fields': sorted(Team._fields)[:5]}\n"
    )
    sample = (
        "lines = env['account.analytic.line'].search([], limit=5)\n"
        "result = {'sample': [l.id for l in lines]}\n"
    )
    query = (
        "rows = env['account.analytic.line'].search_read([], ['amount'])\n"
        "href = page_url(rows, 'Rentabilidad', new=True)\n"
        "result = {'page_url': href, 'data': rows[:50]}\n"
    )
    out, incomplete = compose.compose_capture_pipeline(
        [probe, sample, query], [],
    )
    assert out == query.strip()
    assert not incomplete
    reads_prior = (
        "rows = previous_result.get('data') or []\n"
        "result = {'data': rows, '__return_direct__': True}\n"
    )
    merged, incomplete = compose.compose_capture_pipeline(
        [sample, reads_prior], [],
    )
    assert '_pipeline_rows' in merged
    assert "env['account.analytic.line']" in merged
    assert not incomplete
    compile(merged, '<skill>', 'exec')
    src = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(
        encoding='utf-8',
    )
    body = src.split('def compose_capture_code', 1)[1].split('\n    def ', 1)[0]
    assert 'return composed, pipeline_incomplete' in body


def test_a_step_the_sandbox_refused_is_not_captured():
    compose = _load()
    assert compose.log_run_failed(
        "ERROR (-32602): AST Validation Error: [PROHIBITED:DIR] Cannot use 'dir'.",
    )
    assert compose.log_run_failed('  ERROR (500): boom')
    assert not compose.log_run_failed('{"has_page_url": true}')
    assert not compose.log_run_failed('')
    assert not compose.log_run_failed(None)
    src = (_ROOT / 'common' / 'models' / 'chatboo_session.py').read_text(
        encoding='utf-8',
    )
    codes = src.split('def _relaxaicode_codes_for_turn', 1)[1].split(
        '\n    def ', 1,
    )[0]
    assert 'if log_run_failed(log.result_data):' in codes
    best = src.split('def _find_best_capture_log_for_turn', 1)[1].split(
        '\n    def ', 1,
    )[0]
    assert 'log_run_failed(log.result_data)' in best
