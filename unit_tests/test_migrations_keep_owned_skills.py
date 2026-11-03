# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The seed does not hunt retired skills by name (PNS-68, code review)."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_seed_does_not_hunt_retired_names():
    seed = (
        _ROOT / 'common' / 'data' / 'chatboo_skill_data.xml'
    ).read_text(encoding='utf-8')
    assert 'import_from_module' in seed
    assert 'unlink_named_factory_skills' not in seed
    for name in ('flota', 'payroll', 'analisis_financiero', 'analisis-financiero'):
        assert name not in seed
