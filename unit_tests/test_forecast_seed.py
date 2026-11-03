# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""An empty /forecast uses the company city: the seed defaults must let it."""
from __future__ import annotations

import json
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[1] / 'common' / 'ai' / 'skills' / 'system'


def _seed_schema():
    text = (_SKILLS / 'forecast.md').read_text(encoding='utf-8')
    for line in text.split('---', 2)[1].splitlines():
        if line.startswith('param_schema:'):
            return json.loads(line.split(':', 1)[1])
    raise AssertionError('forecast.md has no param_schema')


class _State:
    name = 'Sevilla'


class _Company:
    city = 'Dos Hermanas'
    state_id = _State()


def _run_empty_slash():
    """Same keys the engine hands the sandbox for ``/forecast`` with no args."""
    scope = {
        'arguments': None, 'lugar': None, 'fecha': None, 'company': _Company(),
        'user_lang': 'it_IT',
    }
    for key, spec in _seed_schema().items():
        if isinstance(spec, dict) and spec.get('default') not in (None, ''):
            scope[key] = spec['default']
    code = (_SKILLS / 'forecast.py').read_text(encoding='utf-8')
    exec(compile(code, '<forecast>', 'exec'), scope, scope)
    return scope['result']


def test_an_empty_forecast_geocodes_the_company_city():
    result = _run_empty_slash()
    steps = result.get('propose_steps') or []
    assert len(steps) == 1, result
    assert steps[0]['name'] == 'Dos Hermanas'
    assert 'name=Dos%20Hermanas' in steps[0]['url']
    assert 'language=it' in steps[0]['url']
