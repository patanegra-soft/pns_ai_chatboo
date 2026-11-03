# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com>
"""Display timezone: user, then company, then UTC."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import importlib.util


def _load():
    path = Path(__file__).resolve().parents[1] / 'common' / 'utils' / 'chatboo_display_time.py'
    spec = importlib.util.spec_from_file_location('chatboo_display_time', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_resolve_prefers_user_then_company_then_utc():
    dt = _load()
    assert dt.resolve_display_tz('Europe/Madrid', 'UTC', 'America/New_York') == 'Europe/Madrid'
    assert dt.resolve_display_tz('', None, 'Europe/Madrid') == 'Europe/Madrid'
    assert dt.resolve_display_tz(None, False, '') == 'UTC'


def test_format_wallclock_utc_to_madrid_summer():
    dt = _load()
    naive = datetime(2026, 8, 28, 9, 31, 8)
    assert dt.format_wallclock(naive, 'Europe/Madrid') == '2026-08-28 11:31:08'
    assert dt.format_wallclock(naive, 'UTC') == '2026-08-28 09:31:08'


def test_env_tz_candidates_reads_user_and_company():
    dt = _load()
    env = SimpleNamespace(
        context={'tz': 'Europe/Madrid'},
        user=SimpleNamespace(tz='Atlantic/Canary'),
        company=SimpleNamespace(
            partner_id=SimpleNamespace(tz='Europe/Lisbon'),
            resource_calendar_id=SimpleNamespace(tz='UTC'),
        ),
    )
    assert dt.env_tz_candidates(env) == (
        'Europe/Madrid', 'Atlantic/Canary', 'Europe/Lisbon',
    )
    assert dt.format_env_wallclock(
        env, datetime(2026, 8, 28, 9, 31, 8, tzinfo=timezone.utc),
    ) == '2026-08-28 11:31:08'
