# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""/top-sales asks one question per turn, keeps what it knows in
``__skill_state__`` and stops asking once both answers are in."""
from __future__ import annotations

from pathlib import Path

_SRC = (
    Path(__file__).resolve().parents[1] / 'common' / 'ai' / 'skills' / 'system' / 'top_sales.py'
).read_text(encoding='utf-8')


class _Env(dict):
    def __contains__(self, key):
        return True


def _turn(arguments, state):
    scope = {'env': _Env(), 'arguments': arguments, 'skill_state': state}
    code = _SRC.replace(
        "_rows = _ranking(_state['what'], _from)",
        "_rows = [{'id': 1, 'Name': 'ACME', 'Sales': 1.0}]",
    )
    exec(compile(code, '<top_sales>', 'exec'), scope, scope)
    return scope['result']


def test_each_question_waits_for_the_answer():
    first = _turn('', {})
    assert first['__await_skill_args__'] is True
    assert first['__skill_state__'] == {}
    second = _turn('2', first['__skill_state__'])
    assert second['__await_skill_args__'] is True
    assert second['__skill_state__'] == {'what': 'product'}
    last = _turn('6', second['__skill_state__'])
    assert '__skill_state__' not in last
    assert '__await_skill_args__' not in last
    assert last['data'][0]['Name'] == 'ACME'


def test_a_wrong_number_asks_again():
    again = _turn('9', {})
    assert again['__skill_state__'] == {}
    assert again['__await_skill_args__'] is True


def test_both_answers_at_once():
    result = _turn('3 24', {})
    assert '__skill_state__' not in result
    assert result['summary'].startswith('Top salespeople')
