# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The deployed addon imports the models the stack lists, not ``common/``.

A model file that only ``common/models/__init__.py`` names is still
importable, so its plain functions work — but its ``_inherit`` class is
created after the registry is built and its methods never land on the model.
That is an ``AttributeError`` at runtime and nothing at install.
"""
from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_IMPORT = re.compile(r'^from \. import (\w+)', re.M)


def _imported(path):
    return _IMPORT.findall(path.read_text(encoding='utf-8'))


def test_both_stacks_import_the_same_models_as_common():
    common = _imported(_ROOT / 'common' / 'models' / '__init__.py')
    assert 'chatboo_canvas' in common
    for stack in ('owl1', 'owl2'):
        listed = _imported(
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'models'
            / '__init__.py'
        )
        missing = [name for name in common if name not in listed]
        extra = [name for name in listed if name not in common]
        assert not missing, '%s does not import: %s' % (stack, missing)
        assert not extra, '%s imports what common does not: %s' % (stack, extra)
        # Same order, so a model that inherits another keeps its place.
        assert listed == common


def test_every_model_file_in_common_is_imported():
    folder = _ROOT / 'common' / 'models'
    on_disk = sorted(
        path.stem for path in folder.glob('*.py')
        if path.stem != '__init__'
    )
    listed = sorted(_imported(folder / '__init__.py'))
    assert on_disk == listed
