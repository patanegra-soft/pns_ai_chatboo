# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The form a card proposes: only fields the person may edit, nothing written."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest


class _UserError(Exception):
    pass


class _AccessError(Exception):
    pass


def _stub_odoo():
    odoo = types.ModuleType('odoo')
    odoo._ = lambda text, *args: text % args if args else text
    exceptions = types.ModuleType('odoo.exceptions')
    exceptions.UserError = _UserError
    exceptions.AccessError = _AccessError
    compat = types.ModuleType('odoo.addons.pns_base.utils.compat')
    compat.ODOO_VERSION = 14
    for name, mod in {
        'odoo': odoo,
        'odoo.exceptions': exceptions,
        'odoo.addons': types.ModuleType('odoo.addons'),
        'odoo.addons.pns_base': types.ModuleType('odoo.addons.pns_base'),
        'odoo.addons.pns_base.utils': types.ModuleType('odoo.addons.pns_base.utils'),
        'odoo.addons.pns_base.utils.compat': compat,
    }.items():
        sys.modules.setdefault(name, mod)


_stub_odoo()
_PATH = Path(__file__).resolve().parents[1] / 'common' / 'utils' / 'form_draft.py'
_spec = importlib.util.spec_from_file_location('form_draft', _PATH)
fd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fd)

_FIELDS = {
    'name': {'type': 'char', 'readonly': False},
    'state': {'type': 'selection', 'readonly': True,
              'selection': [('draft', 'Draft'), ('posted', 'Posted')]},
    'partner_id': {'type': 'many2one', 'readonly': True, 'relation': 'res.partner',
                   'states': {'draft': [['readonly', False]]}},
    'invoice_date': {'type': 'date', 'readonly': True,
                     'states': {'draft': [['readonly', False]]}},
    'line_ids': {'type': 'one2many', 'readonly': False},
    'kind': {'type': 'selection', 'readonly': False,
             'selection': [('a', 'A'), ('b', 'B')]},
}


class _Recordset:
    def __init__(self, model, ids):
        self._name = model
        self.ids = ids
        self.id = ids[0] if ids else False

    def __bool__(self):
        return bool(self.ids)

    def exists(self):
        return _Recordset(self._name, [i for i in self.ids if i < 100])

    def check_access_rights(self, operation):
        pass

    def check_access_rule(self, operation):
        pass


class _Model(_Recordset):
    _description = 'Journal Entry'

    def __init__(self, name):
        super().__init__(name, [])

    def browse(self, ids):
        return _Recordset(self._name, [ids] if isinstance(ids, int) else list(ids))

    def fields_get(self, attributes=None):
        return _FIELDS

    def default_get(self, names):
        return {'state': 'draft'}


class _Action:
    _name = 'ir.actions.act_window'
    res_model = 'account.move'
    name = 'Bills'
    context = "{'default_move_type': 'in_invoice'}"


class _Env(dict):
    def __init__(self):
        super().__init__({'account.move': _Model('account.move'),
                          'res.partner': _Model('res.partner')})

    def ref(self, xmlid, raise_if_not_found=True):
        return _Action() if xmlid == 'account.action_move_in_invoice_type' else None


def test_new_record_gets_only_editable_scalar_fields():
    action, context, dropped = fd.form_action(
        _Env(), action='account.action_move_in_invoice_type',
        values={
            'name': 'BILL-1', 'partner_id': 7, 'invoice_date': '2026-03-10',
            'state': 'posted', 'line_ids': [1], 'kind': 'zzz', 'missing': 1,
        },
    )
    assert action['res_model'] == 'account.move'
    assert action['target'] == 'new'
    assert action['context'] == "{'default_move_type': 'in_invoice'}"
    assert 'res_id' not in action
    assert context == {
        'default_name': 'BILL-1',
        'default_partner_id': 7,
        'default_invoice_date': '2026-03-10',
    }
    assert dropped == ['kind', 'line_ids', 'missing', 'state']


def test_a_record_that_does_not_exist_is_not_proposed():
    _, context, dropped = fd.form_action(
        _Env(), model='account.move', values={'partner_id': 500},
    )
    assert context == {}
    assert dropped == ['partner_id']


def test_an_existing_record_opens_to_edit_without_values():
    action, context, _ = fd.form_action(
        _Env(), model='account.move', res_id=5, values={'name': 'x'},
    )
    assert action['res_id'] == 5
    assert context == {'form_view_initial_mode': 'edit'}


def test_an_unknown_action_or_model_opens_nothing():
    with pytest.raises(_UserError):
        fd.form_action(_Env(), action='base.no_such_action')
    with pytest.raises(_UserError):
        fd.form_action(_Env(), model='no.such.model')


def test_no_sudo_in_the_form_draft():
    assert '.sudo(' not in _PATH.read_text(encoding='utf-8')
