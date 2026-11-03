# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""Seed money skills stay on the active company. Refunds stay out where the text says so."""
from pathlib import Path

_SKILLS = (
    Path(__file__).resolve().parents[1] / 'common' / 'ai' / 'skills' / 'system'
)


def _text(name):
    return (_SKILLS / name).read_text(encoding='utf-8')


def test_seed_money_skills_filter_the_active_company():
    for name in (
        'billing.py',
        'annual_billing.py',
        'dashboard.py',
        'credit_facility.py',
    ):
        src = _text(name)
        assert "env.company.id" in src
        assert "('company_id', '='," in src


def test_invoice_skills_still_count_out_invoice_only():
    for name in ('billing.py', 'annual_billing.py', 'dashboard.py'):
        src = _text(name)
        assert "('move_type', '=', 'out_invoice')" in src
        assert 'out_refund' not in src
