# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The file the installer leaves in a stack: its own copy, else ``common/``."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def deployed(stack, *parts):
    own = ROOT.joinpath('stacks', stack, 'pns_ai_chatboo', *parts)
    return own if own.exists() else ROOT.joinpath('common', *parts)
