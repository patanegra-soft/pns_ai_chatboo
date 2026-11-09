# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 Patanegra Soft <https://patanegra.com>
"""The canvas is a page in its own tab, asked for the way a map is asked for."""
from __future__ import annotations

import json
from pathlib import Path
from _deployed import deployed

_ROOT = Path(__file__).resolve().parents[1]
_CONTEXTS = _ROOT / 'common' / 'ai' / 'contexts'
_SESSION = (
    _ROOT / 'common' / 'models' / 'chatboo_session.py'
).read_text(encoding='utf-8')
_CANVAS = (
    _ROOT / 'common' / 'models' / 'chatboo_canvas.py'
).read_text(encoding='utf-8')
_CANVAS_JOB = (
    _ROOT / 'common' / 'models' / 'chatboo_canvas_job.py'
).read_text(encoding='utf-8')
_JOB = (
    _ROOT / 'common' / 'models' / 'chatboo_job.py'
).read_text(encoding='utf-8')


def test_design_step_log_keeps_the_messages_and_the_page():
    step = _SESSION.split('def _log_design_step', 1)[1].split('\n    def ', 1)[0]
    assert "{'role': 'system', 'content': system or ''}" in step
    assert "{'role': 'user', 'content': prompt or ''}" in step
    assert "result_data={'content': [{'type': 'text', 'text': content}]}" in step
    ask = _SESSION.split('def _ask_design', 1)[1].split('\n    def ', 1)[0]
    assert 'audit, result, system, prompt,' in ask


def test_canvas_page_sandboxes_the_model_document():
    page = _CANVAS.split('def canvas_page', 1)[1].split('\ndef ', 1)[0]
    assert 'sandbox="allow-scripts allow-modals"' in page
    assert 'allow-same-origin' not in page
    assert 'html.escape' in page
    paint = _SESSION.split('def _paint_canvas', 1)[1].split('\n    @api.model', 1)[0]
    assert "need='design'" in paint
    assert 'inference_audit' in paint
    assert 'note_turn_side_usage' in paint
    assert "log_mode='accumulate' if turn else 'single'" in paint
    assert 'query_data' not in paint
    assert 'place_rows_on_page(' in paint
    assert 'Do not fetch' in _CANVAS
    assert 'pns-page-rows' in _CANVAS
    assert 'place_rows_on_page' in _CANVAS
    assert 'rows=material' in _CANVAS
    open_fn = _CANVAS.split('def open_page', 1)[1].split(
        'def _blocks_for_page', 1,
    )[0]
    assert 'Sample figures (shape only' in open_fn
    assert 'sample_figures_for_design' in open_fn
    assert 'reusable HTML template' in _CANVAS
    assert 'max_tokens=32768' in _SESSION
    assert '_shape_for_design' not in _CANVAS
    assert 'note_page_waiting' in open_fn
    assert open_fn.index('note_page_waiting') < open_fn.index('paint_canvas')
    assert 'page waits for rows' in open_fn
    assert "env['chatboo.session']" in open_fn
    pack = (_CONTEXTS / 'domain' / 'page_tab' / 'page_tab.xml').read_text(
        encoding='utf-8',
    )
    assert 'waits and uses the rows' in pack
    assert '#pns-page-rows' in pack
    assert 'the page card' in pack


def test_the_server_writes_the_rows_as_visible_html():
    """Design left EJEMPLO in const DATA and painted em-dashes. Not enough."""
    import sys
    import types

    odoo = types.ModuleType('odoo')
    odoo._ = lambda text: text
    sys.modules.setdefault('odoo', odoo)
    spec = __import__('importlib.util', fromlist=['spec_from_file_location'])
    loader = spec.spec_from_file_location(
        'chatboo_canvas_rows',
        _ROOT / 'common' / 'models' / 'chatboo_canvas.py',
    )
    mod = spec.module_from_spec(loader)
    loader.loader.exec_module(mod)
    rows = [{'Cliente': 'EJEMPLO INDUSTRIAL, SAU', 'Facturación': 4408.4}]
    empty = (
        '<html><body><h1>Top</h1><p>\u2014</p>'
        '<script>const DATA = [{"Cliente":"EJEMPLO INDUSTRIAL, SAU"}]</script>'
        '</body></html>'
    )
    out = mod.place_rows_on_page(empty, rows)
    assert 'EJEMPLO INDUSTRIAL, SAU' in out.split('<script>', 1)[0] + out.split(
        '</script>', 1,
    )[-1]
    assert '<td>4408.4</td>' in out
    slotted = '<html><body><section id="pns-page-rows"></section></body></html>'
    filled = mod.place_rows_on_page(slotted, rows)
    assert filled.index('EJEMPLO') < filled.index('</section>')
    assert mod.place_rows_on_page('<p>x</p>', []) == '<p>x</p>'
    blocks = [
        {'title': 'KPIs', 'data': [{'Metric': 'Sales', 'Value': 10, '_row_color': '#eee'}]},
        {'title': 'Months', 'data': [{'Month': 'Jan', 'Untaxed': 3}]},
    ]
    page = mod.place_rows_on_page('<html><body></body></html>', blocks)
    assert page.count('<table') == 2
    assert '<h2>KPIs</h2>' in page
    assert '<h2>Months</h2>' in page
    assert '_row_color' not in page
    assert '#eee' not in page
    assert 'Untaxed' in page
    assert page.find('KPIs') < page.find('Months')
    # Design opened a CSS rule and never a body: tables in <style> paint nothing.
    broken = (
        '<html><head><style>\n'
        '  .hf{<section id="pns-page-rows"></section>\n'
        '</style></head></html>'
    )
    rescued = mod.place_rows_on_page(broken, rows)
    assert '<body>' in rescued.lower()
    assert rescued.lower().find('<td>4408.4</td>') > rescued.lower().find('<body>')
    assert '.hf{<section' not in rescued
    assert 'EJEMPLO' in rescued.split('<style>', 1)[-1].split('</style>', 1)[-1]
    pretty = (
        '<html><head></head><body>'
        '<div id="chips"></div><div id="kpis"></div>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[];document.getElementById("chips").innerHTML="x"</script>'
        '</body></html>'
    )
    cleaned = mod.place_rows_on_page(pretty, rows)
    assert '<td>4408.4</td>' in cleaned
    assert 'EJEMPLO' in cleaned
    done = (
        '<html><body><p>EJEMPLO INDUSTRIAL, SAU · 4408.4</p>'
        '<script>void 0</script></body></html>'
    )
    kept = mod.place_rows_on_page(done, rows)
    assert '<script>void 0</script>' in kept
    assert kept.index('EJEMPLO') < kept.index('<script>')


def test_the_design_call_leaves_its_row_on_the_turn():
    """5VZC: two minutes of Opus and no trace of it in the AI History."""
    paint = _SESSION.split('def _ask_design', 1)[1].split('\n    def ', 1)[0]
    assert ') as audit:' in paint
    assert 'self._log_design_step(' in paint.split('if turn:', 1)[1]
    step = _SESSION.split('def _log_design_step', 1)[1].split('\n    def ', 1)[0]
    assert '_resolve_log_threading()' in step
    assert 'log_llm_inference(' in step
    assert "endpoint='llm_response'" in step
    assert "'Design %s in %.0f s (%d chars)'" in step


def test_paint_canvas_lives_on_the_session_class_already_loaded():
    """A second _inherit that the stack did not list never reached the model."""
    assert 'class ChatbooSessionCanvas' not in _CANVAS
    assert "_inherit = 'chatboo.session'" not in _CANVAS
    assert 'def _paint_canvas' in _SESSION
    assert 'def _page_url' in _SESSION


def test_the_page_is_a_url_on_the_result_not_a_popup():
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'static' / 'src'
        / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'static' / 'src'
        / 'js' / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    for src in (owl1, owl2):
        assert 'window.open(evt.canvas_url' not in src
        assert '/chatboo/' in src
    for rel in (
        'stacks/owl1/pns_ai_chatboo/static/src/css/chatboo_floating.css',
        'stacks/owl2/pns_ai_chatboo/static/src/css/chatboo_floating.css',
    ):
        css = (_ROOT / rel).read_text(encoding='utf-8')
        assert '.o_ai_page_link_card' in css
    job = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(
        encoding='utf-8',
    )
    assert 'canvas_chat_link' not in job
    assert 'decide_open_canvas' not in job
    # The tab is the address; no second window key is stored.
    for src in (_CANVAS, _SESSION):
        assert 'canvas_key' not in src
        assert 'page_target' not in src


def test_page_url_is_published_like_a_map_helper():
    body = _SESSION.split('def sandbox_helpers', 1)[1].split(
        '\n    def _page_url', 1,
    )[0]
    assert "getattr(self, '_' + name)" in body
    assert "'page_url': _wrap('page_url')" in body
    assert "'page_html': _wrap('page_html')" in body
    assert '_claim_page_turn(' in _SESSION
    assert "if 'page_tab' not in codes" in _SESSION
    assert 'note_page_wanted' in _SESSION
    assert not (_ROOT / 'common' / 'models' / 'chatboo_canvas_tool.py').exists()


def test_no_design_provider_is_a_soft_fail_and_never_borrowed():
    body = _SESSION.split('def _page_url', 1)[1].split(
        '\n    def canvas_public_url', 1,
    )[0]
    paint = _SESSION.split('def _paint_canvas', 1)[1].split('\n    @api.model', 1)[0]
    # Soft fail like a geocode miss: no page never aborts the turn.
    assert not [
        line for line in body.splitlines()
        if line.strip().startswith('raise ')
    ]
    for src in (body, paint):
        assert 'conversation' not in src
    # One need, one door: the page never asks for another role.
    assert paint.count("need=") == 1
    assert "need='design'" in paint
    pack = (_CONTEXTS / 'domain' / 'page_tab' / 'page_tab.xml').read_text(
        encoding='utf-8',
    )
    # The pack must not invent "no Design provider" when the url is empty.
    assert "result['notices']" not in pack
    assert 'another provider' in pack
    assert 'Do **not** invent a reason' in pack


def test_the_page_is_stored_off_the_sandbox_cursor():
    store = _SESSION.split('def _store_design', 1)[1].split('\n    def ', 1)[0]
    # caja A is READ ONLY and rolled back: writing the page there 404s the url.
    assert 'self.env.registry.cursor()' in store
    assert 'new_cr.commit()' in store
    assert 'new_cr.rollback()' in store
    assert 'new_cr.close()' in store
    assert 'self.write(' not in store
    # The revision travels back, because the sandbox cursor cannot see it.
    assert 'return rev' in store
    paint = _SESSION.split('def _paint_canvas', 1)[1].split('\n    @api.model', 1)[0]
    assert 'canvas_public_url(rev=rev)' in paint


def test_every_way_out_says_why_in_the_log():
    # The engine publishes the endpoint; the row is greyed out in its step.
    assert 'tool_name=CAPABILITY_SKIPPED' in _CANVAS
    assert '_resolve_log_threading()' in _CANVAS
    resolve = _CANVAS.split('def _session_of_this_turn', 1)[1].split(
        '\ndef ', 1,
    )[0]
    assert resolve.count('log_no_page(') == 3
    assert 'resolve_session_ref(env)' in resolve
    paint = _SESSION.split('def _paint_canvas', 1)[1].split('\n    @api.model', 1)[0]
    assert paint.count('log_no_page(') == 4
    assert 'except Exception as exc:' in paint


def test_the_helper_never_throws_into_the_sandbox():
    body = _SESSION.split('def _page_url', 1)[1].split(
        '\n    def canvas_public_url', 1,
    )[0]
    # The model wraps the call in its own try; an escaping exception is a
    # cause nobody can read afterwards.
    assert 'except Exception as exc:' in body
    assert 'log_no_page(' in body
    assert 'type(exc).__name__' in body


def test_the_when_is_a_turn_pack_not_the_identity():
    identity = (
        _CONTEXTS / 'domain' / 'self_chatboo' / 'self_chatboo.xml'
    ).read_text(encoding='utf-8')
    assert 'page_url' not in identity
    pack = (_CONTEXTS / 'domain' / 'page_tab' / 'page_tab.xml').read_text(
        encoding='utf-8',
    )
    assert '<code>page_tab</code>' in pack
    assert "'page_url': page_url(rows," in pack
    assert 'same' in pack.lower() and 'relaxaicode' in pack
    assert '__untrusted_html_preview__' in pack
    for name in ('discovery_page_tab.json', 'discovery_page_tab_es_ES.json'):
        row = json.loads((_CONTEXTS / 'discovery' / name).read_text(
            encoding='utf-8',
        ))
        assert row['tipo'] == 'discovery'
        assert row['target'] == 'page_tab'
        assert 'canvas' in row['triggers']


def _load_canvas_module():
    import importlib.util
    import sys
    import types

    odoo = types.ModuleType('odoo')
    odoo._ = lambda text: text
    sys.modules.setdefault('odoo', odoo)
    spec = importlib.util.spec_from_file_location(
        'chatboo_canvas_client', _ROOT / 'common' / 'models' / 'chatboo_canvas.py',
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fleet(count=17):
    photo = 'iVBORw0KGgo' + 'A' * 12000
    return [{
        'title': 'Fleet',
        'data': [
            {'Vehicle': 'Renault/KANGOO/%04d MKH' % (1000 + i), 'Brand': 'Renault',
             'image_128': photo, 'id': i + 1}
            for i in range(count)
        ],
    }]


def test_photos_do_not_eat_the_rows_design_sees():
    """17 vehicles with photos reached Design as 6: the JSON was cut at 80000."""
    mod = _load_canvas_module()
    blocks, images = mod.pictures_as_tokens(None, _fleet())
    assert len(images) == 17
    assert blocks[0]['data'][16]['image_128'] == 'pns-img:17'
    dumped, note = mod.figures_for_design(blocks)
    assert len(json.loads(dumped)[0]['data']) == 17
    assert note == 'Show all 17 rows.'
    sampled, sample_note = mod.sample_figures_for_design(blocks)
    assert len(json.loads(sampled)[0]['data']) == 3
    assert json.loads(sampled)[0]['keys'][0] == 'Vehicle'
    assert '17' in sample_note
    assert 'DATA.length' in sample_note
    assert 'pns-img:7' in mod.DESIGN_SYSTEM
    assert 'every row in DATA' in mod.DESIGN_SYSTEM
    for system in (mod.DESIGN_SYSTEM, mod.EDIT_SYSTEM):
        assert 'const DATA = the figures JSON from the prompt' in system
        assert 'same keys, no renamed columns' in system
        assert 'Do not write a figure, a row label or the page title' in system
        assert 'fallback label' in system
        assert 'month names' in system
        assert 'chip, button or filter' in system
        assert 'reusable HTML template' in system
        assert 'server always replaces' in system
        assert 'in the HTML, or in a script' not in system
    paint = _SESSION.split('def _paint_canvas', 1)[1].split('\n    def ', 1)[0]
    assert 'design_figures_centralized' in paint
    assert 'design_figure_leaks' in paint
    assert paint.index('design_figures_centralized') < paint.index('_store_design')
    assert 'captured=True' in paint
    assert 'kept the layout' in paint
    assert 'asking again' in paint
    assert 'baked these values outside' in paint
    assert 'is_document(raw)' in paint
    assert "mixed figures into the template; dropped" not in paint
    open_fn = _CANVAS.split('def open_page', 1)[1].split('def _blocks_for_page', 1)[0]
    assert '[:80000]' not in open_fn
    assert 'pictures_as_tokens(sessions.env' in open_fn
    assert 'swap_pictures(place_rows_on_page(' in _SESSION
    assert 'pictures_out(self.canvas_design, images)' in _SESSION
    assert 'strip_pictures' not in _SESSION


def test_design_gets_every_row_whatever_the_size():
    """No budget: the input to Design is never cut."""
    mod = _load_canvas_module()
    blocks = [{'title': 'Big', 'data': [
        {'Name': 'Row %d' % i, 'Note': 'y' * 2000} for i in range(3000)
    ]}]
    dumped, note = mod.figures_for_design(blocks)
    assert len(json.loads(dumped)[0]['data']) == 3000
    assert note == 'Show all 3000 rows.'
    sampled, sample_note = mod.sample_figures_for_design(blocks)
    assert len(json.loads(sampled)[0]['data']) == 3
    assert '3000' in sample_note
    assert 'BUDGET' not in _CANVAS
    assert '_MAX' not in _CANVAS
    assert 'These are' not in _CANVAS


def test_a_pretty_page_in_any_word_order_finds_the_page_tab():
    """II4T: «una bonita página» matched no trigger; the turn painted a bubble."""
    from importlib import util as spec
    from _engine_params import engine_file
    loader = spec.spec_from_file_location(
        'domain_index_page_tab',
        engine_file('common', 'utils', 'domain_index.py'),
    )
    di = spec.module_from_spec(loader)
    loader.loader.exec_module(di)
    found = _CONTEXTS / 'discovery'
    for name, sentence in (
        ('discovery_page_tab_es_ES.json',
         'hazme una bonita página con el balance de sumas y saldos'),
        ('discovery_page_tab.json',
         'make me a nice page with the trial balance'),
    ):
        row = json.loads((found / name).read_text(encoding='utf-8'))
        entry = {'code': row['target'], 'triggers': row['triggers'],
                 'priority': row['priority']}
        trial = {'code': 'trial_balance', 'triggers': ['balance'], 'priority': 50}
        codes = di.match_domains(sentence, [trial, entry])['codes']
        assert 'page_tab' in codes and 'trial_balance' in codes


def test_a_page_whose_script_draws_the_rows_keeps_its_controls():
    mod = _load_canvas_module()
    blocks, _images = mod.pictures_as_tokens(None, _fleet())
    data = json.dumps([{'plate': row['Vehicle']} for row in blocks[0]['data']])
    page = (
        '<html><head><style>section{display:block}</style></head><body>'
        '<header>Fleet</header><div id="chips"></div><div id="grid"></div>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=%s;'
        'document.getElementById("chips").innerHTML="x";</script>'
        '</body></html>' % data
    )
    out = mod.place_rows_on_page(page, blocks)
    assert '<div id="chips"></div>' in out
    assert 'document.getElementById("chips")' in out
    spare = out.split('<section id="pns-page-rows" hidden', 1)[1]
    assert spare.startswith(' style="display:none!important">')
    assert blocks[0]['data'][16]['Vehicle'] in spare.split('</section>', 1)[0]
    assert 'pns-page-rows-visible' not in out
    head = out.split('<head>', 1)[1]
    assert head.startswith('<script id="pns-page-rows-watch">')
    watch = head.split('</script>', 1)[0]
    assert 'addEventListener("error"' in watch
    assert 'addEventListener("load"' in watch
    assert blocks[0]['data'][0]['Vehicle'] in watch
    again = mod.place_rows_on_page(out, blocks)
    assert again.count('pns-page-rows-watch') == 1
    assert again.count('<section id="pns-page-rows"') == 1
    assert mod.place_rows_on_page(out, []) == out
    for system in (mod.DESIGN_SYSTEM, mod.EDIT_SYSTEM):
        assert 'never add one that only looks like it works' in system
        assert 'one failing control' in system
    assert 'still works after your change' in mod.EDIT_SYSTEM
    assert 'still works after your change' not in mod.DESIGN_SYSTEM


def test_a_page_with_six_of_seventeen_rows_gets_every_row():
    mod = _load_canvas_module()
    blocks, images = mod.pictures_as_tokens(None, _fleet())
    cards = ''.join(
        '<div class="card"><img src="%s"><b>%s</b> Renault</div>'
        % (row['image_128'], row['Vehicle'])
        for row in blocks[0]['data'][:6]
    )
    six = '<html><head></head><body>%s</body></html>' % cards
    page = mod.swap_pictures(mod.place_rows_on_page(six, blocks), images)
    for row in _fleet()[0]['data']:
        assert row['Vehicle'] in page
    assert 'pns-img:' not in page
    assert 'src="data:image/png;base64,iVBORw0KGgo' in page
    every = '<html><body>%s</body></html>' % ''.join(
        '<p>%s</p>' % row['Vehicle'] for row in blocks[0]['data']
    )
    assert mod.place_rows_on_page(every, blocks) == every
    kept = {}
    assert mod.pictures_out(page, kept).count('data:image') == 0
    assert mod.swap_pictures(mod.pictures_out(page, kept), kept) == page


def test_the_open_page_goes_to_design_with_tokens_and_comes_back_whole():
    mod = _load_canvas_module()
    a = 'data:image/png;base64,' + 'A' * 80
    b = 'data:image/jpeg;base64,' + 'B' * 80
    images = {'pns-img:1': a}
    page = '<body><img src="%s"><img src="%s"><img src="%s"></body>' % (a, b, b)
    text = mod.pictures_out(page, images)
    assert text == (
        '<body><img src="pns-img:1"><img src="pns-img:2">'
        '<img src="pns-img:2"></body>'
    )
    assert images == {'pns-img:1': a, 'pns-img:2': b}
    assert mod.swap_pictures(text, images) == page


def test_a_change_is_a_few_blocks_not_the_whole_page():
    mod = _load_canvas_module()
    page = (
        '<html><body><h1>Fleet</h1>\n<table><tr><th>Plate</th><th>VIN</th></tr>'
        '</table>\n<p class="note">old</p></body></html>'
    )
    answer = (
        'Here you go\n'
        '<<<<<<< FIND\n<h1>Fleet</h1>\n=======\n<h1>Fleet (17)</h1>\n>>>>>>> REPLACE\n'
        '<<<<<<< FIND\n<th>VIN</th>\n=======\n>>>>>>> REPLACE\n'
        '<<<<<<< FIND\n  <p class="note">old</p>  \n=======\n'
        '<p class="note">new</p>\n>>>>>>> REPLACE\n'
    )
    edits = mod.page_edits(answer)
    assert len(edits) == 3
    changed = mod.apply_edits(page, edits)
    assert '<h1>Fleet (17)</h1>' in changed
    assert '<th>VIN</th>' not in changed and '<th>Plate</th>' in changed
    assert '<p class="note">new</p>' in changed
    assert mod.apply_edits(page + '<h1>Fleet</h1>', edits) is None
    assert mod.apply_edits(page, [('<h2>none</h2>', 'x')]) is None
    assert mod.apply_edits(page, [('  ', 'x')]) is None
    assert mod.apply_edits(page, []) is None
    assert mod.page_edits('<html><body>whole</body></html>') == []
    assert mod.is_document('<!DOCTYPE html><html>')
    assert not mod.is_document('<<<<<<< FIND')
    for rule in ('pns-img:7', 'every row in DATA', 'print'):
        assert rule in mod.DESIGN_SYSTEM and rule in mod.EDIT_SYSTEM
    assert '<<<<<<< FIND' in mod.EDIT_SYSTEM
    assert 'exactly once' in mod.EDIT_SYSTEM


def test_a_change_asks_for_changes_and_lays_out_again_only_if_they_do_not_fit():
    paint = _SESSION.split('def _paint_canvas', 1)[1].split('\n    def ', 1)[0]
    edit_branch = paint.split('if page:\n                result', 1)[1].split(
        '            else:', 1,
    )[0]
    assert "self._ask_design(EDIT_SYSTEM, prompt, 'changed the page')" in paint
    assert 'apply_edits(page, edits)' in edit_branch
    assert 'edits or not is_document(raw)' in edit_branch
    assert 'self._ask_design(\n                        DESIGN_SYSTEM' in edit_branch
    ask = _SESSION.split('def _ask_design', 1)[1].split('\n    def ', 1)[0]
    assert "need='design'" in ask
    assert 'note_turn_side_usage(' in ask
    assert 'self._log_design_step(' in ask


def test_page_edit_changes_the_open_page_without_querying_again():
    helpers = _SESSION.split('def sandbox_helpers', 1)[1].split('\n    def ', 1)[0]
    assert "'page_edit': _wrap('page_edit')" in helpers
    method = _SESSION.split('def _page_edit', 1)[1].split('\n    def ', 1)[0]
    assert 'edit_page(self, instruction, rows)' in method
    edit = _CANVAS.split('def edit_page', 1)[1].split('\ndef ', 1)[0]
    assert "'no page is open to change'" in edit
    assert 'session._paint_canvas(instruction, new_page=False)' in edit
    assert 'open_page(sessions, rows, instruction, new=False)' in edit
    assert 'note_page_wanted(sessions.env)' in edit
    pack = (
        _CONTEXTS / 'domain' / 'page_tab' / 'page_tab.xml'
    ).read_text(encoding='utf-8')
    assert "page_edit('what to change on the page')" in pack
    assert 'without\n  rows' in pack
    assert 'reusable template' in pack
    assert 'fills `const DATA`' in pack


def test_only_the_frame_scrolls():
    """An inline iframe leaves a few pixels below it and the shell scrolls too."""
    mod = _load_canvas_module()
    shell = mod.canvas_page('<html><body>page</body></html>', 'Title')
    assert 'html,body{margin:0;height:100%;overflow:hidden}' in shell
    assert 'iframe{display:block;' in shell


def test_an_open_page_keeps_its_pack_on_every_turn():
    """A follow-up that names only the data still learns about ``page_edit``."""
    mod = _load_canvas_module()

    class Session:
        def __init__(self, open_, design):
            self.canvas_open = open_
            self.canvas_design = design

    assert mod.has_open_page(Session(True, '<html>page</html>'))
    assert not mod.has_open_page(Session(True, '  '))
    assert not mod.has_open_page(Session(False, '<html>page</html>'))
    edit = _CANVAS.split('def edit_page', 1)[1].split('\ndef ', 1)[0]
    assert 'if not has_open_page(session):' in edit
    held = _SESSION.split('def _held_domain_codes', 1)[1].split('\n    def ', 1)[0]
    assert "return ['page_tab'] if has_open_page(self) else []" in held
    request = (
        _ROOT / 'common' / 'models' / 'chatboo_async_request.py'
    ).read_text(encoding='utf-8')
    assert 'held_domain_codes = self.session_id._held_domain_codes()' in request
    assert 'held_domain_codes=held_domain_codes,' in request


def test_only_pictures_become_tokens():
    mod = _load_canvas_module()
    pdf = 'JVBERi0xLjQK' + 'A' * 200
    blocks, images = mod.pictures_as_tokens(None, [{
        'title': '', 'data': [{'doc': pdf, 'url': '/web/image/res.partner/1/image_128',
                               'name': 'x'}],
    }])
    assert images == {}
    assert blocks[0]['data'][0]['doc'] == pdf
    assert blocks[0]['data'][0]['url'] == '/web/image/res.partner/1/image_128'


def test_the_bubble_tables_reach_the_page_as_scalars():
    mod = _load_canvas_module()
    blocks = mod.tables_from_client([
        {'title': 'Top', 'rows': [
            {'Cliente': 'ACME', 'Total': 10.5, 'Nested': {'x': 1}},
        ]},
        {'title': 'Empty', 'rows': []},
        'junk',
        {'rows': 'not a list'},
    ])
    assert blocks == [{
        'title': 'Top',
        'data': [{'Cliente': 'ACME', 'Total': 10.5, 'Nested': "{'x': 1}"}],
    }]
    assert mod.tables_from_client(None) == []
    many = mod.tables_from_client([{'rows': [
        {'n': i, 'long': 'x' * 5000} for i in range(5000)
    ]} for _t in range(20)])
    assert len(many) == 20
    assert len(many[0]['data']) == 5000
    assert len(many[0]['data'][0]['long']) == 5000


def test_the_canvas_button_checks_the_owner_and_leaves_the_request():
    for stack in ('owl1', 'owl2'):
        ctrl = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
        ).read_text(encoding='utf-8')
        own = ctrl.split('def _own_session', 1)[1].split('\n    def ', 1)[0]
        assert "('user_id', '=', request.env.uid)" in own
        assert '.search([' in own
        for route in ('/chatboo/canvas/build', '/chatboo/canvas/running'):
            body = ctrl.split("'%s'" % route, 1)[1].split('@http.route', 1)[0]
            assert 'self._user_may_use_chatboo()' in body
            assert 'self._own_session(session_id)' in body
            assert '.sudo()' not in body
        for route in ('/chatboo/canvas/state', '/chatboo/canvas/cancel'):
            body = ctrl.split("'%s'" % route, 1)[1].split('@http.route', 1)[0]
            assert 'self._user_may_use_chatboo()' in body
            assert 'self._own_canvas_job(job_id)' in body
            assert '.sudo()' not in body
        own_job = ctrl.split('def _own_canvas_job', 1)[1].split('\n    def ', 1)[0]
        assert "('user_id', '=', request.env.uid)" in own_job
        assert "data['canvas_available'] = self._canvas_available()" in ctrl
    available = _SESSION.split('def canvas_available', 1)[1].split('\n    def ', 1)[0]
    assert "need='design'" in available
    assert "_inherit = 'chatboo.job.mixin'" in _CANVAS_JOB
    start = _CANVAS_JOB.split('def _start', 1)[1].split('\n    def ', 1)[0]
    assert 'tables_from_client(tables)' in start
    assert start.index('_live_for(session)') < start.index('job._spawn()')
    assert start.index('self.env.cr.commit()') < start.index('job._spawn()')
    process = _CANVAS_JOB.split('def _process', 1)[1].split('\n    def ', 1)[0]
    assert 'chatboo_canvas_job=self.id' in process
    assert 'open_page(' in process
    assert process.index('_start_heartbeat()') < process.index('open_page(')
    assert process.index('_stop_heartbeat(beat)') < process.index('_is_cancel_requested()')
    close = _CANVAS_JOB.split('def _close', 1)[1].split('\n    def ', 1)[0]
    assert '_get_registry(self.env.cr.dbname).cursor()' in close
    for gone in ('canvas_build_started', 'canvas_build_error', 'CANVAS_BUILD_MINUTES',
                 'def _spawn_canvas_build', 'def _set_canvas_build',
                 'def build_canvas_from_tables', 'def canvas_build_state'):
        assert gone not in _SESSION.split('_FOSSIL_COLUMNS = ', 1)[1].split('\n', 1)[1]
    init = _SESSION.split('    def init(self):', 1)[1].split('\n    @api.model', 1)[0]
    assert 'DROP COLUMN IF EXISTS' in init
    acl = (_ROOT / 'common' / 'security' / 'ir.model.access.csv').read_text(encoding='utf-8')
    assert 'model_chatboo_canvas_job,base.group_user,1,0,0,0' in acl
    rules = (_ROOT / 'common' / 'security' / 'security.xml').read_text(encoding='utf-8')
    rule = rules.split('id="chatboo_canvas_job_user_rule"', 1)[1].split('</record>', 1)[0]
    assert "[('user_id', '=', user.id)]" in rule
    cron = (_ROOT / 'common' / 'models' / 'chatboo_async_request.py').read_text(
        encoding='utf-8').split('def cron_maintenance', 1)[1].split('\n    def ', 1)[0]
    assert "self.env['chatboo.canvas.job']" in cron


def test_a_page_in_the_making_shows_the_dots_and_can_be_cancelled():
    charts = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
    ).read_text(encoding='utf-8')
    paint = charts.split('function paintCanvasButton', 1)[1].split('\n    function ', 1)[0]
    assert 'btn.disabled' not in paint
    assert 'o_chatboo_typing' in paint
    assert 'innerHTML' not in paint
    assert 'label("canvasCancel")' in paint
    start = charts.split('function startCanvas', 1)[1].split('\n    function ', 1)[0]
    assert 'cancelCanvas(key, job)' in start
    assert start.count('if (job.cancelled)') == 2
    assert 'cancelCanvasJob(job.jobId)' in start
    cancel = charts.split('function cancelCanvas', 1)[1].split('\n    function ', 1)[0]
    assert 'canvasHost.confirmCancel(function ()' in cancel
    assert '"/chatboo/canvas/cancel"' not in cancel
    drop = charts.split('function dropCanvas', 1)[1].split('\n    function ', 1)[0]
    assert 'cancelCanvasJob(job.jobId)' in drop
    owl2 = (
        _ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'static' / 'src' / 'js' / 'chatboo_app.js'
    ).read_text(encoding='utf-8')
    asks = owl2.split('confirmCancel:', 1)[1].split('} : null);', 1)[0]
    assert 'this.dialog.add(ConfirmationDialog' in asks
    assert '_t("Yes, cancel")' in asks and '_t("Keep waiting")' in asks
    owl1 = (
        _ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
        / 'chatboo_component_v2.js'
    ).read_text(encoding='utf-8')
    asks = owl1.split('confirmCancel:', 1)[1].split('} : null);', 1)[0]
    assert "if (confirm(_t('Cancel the page in progress? It will not be built.')))" in asks
    for stack in ('owl1', 'owl2'):
        assert (
            deployed(stack, 'static', 'src', 'js', 'chatboo_charts.js')
        ).read_text(encoding='utf-8') == charts
    follow = charts.split('function followCanvas', 1)[1].split('\n    function ', 1)[0]
    assert follow.count('if (job.cancelled)') == 2
    assert '"/chatboo/canvas/state", { job_id: jobId }' in charts
    cancel_job = charts.split('function cancelCanvasJob', 1)[1].split('\n    function ', 1)[0]
    assert '"/chatboo/canvas/cancel"' in cancel_job and 'job_id: jobId' in cancel_job
    resume = charts.split('function resumeCanvas', 1)[1].split('\n    function ', 1)[0]
    assert '"/chatboo/canvas/running"' in resume
    assert 'followCanvas(job)' in resume
    mount = charts.split('function mountCanvasButtons', 1)[1].split('\n    function ', 1)[0]
    assert 'resumeCanvas()' in mount
    paint_page = _SESSION.split('def _paint_canvas', 1)[1].split('\n    def ', 1)[0]
    assert paint_page.index('_canvas_build_cancelled()') < paint_page.index('_store_design(')
    cancelled = _SESSION.split('def _canvas_build_cancelled', 1)[1].split('\n    def ', 1)[0]
    assert "self.env['chatboo.canvas.job'].browse(job_id)._is_cancel_requested()" in cancelled
    request_cancel = _JOB.split('def request_cancel', 1)[1].split('\n    def ', 1)[0]
    assert request_cancel.index('self.user_id.id != self.env.uid') < request_cancel.index('sudo()')
    for stack, app, po in (
        ('owl1', 'chatboo_component_v2.js', 'es.po'),
        ('owl2', 'chatboo_app.js', 'es_ES.po'),
    ):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
        js = (base / 'static' / 'src' / 'js' / app).read_text(encoding='utf-8')
        assert 'canvasCancel: _t("Building the page. Click to cancel.")' in js
        catalog = (base / 'i18n' / po).read_text(encoding='utf-8')
        assert (
            'msgid "Building the page. Click to cancel."\n'
            'msgstr "Creando la página. Pulsa para cancelar."'
        ) in catalog


def test_the_bubble_shows_one_view_and_its_buttons():
    charts = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
    ).read_text(encoding='utf-8')
    for gone in ('Ver datos', 'Ocultar gráfico', 'Ocultar datos',
                 'mountChartTableShell', 'shouldAutoMountChartUi'):
        assert gone not in charts
    to_chart = charts.split('function showChartView', 1)[1].split('function ', 1)[0]
    assert 'setTableCollapsed(block, true)' in to_chart
    to_table = charts.split('function showTableView', 1)[1].split('function ', 1)[0]
    assert 'hideChart(block)' in to_table
    assert 'setTableCollapsed(block, false)' in to_table
    toggle = charts.split('function updatePrimaryToggleLabel', 1)[1].split(
        'function showChartView', 1,
    )[0]
    assert 'o_chatboo_chart_controls' in toggle
    assert 'label("data")' in toggle and 'label("chart")' in toggle
    mount = charts.split('function mountCanvasButton(block)', 1)[1].split(
        'function mountCanvasButtons', 1,
    )[0]
    assert 'if (!canvasHost)' in mount
    assert 'canvasButtonIn(block)' in mount
    assert '!== block' not in mount
    assert 'paintCanvasRow(row, job)' in charts
    assert 'tables: tables' in charts
    assert 'bar.insertBefore(btn, bar.firstChild)' in mount
    hydrate = charts.split('function hydrateRoot', 1)[1].split(
        'function destroyInRoot', 1,
    )[0]
    assert 'mountCanvasButtons(root)' in hydrate
    for stack, app, po in (
        ('owl1', 'chatboo_component_v2.js', 'es.po'),
        ('owl2', 'chatboo_app.js', 'es_ES.po'),
    ):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
        js = (base / 'static' / 'src' / 'js' / app).read_text(encoding='utf-8')
        assert 'canvas_available' in js
        assert 'charts.setCanvas(available ?' in js
        assert '_t("Data")' in js
        catalog = (base / 'i18n' / po).read_text(encoding='utf-8')
        assert 'msgid "Data"\nmsgstr "Datos"' in catalog
        assert 'msgid "Open page"\nmsgstr "Abrir página"' in catalog


def test_a_page_laid_out_before_its_name_takes_the_name_later():
    """5VZC: page_url(rows) ran before result['summary']; every tab said Canvas."""
    open_fn = _CANVAS.split('def open_page', 1)[1].split('\ndef _name_it_later', 1)[0]
    assert 'if url and not name:' in open_fn
    assert '_name_it_later(sessions.env, session, url)' in open_fn
    later = _CANVAS.split('def _name_it_later', 1)[1].split('\ndef ', 1)[0]
    assert 'note_page_untitled(env, retitle)' in later
    assert 'session._store_title(title)' in later
    store = _SESSION.split('def _store_title', 1)[1].split('\n    def ', 1)[0]
    assert 'self.env.registry.cursor()' in store
    assert "if (session.canvas_title or '').strip():" in store
    assert "session.write({'canvas_title': title})" in store


def test_a_captured_page_opens_without_design_and_drops_that_days_figures():
    mod = _load_canvas_module()
    baked = (
        '<html><body><section id="pns-page-rows">'
        '<p>Renault/KANGOO/1001</p></section></body></html>'
    )
    template = mod.as_page_template(baked)
    assert 'Renault/KANGOO/1001' not in template
    assert 'id="pns-page-rows"' in template
    wrapped = mod.wrap_captured_page('result = {"data": []}\n', baked, 'Fleet')
    assert 'page_html(_page_template, result, _page_title)' in wrapped
    assert 'result["title"] = _page_title' in wrapped
    assert 'Renault/KANGOO/1001' not in wrapped
    assert '_ask_design' not in wrapped
    html_fn = _SESSION.split('def _page_html', 1)[1].split('\n    def _page_edit', 1)[0]
    assert '_ask_design' not in html_fn
    assert 'skill_publish_check' in html_fn
    assert 'place_rows_on_page' in html_fn
    assert 'html = sync_canvas_title_phrases(html, title)' in html_fn
    after_sync = html_fn.split(
        'html = sync_canvas_title_phrases(html, title)', 1,
    )[1]
    assert 'place_rows_on_page' in after_sync
    assert 'captured=True' in after_sync
    wrap = _SESSION.split('def _wrap_open_page', 1)[1].split('\n    def ', 1)[0]
    assert 'canvas_design' in wrap
    assert 'code_touches_page(code)' in wrap
    assert 'wrap_captured_page' in wrap
    assert 'captured_page_is_reusable' not in wrap


def test_a_table_turn_in_a_session_with_a_page_is_not_a_page_skill():
    mod = _load_canvas_module()
    assert not mod.code_touches_page(
        "rows = env['res.partner'].search_read([], ['name'])\n"
        "result = {'data': rows}\n",
    )
    assert mod.code_touches_page("url = page_url(rows, 'x', new=True)\n")
    assert mod.code_touches_page("url = page_edit('more tabs')\n")
    assert mod.code_touches_page(
        "_opened = page_html(_page_template, result, _page_title)\n",
    )
    assert not mod.code_touches_page("text = 'page_url(rows)'\n")
    wizard = (
        Path(__file__).resolve().parent.parent
        / 'common' / 'models' / 'skill_capture_wizard.py'
    ).read_text(encoding='utf-8')
    gate = wizard.split('def _assert_captured_page_reusable', 1)[1].split(
        '\n    def ', 1,
    )[0]
    assert 'canvas_design' not in gate
    assert (
        'if self._opens_saved_page() and self._page_has_param_rows():'
    ) in wizard


def test_saving_a_skill_keeps_designs_chrome():
    """A new Design pass would throw away the page they liked."""
    mod = _load_canvas_module()
    baked = (
        '<html><body>'
        '<p>Últimos 12 meses</p>'
        '<section id="pns-page-rows"></section>'
        '</body></html>'
    )
    title = 'Rentabilidad (Últimos 24 meses)'
    wrapped = mod.wrap_captured_page('result = {"data": []}\n', baked, title)
    stored = wrapped.split('_page_title = ', 1)[0]
    assert 'Últimos 12 meses' in stored
    assert 'Últimos 24 meses' not in stored
    assert 'Rentabilidad (Últimos 24 meses)' in wrapped
    assert 'page_html(_page_template, result, _page_title)' in wrapped
    assert '_ask_design' not in wrapped
    opened = mod.sync_canvas_title_phrases(baked, title)
    assert 'Últimos 24 meses' in opened
    assert 'Últimos 12 meses' not in opened


def test_captured_page_binds_this_runs_figures_not_yesterdays():
    """Same labels (REC, Sevilla) must not keep yesterday's amounts."""
    mod = _load_canvas_module()
    old = (
        '<html><body>'
        '<p>Últimos 12 meses</p>'
        '<div class="kpi">REC Sevilla 100</div>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":100}];'
        '</script>'
        '</body></html>'
    )
    title = 'Rentabilidad (Últimos 24 meses)'
    rows = [{'Área': 'REC', 'Provincia': 'Sevilla', 'Importe': 250}]
    html = mod.sync_canvas_title_phrases(old, title)
    out = mod.place_rows_on_page(html, rows, captured=True)
    assert 'Últimos 24 meses' in out
    assert '"Importe": 250' in out
    assert 'Importe": 100' not in out
    assert '<td>250</td>' in out
    other = (
        '<html><body>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[{"plate":"X","km":10}];</script>'
        '</body></html>'
    )
    rebound = mod.place_rows_on_page(
        other, [{'Vehicle': 'Y', 'Mileage': 20}], captured=True,
    )
    assert '<td>20</td>' in rebound
    assert '"Mileage": 20' in rebound
    assert 'plate' not in rebound.split('<script>', 1)[1].split('</script>', 1)[0]
    unnamed = (
        '<html><body>'
        '<section id="pns-page-rows"></section>'
        '<script>const ROWS=[{"plate":"X","km":10}];</script>'
        '</body></html>'
    )
    cleared = mod.place_rows_on_page(
        unnamed, [{'Vehicle': 'Y', 'Mileage': 20}], captured=True,
    )
    assert '<td>20</td>' in cleared
    assert 'const ROWS=[]' in cleared
    assert 'pns-page-rows-visible' in cleared


def test_design_without_const_data_is_rejected():
    """A page that mixed figures into the markup cannot be a skill later."""
    mod = _load_canvas_module()
    rows = [{'Área': 'REC', 'Provincia': 'Sevilla', 'Importe': 250}]
    ok = (
        '<html><body><h1>Rentabilidad</h1>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":250}];'
        '</script></body></html>'
    )
    assert mod.design_figures_centralized(ok, rows)
    assert not mod.design_figures_centralized(
        '<html><body><p>REC 250</p></body></html>', rows,
    )
    mixed = (
        '<html><body><p>REC Sevilla 250</p>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":250}];'
        '</script></body></html>'
    )
    assert not mod.design_figures_centralized(mixed, rows)
    empty = (
        '<html><body><h1>Rentabilidad</h1>'
        '<script>const DATA=[];</script></body></html>'
    )
    assert not mod.design_figures_centralized(empty, rows)
    css_only = (
        '<html><head><style>.grid{width:12px}</style></head><body>'
        '<p class="col-12">Rentabilidad</p>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":250}];'
        '</script></body></html>'
    )
    assert mod.design_figures_centralized(css_only, rows)
    assert mod.design_figures_centralized(ok, [])
    titled = (
        '<html><body><h1>Rentabilidad (Últimos 24 meses)</h1>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":250}];'
        '</script></body></html>'
    )
    assert not mod.design_figures_centralized(
        titled, rows, 'Rentabilidad (Últimos 24 meses)',
    )
    chips = (
        '<html><body><div id="chips"></div>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":250}];'
        '</script></body></html>'
    )
    assert mod.design_figures_centralized(chips, rows)
    buttons = (
        '<html><body>'
        '<button type="button">Sevilla</button>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":250}];'
        '</script></body></html>'
    )
    assert not mod.design_figures_centralized(buttons, rows)
    attr = (
        '<html><body>'
        '<button type="button" data-area="REC"></button>'
        '<section id="pns-page-rows"></section>'
        '<script>const DATA=[{"Área":"REC","Provincia":"Sevilla","Importe":250}];'
        '</script></body></html>'
    )
    assert not mod.design_figures_centralized(attr, rows)
    fallback = mod._page_for_rows([{'title': 'R', 'data': rows}])
    assert 'const DATA=' in fallback
    assert '"Importe": 250' in fallback
    assert mod.captured_page_is_reusable(fallback, rows)
    assert not mod.captured_page_is_reusable(mixed, rows)
    assert not mod.captured_page_is_reusable(
        titled, rows, 'Rentabilidad (Últimos 24 meses)',
    )
    fictional = (
        '<html><body><h1></h1><div id="chips"></div>'
        '<section id="pns-page-rows"></section>'
        '<script>const TITLE="Sample";'
        'const DATA=[{"Área":"NORTE","Provincia":"Madrid","Importe":1}];'
        'document.getElementById("chips").innerHTML="x";</script>'
        '</body></html>'
    )
    assert mod.design_figures_centralized(fictional, rows, 'Rentabilidad')
    filled = mod.place_rows_on_page(
        fictional, rows, captured=True, title='Rentabilidad por Área',
    )
    assert '"Importe": 250' in filled
    assert 'NORTE' not in filled
    assert 'Madrid' not in filled
    script = filled.split('<script>', 1)[1].split('</script>', 1)[0]
    assert 'Rentabilidad por Área' in script
    assert 'id="chips"' in filled
    assert 'pns-page-rows-visible' not in filled
    baked_sample = fictional.replace(
        '<div id="chips"></div>',
        '<button type="button">Madrid</button>',
    )
    assert not mod.design_figures_centralized(baked_sample, rows)
    slider = (
        '<html><head><style>:root{--bg:#fff}'
        'html[data-theme="dark"]{--bg:#111}</style></head><body>'
        '<button type="button" class="play" aria-label="Play">▶</button>'
        '<input type="range" id="slider" min="0" max="0" value="0" step="1">'
        '<div id="periodNow"></div>'
        '<section id="pns-page-rows"></section>'
        '<script>const TITLE="Rentabilidad";'
        'const DATA=[{"Periodo":"2024-T4","Area_Cod":"INC",'
        '"Area_Nombre":"[INC] Incidencias","Area_Color":"#FF0000",'
        '"Area_Texto":"#FFFFFF","Provincia":"Granada","Ingresos":0.0,'
        '"Gastos":0.0,"Margen":0.0}];</script>'
        '</body></html>'
    )
    live = [
        {'Periodo': '2024-T4', 'Area_Cod': 'INC',
         'Area_Nombre': '[INC] Incidencias', 'Area_Color': '#FF0000',
         'Area_Texto': '#FFFFFF', 'Provincia': 'Granada', 'Ingresos': 0.0,
         'Gastos': 18167.0, 'Margen': -18167.0},
    ]
    assert mod.design_figures_centralized(slider, live, 'Rentabilidad')
    bound = mod.place_rows_on_page(
        slider, live, captured=True, title='Rentabilidad',
    )
    assert '18167' in bound
    assert 'pns-page-rows-visible' not in bound
    assert 'id="slider"' in bound
    leftover = (
        '<html><body><div id="periodNow"></div>'
        '<section id="pns-page-rows"></section>'
        '<script>const TITLE="Rentabilidad";'
        'const DATA=[{"Periodo":"2025-01","Area":"INC"}];'
        'const PERIODS=["2025-01"];</script>'
        '</body></html>'
    )
    later = [{'Periodo': '2024-T4', 'Area': 'INC'}]
    assert not mod.design_figures_centralized(leftover, later)
    assert '2025-01' in mod.design_figure_leaks(leftover, later)
    assert not mod.captured_page_is_reusable(leftover, later)
    fallback = leftover.replace(
        'const PERIODS=["2025-01"];',
        'const P=r.provincia||"Sin provincia";',
    ).replace(
        'const DATA=[{"Periodo":"2025-01","Area":"INC"}];',
        'const DATA=[{"Periodo":"2025-01","Area":"INC",'
        '"Provincia":"Sin provincia"}];',
    )
    assert not mod.design_figures_centralized(
        fallback, [{'Periodo': '2024-T4', 'Area': 'INC',
                    'Provincia': 'Sevilla'}],
    )
    assert 'Sin provincia' in mod.design_figure_leaks(
        fallback, [{'Periodo': '2024-T4', 'Area': 'INC',
                    'Provincia': 'Sevilla'}],
    )
    derived = leftover.replace(
        'const PERIODS=["2025-01"];',
        'const PERIODS=DATA.map(function(r){return r.Periodo;});',
    )
    assert mod.design_figures_centralized(derived, later)
    painted = derived.replace(
        '<script>',
        '<script id="pns-page-rows-watch">var ROWS=[["2025-01"]];</script>'
        '<script>',
    )
    assert mod.design_figures_centralized(painted, later)


def test_canvas_chrome_follows_the_title_not_the_baked_period():
    """Design painted 12 meses; the slash already named the page 24."""
    mod = _load_canvas_module()
    baked = (
        '<html><head><style>.grid{width:12px}</style></head>'
        '<body>'
        '<h1>Rentabilidad por Áreas</h1>'
        '<p class="col-12">Últimos 12 meses - 163 combinaciones</p>'
        '<script>const N=12;</script>'
        '</body></html>'
    )
    title = 'Rentabilidad por Áreas de Negocio y Provincia (Últimos 24 meses)'
    out = mod.sync_canvas_title_phrases(baked, title)
    assert 'Últimos 24 meses' in out
    assert 'Últimos 12 meses' not in out
    assert '163 combinaciones' in out
    assert 'width:12px' in out
    assert 'class="col-12"' in out
    assert 'const N=12;' in out
    assert mod.sync_canvas_title_phrases(baked, '') == baked
    assert mod.sync_canvas_title_phrases(baked, 'Fleet') == baked


def test_a_captured_page_does_not_call_design_again():
    mod = _load_canvas_module()
    baked = '<html><body><section id="pns-page-rows"></section></body></html>'
    source = (
        "rows = [{'Área': 'REC', 'Provincia': 'Sevilla'}]\n"
        "instruction = (\n"
        "    'Página interactiva y vistosa con la rentabilidad'\n"
        ")\n"
        "url = page_url(rows, instruction, new=True)\n"
        "result = {'data': rows, 'page_url': url}\n"
    )
    cleaned = mod.without_design_page_calls(source)
    assert 'page_url(' not in cleaned
    assert "url = ''" in cleaned
    assert 'rows = ' in cleaned
    wrapped = mod.wrap_captured_page(source, baked, 'Rentabilidad')
    assert 'page_url(' not in wrapped
    assert '_page_rows = (rows)\nurl = \'\'' in wrapped
    compile(wrapped, '<skill>', 'exec')
    again = mod.wrap_captured_page(
        source + "\npage_html(_page_template, result, _page_title)\n",
        baked,
        'Rentabilidad',
    )
    assert 'page_url(' not in again


def test_a_captured_page_gets_the_rows_the_turn_put_on_it():
    """``result['data']`` is the bubble preview; the page had every row."""
    mod = _load_canvas_module()
    baked = '<html><body><section id="pns-page-rows"></section></body></html>'
    source = (
        "rows = [{'Periodo': '2026-%02d' % m} for m in range(1, 13)]\n"
        "if rows:\n"
        "    href = page_url(\n"
        "        rows, 'Rentabilidad', new=True,\n"
        "    )\n"
        "result = {'page_url': href, 'data': rows[:2]}\n"
    )
    wrapped = mod.wrap_captured_page(source, baked, 'Rentabilidad')
    assert 'page_url(' not in wrapped
    assert '    _page_rows = (rows)\n    href = ' in wrapped
    assert (
        'page_html(_page_template, _page_rows if _page_rows is not None '
        'else result, _page_title)'
    ) in wrapped
    seen = {}

    def page_html(_html, rows, _title):
        seen['rows'] = rows
        return '/chatboo/canvas/1?rev=1'

    scope = {'page_html': page_html}
    exec(compile(wrapped, '<skill>', 'exec'), scope, scope)
    assert len(seen['rows']) == 12
    assert scope['result']['page_url'] == '/chatboo/canvas/1?rev=1'
    edited = mod.without_design_page_calls(
        "url = page_edit('more', rows=data)\n", keep_rows=True,
    )
    assert edited == "_page_rows = (data)\nurl = ''\n"
    nested = mod.without_design_page_calls(
        "url = page_url([r for r in rows if r.get('a', ')')], 'x, y')\n",
        keep_rows=True,
    )
    assert nested == (
        "_page_rows = ([r for r in rows if r.get('a', ')')])\nurl = ''\n"
    )


def test_the_tab_is_named_after_the_answer():
    mod = _load_canvas_module()
    blocks = [{'title': '', 'data': [1]}, {'title': 'Second', 'data': [2]}]
    assert mod.page_title([], blocks, '  Top 5  clientes ') == 'Top 5 clientes'
    assert mod.page_title({'title': 'From result'}, blocks) == 'From result'
    assert mod.page_title([], blocks) == 'Second'
    assert mod.page_title([], [{'title': '', 'data': [1]}]) == ''
    assert '<title>Top &lt;5&gt;</title>' in mod.canvas_page('<p>x</p>', 'Top <5>')
    assert '<title>Canvas</title>' in mod.canvas_page('<p>x</p>')
    open_fn = _CANVAS.split('def open_page', 1)[1].split('def _blocks_for_page', 1)[0]
    assert 'title=name' in open_fn
    store = _SESSION.split('def _store_design', 1)[1].split('\n    def ', 1)[0]
    assert "values['canvas_title']" in store
    charts = (
        _ROOT / 'common' / 'static' / 'src' / 'js' / 'chatboo_charts.js'
    ).read_text(encoding='utf-8')
    assert 'title: canvasTitleOf(row)' in charts
    for stack in ('owl1', 'owl2'):
        ctrl = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'controllers' / 'chatboo.py'
        ).read_text(encoding='utf-8')
        assert "session.canvas_design or '', session.canvas_title or ''," in ctrl


def test_a_hidden_card_stays_hidden_on_screen_whatever_its_display():
    import html as html_lib

    mod = _load_canvas_module()
    # The page of 17/10: the filter set hidden, .card{display:flex} kept it.
    design = (
        '<html><head><style>.card{display:flex}</style></head><body>'
        '<article class="card" hidden>Ana</article></body></html>'
    )
    rule = '@media screen{html [hidden]{display:none!important}}'
    frame = html_lib.unescape(
        mod.canvas_page(design, 'Top').split('srcdoc="', 1)[1].split('"></iframe>', 1)[0]
    )
    assert frame.index(rule) > frame.index('.card{display:flex}')
    assert frame.index(rule) < frame.index('</body>')
    standalone = mod.downloadable_page(design)
    assert standalone.index(rule) < standalone.index('</body>')
    assert 'set its hidden attribute' in mod.DESIGN_SYSTEM
    assert 'set its hidden attribute' in mod.EDIT_SYSTEM
    # The spare tables still open: show() drops hidden and sets display inline.
    assert 's.hidden=false' in mod._spare_rows_watch([['Ana']])


def test_the_page_names_the_company_its_figures_come_from():
    from types import SimpleNamespace

    mod = _load_canvas_module()
    for system in (mod.DESIGN_SYSTEM, mod.EDIT_SYSTEM):
        assert 'show that name in the page header' in system
        assert 'unless the instruction says not to' in system
        assert 'a weather forecast' in system
        assert 'Never write a company name the prompt does not give' in system
    env = SimpleNamespace(company=SimpleNamespace(name='  ACME  de Ejemplo '))
    assert mod.company_name(env) == 'ACME de Ejemplo'
    assert mod.company_name(SimpleNamespace(company=SimpleNamespace(name=False))) == ''
    assert mod.company_name(object()) == ''
    open_fn = _CANVAS.split('def open_page', 1)[1].split('\ndef ', 1)[0]
    assert "text += '\\nCompany: ' + company" in open_fn
    assert open_fn.index('company_name(sessions.env)') < open_fn.index('figures_for_design(')
    # The bubble button builds in a thread: same company the user picked.
    spawn = _JOB.split('def _spawn', 1)[1].split('\n    def ', 1)[0]
    assert 'context = dict(self.env.context)' in spawn
    assert 'api.Environment(cr, uid, context)' in spawn


def test_every_page_prints_and_downloads():
    import html as html_lib

    mod = _load_canvas_module()
    shell = mod.canvas_page(
        '<html><body><h1>Top</h1></body></html>', 'Top',
        download_url='/chatboo/canvas/7/download?rev=3',
    )
    # Buttons sit on our page, the frame only listens for its parent.
    assert shell.index('id="pns-tools"') < shell.index('<iframe')
    assert "postMessage(\\'pns-print\\',\\'*\\')" in shell or "postMessage('pns-print','*')" in shell
    assert 'href="/chatboo/canvas/7/download?rev=3"' in shell
    assert 'allow-same-origin' not in shell
    frame = html_lib.unescape(shell.split('srcdoc="', 1)[1].split('"></iframe>', 1)[0])
    assert frame.index('pns-print-bridge') < frame.index('</body>')
    assert 'e.source===window.parent' in frame
    assert 'id="pns-tools"' not in mod.canvas_page('')
    standalone = mod.downloadable_page('<html><body><h1>Top</h1></body></html>')
    assert standalone.index('id="pns-print"') < standalone.index('</body>')
    assert 'onclick="window.print()"' in standalone
    print_btn = shell.split('id="pns-print"', 1)[1].split('</button>', 1)[0]
    assert '<path d="M14 2H6a2 2 0 0 0-2 2v16' in print_btn
    assert print_btn.endswith('</svg>Print / PDF')
    down = shell.split('id="pns-download"', 1)[1].split('</a>', 1)[0]
    assert 'download="top.html"' in down
    assert '<path d="M21 15v4a2 2 0 0 1-2 2H5' in down
    assert down.endswith('</svg>Download HTML')
    assert '/secretary/' not in shell
    file_print = standalone.split('id="pns-print"', 1)[1].split('</button>', 1)[0]
    assert '<path d="M14 2H6a2 2 0 0 0-2 2v16' in file_print
    assert file_print.endswith('</svg>Print / PDF')
    assert '@media print{#pns-file-tools{display:none!important}}' in standalone
    assert mod.downloadable_page('') == ''
    assert mod.download_filename('Top 5 Clientes / Sevilla: facturación') == (
        'top-5-clientes-sevilla-facturacion.html'
    )
    assert mod.download_filename('') == 'canvas.html'
    assert mod.download_filename('', (
        '<html><head><title>Rentabilidad 2026</title></head></html>'
    )) == 'rentabilidad-2026.html'
    fn = _CANVAS.split('def download_filename', 1)[1].split('\ndef ', 1)[0]
    assert "_('Canvas')" not in fn
    assert 'do not add your own' in mod.DESIGN_SYSTEM
    for stack, po in (('owl1', 'es.po'), ('owl2', 'es_ES.po')):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
        catalog = (base / 'i18n' / po).read_text(encoding='utf-8')
        assert 'msgid "Print / PDF"\nmsgstr "Imprimir / PDF"' in catalog
        assert 'msgid "Download HTML"\nmsgstr "Descargar HTML"' in catalog
        ctrl = (base / 'controllers' / 'chatboo.py').read_text(encoding='utf-8')
        route = ctrl.split("'/chatboo/canvas/<int:session_id>/download'", 1)[1]
        route = route.split('@http.route', 1)[0]
        assert 'self._own_session(session_id)' in route
        assert 'content_disposition(' in route
        assert 'downloadable_page(session.canvas_design)' in route
        assert 'download_filename(session.canvas_title, session.canvas_design)' in route
        shared = ctrl.split("'/chatboo/page/<int:page_id>/download'", 1)[1]
        shared = shared.split('@http.route', 1)[0]
        assert 'download_filename(shared.name, shared.design)' in shared


def test_every_page_has_a_day_and_a_night_theme():
    import html as html_lib

    mod = _load_canvas_module()
    for system in (mod.DESIGN_SYSTEM, mod.EDIT_SYSTEM):
        assert 'the night values on html[data-theme="dark"]' in system
        assert 'do not add your own switch' in system
        assert 'pns-theme event' in system
    design = (
        '<html><head><style>:root{--bg:#fff}'
        "html[data-theme='dark']{--bg:#111}</style></head>"
        '<body><script>draw()</script></body></html>'
    )
    assert mod.has_night_theme(design)
    # No night colours, no switch: the button never promises what the page lacks.
    day_only = (
        '<html><head><style>:root{--bg:#fff}</style></head><body>'
        '<script>document.querySelector(\'[data-theme="dark"]\')</script>'
        '</body></html>'
    )
    assert not mod.has_night_theme(day_only)
    plain = mod.canvas_page(day_only, 'Top')
    assert 'id="pns-theme"' not in plain and 'pns-theme-script' not in plain
    assert 'pns-theme-start' not in html_lib.unescape(plain)
    assert 'id="pns-theme"' not in mod.downloadable_page(day_only)
    assert 'id="pns-print"' in mod.downloadable_page(day_only)
    shell = mod.canvas_page(design, 'Top')
    tools = shell.split('id="pns-tools"', 1)[1].split('</div>', 1)[0]
    assert tools.index('id="pns-theme"') < tools.index('id="pns-print"')
    # Our page keeps the choice; the frame only listens for its parent.
    assert shell.index('pns-theme-script') > shell.index('</iframe>')
    assert 'localStorage' in mod._THEME_SCRIPT
    assert 'allow-same-origin' not in shell
    frame = html_lib.unescape(shell.split('srcdoc="', 1)[1].split('"></iframe>', 1)[0])
    # Set before the model's styles and scripts, so the first paint is right.
    assert frame.index('pns-theme-start') < frame.index(':root{--bg:#fff}')
    assert frame.index('pns-theme-start') < frame.index('draw()')
    assert frame.index('pns-theme-bridge') < frame.index('</body>')
    assert 'e.source===window.parent' in mod._THEME_BRIDGE
    assert 'beforeprint' in mod._THEME_BRIDGE and 'set("light")' in mod._THEME_BRIDGE
    assert 'pns-theme-script' not in mod.canvas_page('')
    standalone = mod.downloadable_page(design)
    assert standalone.index('pns-theme-start') < standalone.index(':root{--bg:#fff}')
    assert 'onclick="window.pnsTheme()"' in standalone
    assert 'window.pnsTheme=function' in standalone
    # The button says where a press takes you: moon and Dark mode by day,
    # sun and Light mode by night.
    assert '#pns-theme[aria-pressed="true"] .pns-to-dark{display:none}' in shell
    assert '#pns-theme[aria-pressed="false"] .pns-to-light{display:none}' in shell
    assert 'html[data-theme="dark"] #pns-theme .pns-to-dark{display:none}' in standalone
    assert 'html:not([data-theme="dark"]) #pns-theme .pns-to-light{display:none}' in standalone
    button = shell.split('id="pns-theme"', 1)[1].split('</button>', 1)[0]
    assert 'class="pns-tool"' in button
    to_dark = button.split('class="pns-to-dark">', 1)[1].split('</span>', 1)[0]
    to_light = button.split('class="pns-to-light">', 1)[1].split('</span>', 1)[0]
    assert '<path d="M21 12.79' in to_dark and to_dark.endswith('</svg>Dark mode')
    assert '<circle cx="12"' in to_light and to_light.endswith('</svg>Light mode')
    # Same colours as the other buttons: none of its own.
    for page in (shell, standalone):
        icons = page.split('<style id="pns-theme-icons">', 1)[1].split('</style>', 1)[0]
        assert 'background' not in icons and 'color' not in icons
    standalone_button = standalone.split('id="pns-theme"', 1)[1].split('</button>', 1)[0]
    assert 'pns-tool' not in standalone_button
    assert '#pns-file-tools button{' in standalone
    # A click leaves focus on the button: only keyboard focus may keep it blue.
    for page in (shell, standalone):
        assert 'focus-visible' in page
        assert '.pns-tool:focus{' not in page and ',.pns-tool:focus{' not in page
        assert '#pns-file-tools button:focus{' not in page
        assert '#pns-theme:focus svg' not in page
    # Our wrapping is added when shown, never stored with the design.
    assert 'pns-theme' not in design
    for stack, po in (('owl1', 'es.po'), ('owl2', 'es_ES.po')):
        catalog = (
            _ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'i18n' / po
        ).read_text(encoding='utf-8')
        assert 'msgid "Dark mode"\nmsgstr "Modo oscuro"' in catalog
        assert 'msgid "Light mode"\nmsgstr "Modo claro"' in catalog
        assert 'msgid "Day / Night"' not in catalog


def test_a_shared_page_is_a_fixed_copy_for_named_users():
    security = (_ROOT / 'common' / 'security' / 'security.xml').read_text(encoding='utf-8')
    read_rule = security.split('chatboo_canvas_page_read_rule', 1)[1].split('</record>', 1)[0]
    assert "['|', ('owner_id', '=', user.id), ('user_ids', 'in', [user.id])]" in read_rule
    assert '<field name="perm_read" eval="True"/>' in read_rule
    assert '<field name="perm_write" eval="False"/>' in read_rule
    owner_rule = security.split('chatboo_canvas_page_owner_rule', 1)[1].split('</record>', 1)[0]
    assert "[('owner_id', '=', user.id)]" in owner_rule
    for perm in ('write', 'create', 'unlink'):
        assert '<field name="perm_%s" eval="True"/>' % perm in owner_rule
    acl = (_ROOT / 'common' / 'security' / 'ir.model.access.csv').read_text(encoding='utf-8')
    assert 'model_chatboo_canvas_page,base.group_user' in acl
    model = (_ROOT / 'common' / 'models' / 'chatboo_canvas_page.py').read_text(encoding='utf-8')
    assert "domain=[('share', '=', False)]" in model
    assert 'sudo().create' not in model
    create = model.split('def create', 1)[1].split('\n    def ', 1)[0]
    assert 'if not self.env.su:' in create
    write = model.split('def write', 1)[1].split('\n    def ', 1)[0]
    assert '_SYSTEM_FIELDS.intersection(vals)' in write
    assert "frozenset({'design', 'owner_id'})" in model
    for stack in ('owl1', 'owl2'):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
        ctrl = (base / 'controllers' / 'chatboo.py').read_text(encoding='utf-8')
        share = ctrl.split("'/chatboo/canvas/<int:session_id>/share'", 1)[1].split('@http.route', 1)[0]
        assert "methods=['POST']" in share
        assert 'csrf=False' not in share
        assert share.index('user_has_chatboo_access') < share.index('.sudo()')
        assert share.index('self._own_session(session_id)') < share.index('.sudo()')
        assert share.count('.sudo()') == 1
        assert 'pages.sudo().create(values)' in share
        assert 'redirect' not in share
        assert 'pages.people_named(user_ids).ids' in share
        assert "_('Canvas')" not in share
        readable = ctrl.split('def _readable_page', 1)[1].split('\n    def ', 1)[0]
        assert ".search([('id', '=', page_id)], limit=1)" in readable
        assert 'sudo' not in readable
        page = ctrl.split("'/chatboo/page/<int:page_id>'", 1)[1].split('@http.route', 1)[0]
        assert 'self._readable_page(page_id)' in page
        assert '} if owner else {}' in page
        manifest = (base / '__manifest__.py').read_text(encoding='utf-8')
        assert "'views/chatboo_canvas_page_views.xml'" in manifest
        assert (base / 'views' / 'chatboo_canvas_page_views.xml').read_text(
            encoding='utf-8',
        ) == (_ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'views'
              / 'chatboo_canvas_page_views.xml').read_text(encoding='utf-8')
        po = 'es.po' if stack == 'owl1' else 'es_ES.po'
        catalog = (base / 'i18n' / po).read_text(encoding='utf-8')
        assert 'msgid "Shared with"\nmsgstr "Compartida con"' in catalog
        owner = catalog.split('\nmsgid "Owner"', 1)[0].rsplit('#. module', 1)[1]
        assert 'field_chatboo_canvas_page__owner_id' in owner


def test_sharing_is_picking_names_and_the_ai_admin_sees_every_page():
    mod = _load_canvas_module()
    page = '<html><body></body></html>'
    shell = mod.canvas_page(
        page, 'Top', share_url='/chatboo/canvas/7/share', csrf_token='tok"en',
        people_url='/chatboo/share/people', people=[{'id': 3, 'name': 'Ana <b>'}],
    )
    assert '<form' not in shell
    panel = shell.split('id="pns-share-panel"', 1)[1].split('</div><script', 1)[0]
    assert 'data-csrf="tok&quot;en"' in panel
    assert 'data-url="/chatboo/canvas/7/share"' in panel
    assert 'Ana &lt;b&gt;' in panel and 'Ana <b>' not in panel
    script = shell.split('<script id="pns-share-script">', 1)[1].split('</script>', 1)[0]
    assert 'innerHTML' not in script
    assert 'method:"POST"' in script
    assert 'p.setAttribute("data-url",res.people_url)' in script
    share_btn = shell.split('id="pns-share"', 1)[1].split('</button>', 1)[0]
    assert '<circle cx="18" cy="5" r="3"/>' in share_btn
    assert share_btn.endswith('</svg>Share')
    assert '/secretary/' not in shell
    assert 'id="pns-share-pick-close"' in panel
    assert 'id="pns-share-sum-close"' in panel
    assert 'id="pns-share-who"' in panel
    assert 'id="pns-share-veil"' in shell
    assert 'pick.hidden=true;summary.hidden=false' in script
    assert 'getElementById("pns-share-pick-close")' in script
    assert 'getElementById("pns-share-sum-close")' in script
    assert 'id="pns-share"' not in mod.canvas_page(page, 'Top')
    assert 'id="pns-share"' not in mod.canvas_page(
        page, 'Top', share_url='/x', csrf_token='t',
    )
    model = (_ROOT / 'common' / 'models' / 'chatboo_canvas_page.py').read_text(encoding='utf-8')
    named = model.split('def people_named', 1)[1].split('\n    def ', 1)[0]
    assert 'not user.share' in named and 'sudo' not in named
    matching = model.split('def people_matching', 1)[1].split('\n    @', 1)[0]
    assert "('share', '=', False)" in matching and 'sudo' not in matching
    assert "self.write({'user_ids': [(5, 0, 0)]})" in model
    security = (_ROOT / 'common' / 'security' / 'security.xml').read_text(encoding='utf-8')
    admin = security.split('chatboo_canvas_page_admin_rule', 1)[1].split('</record>', 1)[0]
    assert "[(1, '=', 1)]" in admin
    assert "ref('pns_ai_mcp.group_ai_admin')" in admin
    for perm in ('read', 'write', 'create', 'unlink'):
        assert '<field name="perm_%s" eval="True"/>' % perm in admin
    for stack in ('owl1', 'owl2'):
        base = _ROOT / 'stacks' / stack / 'pns_ai_chatboo'
        ctrl = (base / 'controllers' / 'chatboo.py').read_text(encoding='utf-8')
        people = ctrl.split("'/chatboo/share/people', type=", 1)[1].split('@http.route', 1)[0]
        assert 'request.env.user.share' in people and 'sudo' not in people
        edit = ctrl.split("'/chatboo/page/<int:page_id>/people'", 1)[1].split('@http.route', 1)[0]
        assert "methods=['POST']" in edit and 'csrf=False' not in edit
        assert 'shared.owner_id.id != request.env.uid' in edit
        assert 'sudo' not in edit
        views = (base / 'views' / 'chatboo_canvas_page_views.xml').read_text(encoding='utf-8')
        assert 'parent="pns_ai_mcp.menu_ai_security"' in views
        assert '<field name="view_mode">tree,form</field>' in views
        assert views.count('name="action_unshare"') == 2
        po = 'es.po' if stack == 'owl1' else 'es_ES.po'
        catalog = (base / 'i18n' / po).read_text(encoding='utf-8')
        assert 'msgid "Shared pages"\nmsgstr "Páginas compartidas"' in catalog
        assert 'msgid "Stop sharing"\nmsgstr "Dejar de compartir"' in catalog
        assert 'msgid "Search people"\nmsgstr "Buscar personas"' in catalog
        assert 'Manage sharing' not in catalog


def test_someone_added_to_a_shared_page_hears_about_it():
    model = (_ROOT / 'common' / 'models' / 'chatboo_canvas_page.py').read_text(encoding='utf-8')
    create = model.split('def create', 1)[1].split('\n    def ', 1)[0]
    assert 'page._tell_new_readers(page.user_ids)' in create
    write = model.split('def write', 1)[1].split('\n    def ', 1)[0]
    assert "if 'user_ids' in vals else {}" in write
    assert 'page.user_ids - before[page.id]' in write
    tell = model.split('def _tell_new_readers', 1)[1].split('\n    def ', 1)[0]
    assert 'users = users - self.owner_id' in tell
    assert "'action': 'page_shared'" in tell
    assert "'url': self.page_path()" in tell
    assert 'sudo' not in tell
    assert tell.index("self._notify_inbox(users.mapped('partner_id'))") < tell.index(
        "if 'bus.bus' not in self.env:"
    )
    assert "_inherit = ['mail.thread']" in model
    inbox = model.split('def _notify_inbox', 1)[1].split('\n    def ', 1)[0]
    assert 'page.message_notify(' in inbox
    assert 'partner_ids=readers.ids' in inbox
    assert 'with_context(lang=lang' in inbox
    note = model.split('def _inbox_note', 1)[1]
    assert 'Markup(' in note
    assert "_('%s shared a page with you')" in note
    assert 'self.url' in note
    for stack in ('owl1', 'owl2'):
        manifest = (_ROOT / 'stacks' / stack / 'pns_ai_chatboo' / '__manifest__.py').read_text(
            encoding='utf-8',
        )
        assert "'mail'" in manifest.split("'depends'", 1)[1].split(']', 1)[0]
    owl1 = (_ROOT / 'stacks' / 'owl1' / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
            / 'chatboo_systray.js').read_text(encoding='utf-8')
    start = owl1.split('start: function', 1)[1].split('_enableSystray: function', 1)[0]
    assert start.index("'onNotification'") < start.index('pns_chatboo_show_systray')
    assert "route: '/chatboo/check_health'" not in start
    enable = owl1.split('_enableSystray: function', 1)[1].split('\n        },', 1)[0]
    assert 'onNotification' not in enable
    handler = owl1.split('_onBusNotifications: function', 1)[1].split('_onAsyncDone', 1)[0]
    assert handler.index("'page_shared'") < handler.index('if (!this._hasAccess)')
    owl2 = (_ROOT / 'stacks' / 'owl2' / 'pns_ai_chatboo' / 'static' / 'src' / 'js'
            / 'chatboo_systray.js').read_text(encoding='utf-8')
    sync = owl2.split('_onSyncPayload(raw)', 1)[1].split('\n    }\n', 1)[0]
    assert sync.index('"page_shared"') < sync.index('const isAsyncDone')
    for js in (owl1, owl2):
        shown = js.split('_showSharedPage', 2)[2]
        assert "/chatboo/page/" in shown.split('Open page', 1)[0]
        assert "'noopener'" in shown or '"noopener"' in shown
    for stack, po in (('owl1', 'es.po'), ('owl2', 'es_ES.po')):
        catalog = (_ROOT / 'stacks' / stack / 'pns_ai_chatboo' / 'i18n' / po).read_text(
            encoding='utf-8',
        )
        assert ('msgid "%s shared a page with you"\n'
                'msgstr "%s ha compartido una página contigo"') in catalog
        shared = catalog.split('msgid "Shared page"', 1)[0].rsplit('#. module', 1)[1]
        assert 'chatboo_systray.js' in shared


def test_canvas_tools_clear_the_frame_scrollbar():
    """The frame scrollbar runs under the tools: leave it plus the gap."""
    import re
    style = _CANVAS.split('_TOOL_STYLE = (', 1)[1].split(')', 1)[0]
    right = int(re.search(r'right:(\d+)px', style).group(1))
    gap = int(re.search(r'gap:(\d+)px', style).group(1))
    assert right >= 17 + gap
    panel = re.search(r'#pns-share-panel\{[^}]*right:(\d+)px', _CANVAS)
    assert int(panel.group(1)) == right
