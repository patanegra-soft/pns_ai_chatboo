# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""/forecast: an empty slash geocodes the company city; the forecast round
asks Open-Meteo for the span the parameters gave; the last round draws it."""
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
    name = 'Ejemplo Province'


class _Company:
    city = 'Villaejemplo'
    state_id = _State()


def _run(prev=None, **params):
    """Same keys the engine hands the sandbox for ``/forecast``."""
    scope = {'company': _Company(), 'user_lang': 'it_IT', 'previous_result': prev}
    for key, spec in _seed_schema().items():
        scope[key] = spec.get('default') if isinstance(spec, dict) else None
    scope.update(params)
    code = (_SKILLS / 'forecast.py').read_text(encoding='utf-8')
    exec(compile(code, '<forecast>', 'exec'), scope, scope)
    return scope['result']


def test_an_empty_forecast_geocodes_the_company_city():
    steps = _run().get('propose_steps') or []
    assert len(steps) == 1
    assert steps[0]['name'] == 'Villaejemplo (Ejemplo Province)'
    assert 'name=Villaejemplo&' in steps[0]['url']
    assert 'language=it' in steps[0]['url']


def test_the_company_region_picks_the_homonym_of_its_city():
    geo = {
        'url': 'https://geocoding-api.open-meteo.com/v1/search?name=Villaejemplo',
        'body': json.dumps({'results': [
            {'name': 'Villaejemplo', 'admin1': 'Big Region', 'country_code': 'AU',
             'latitude': 1, 'longitude': 2},
            {'name': 'Villaejemplo', 'admin1': 'Ejemplo Province', 'country_code': 'ES',
             'latitude': 3, 'longitude': 4},
        ]}),
    }
    steps = _run([geo])['propose_steps']
    assert 'latitude=3&longitude=4' in steps[0]['url']


def test_a_two_letter_code_is_not_a_piece_of_a_word():
    geo = {
        'url': 'https://geocoding-api.open-meteo.com/v1/search?name=Springfield',
        'body': json.dumps({'results': [
            {'name': 'Springfield', 'country_code': 'AU',
             'latitude': 1, 'longitude': 2},
            {'name': 'Springfield', 'country': 'Saudi Arabia',
             'latitude': 3, 'longitude': 4},
        ]}),
    }
    steps = _run([geo], place='Springfield (Saudi Arabia)')['propose_steps']
    assert 'latitude=3&longitude=4' in steps[0]['url']


def test_the_country_in_brackets_picks_the_homonym():
    geo = {
        'url': 'https://geocoding-api.open-meteo.com/v1/search?name=Springfield',
        'body': json.dumps({'results': [
            {'name': 'Springfield', 'country': 'Elsewhere', 'latitude': 1, 'longitude': 2},
            {'name': 'Springfield', 'country': 'Exampleland', 'latitude': 3, 'longitude': 4},
        ]}),
    }
    steps = _run([geo], place='Springfield (Exampleland)', start='2030-01-05', days=2)['propose_steps']
    assert 'latitude=3&longitude=4' in steps[0]['url']
    assert 'start_date=2030-01-05&end_date=2030-01-06' in steps[0]['url']


def test_the_last_round_draws_one_row_per_day():
    forecast = {
        'url': 'https://api.open-meteo.com/v1/forecast?latitude=3&city=Springfield',
        'body': json.dumps({'daily': {
            'time': ['2030-01-05', '2030-01-06'],
            'weathercode': [0, 61],
            'temperature_2m_max': [10, 12.5],
            'sunrise': ['2030-01-05T07:50', '2030-01-06T07:51'],
        }}),
    }
    result = _run([forecast], place='Springfield')
    assert [row['Sky'] for row in result['data']] == ['\u2600\ufe0f Clear', '\U0001f327\ufe0f Rain']
    assert result['data'][1]['Max'] == '12.5\u00b0'
    assert result['data'][0]['Sunrise'] == '07:50'
    assert 'Springfield' in result['summary']
