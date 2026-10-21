#!/usr/bin/env python3
"""Optional local Playwright capture. Never installs dependencies or uploads files.

Run with python3 -B. All output is in a validated off-repository report run.
Machine checks do not certify visual quality, privacy, facts, or user approval.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import uuid
from report_workspace import PolicyError, check_run, digest, load_run, write_json
from check_report import check_html

CORE_TEXT = """() => {
 const c = document.querySelector('main').cloneNode(true);
 c.querySelectorAll('details,button,script,style,noscript,[data-interactive]').forEach(e => e.remove());
 return c.textContent.replace(/\\s+/g,' ').trim();
}"""
PAGE_METRICS = """() => ({
 horizontal_overflow_px: Math.max(0, document.documentElement.scrollWidth - innerWidth),
 broken_images: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length,
 broken_anchors: [...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href'))
   .filter(h => h.length > 1 && !document.getElementById(h.slice(1))),
 body_font: getComputedStyle(document.body).fontFamily,
 font_status: document.fonts.status,
 viewport: {width: innerWidth, height: innerHeight},
 main_text_length: document.querySelector('main').innerText.length
})"""

def capture(run_arg: Path, browser_path: str | None, export_figures: bool, load_mode: str = "file") -> tuple[Path, dict]:
    check = check_run(run_arg)
    if not check['ok']:
        raise PolicyError(json.dumps(check, ensure_ascii=False))
    run, meta = load_run(run_arg)
    report = run / 'delivery/report.html'
    source_hash = digest(report)
    errors, warnings = check_html(report.read_text(encoding='utf-8'))
    if errors:
        raise PolicyError('Static preflight failed: ' + '; '.join(errors))
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PolicyError('Playwright is not installed. Use an existing browser tool, or ask for dependency installation; no install was attempted.') from exc
    capture_id = source_hash[:12] + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6]
    output = run / 'qa/screenshots' / capture_id
    output.mkdir(mode=0o700)
    result = {
        'source_html_sha256': source_hash, 'capture_id': capture_id, 'source': 'delivery/report.html',
        'captured_at': datetime.now(timezone.utc).isoformat(), 'os': platform.platform(),
        'visual_review': 'not_reviewed', 'content_review': 'not_reviewed', 'user_design_approval': 'not_requested',
        'static_warnings': warnings, 'screenshots': [], 'figure_exports': [], 'checks': {},
        'page_errors': [], 'blocked_requests': [], 'navigation_mode': 'file://' if load_mode == 'file' else 'set_content',
        'file_protocol_verified': load_mode == 'file',
        'device_scale_factor': 1, 'theme': 'light', 'javascript': {'primary': True, 'secondary': False},
        'print_scope': 'print-media CSS preview, not PDF/physical-print validation'
    }
    def load(page):
        if load_mode == 'file':
            page.goto(report.as_uri(), wait_until='load', timeout=20000)
        else:
            page.set_content(report.read_text(encoding='utf-8'), wait_until='load', timeout=20000)
    def shot(locator, name: str, **kwargs):
        locator.screenshot(path=str(output / name), animations='disabled', **kwargs)
        result['screenshots'].append(name)
    def attach(context):
        def route_handler(route):
            url = route.request.url
            if url.startswith(('file:', 'data:', 'about:')):
                route.continue_()
            else:
                # Avoid logging query strings/tokens into QA metadata.
                result['blocked_requests'].append(url.split('?', 1)[0].split('#', 1)[0])
                route.abort()
        context.route('**/*', route_handler)
        context.set_offline(True)
    try:
        with sync_playwright() as p:
            launch = {}
            executable = browser_path or shutil.which('chromium') or shutil.which('chromium-browser')
            if executable:
                launch['executable_path'] = executable
            browser = p.chromium.launch(**launch)
            result['browser'] = browser.version
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1,
                                          color_scheme='light', reduced_motion='reduce', service_workers='block')
            attach(context)
            page = context.new_page()
            page.on('pageerror', lambda error: result['page_errors'].append(str(error)))
            load(page)
            page.evaluate('document.fonts.ready')
            original_text = page.evaluate(CORE_TEXT)
            original_title = page.locator('h1').inner_text()
            result['checks']['desktop'] = page.evaluate(PAGE_METRICS)
            shot(page, 'desktop-first.png')
            shot(page, 'desktop-full.png', full_page=True)
            dense = page.locator('[data-qa="dense"]').first
            if dense.count() == 0:
                sections = page.locator('main section')
                if sections.count():
                    lengths = sections.evaluate_all('(es) => es.map(e => e.textContent.length)')
                    dense = sections.nth(max(range(len(lengths)), key=lambda i: lengths[i]))
            if dense.count():
                shot(dense, 'desktop-dense.png')
            footer = page.locator('footer').last
            if footer.count():
                footer.scroll_into_view_if_needed()
                shot(page, 'desktop-end.png')
            figures = page.locator('[data-figure-id]')
            ids = set()
            for i in range(figures.count()):
                element = figures.nth(i)
                fid = element.get_attribute('data-figure-id') or ''
                if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', fid) or fid in ids:
                    raise PolicyError('Figure IDs must be unique lowercase slugs: ' + fid)
                ids.add(fid)
                shot(element, f'figure-{fid}.png')
                if export_figures:
                    target_dir = run / 'figures' / capture_id
                    target_dir.mkdir(mode=0o700, exist_ok=True)
                    target = target_dir / f'{fid}.png'
                    shutil.copyfile(output / f'figure-{fid}.png', target)
                    caption = element.locator('figcaption').inner_text() if element.locator('figcaption').count() == 1 else ''
                    result['figure_exports'].append({'figure_id': fid, 'role': 'content',
                        'local_path': str(target.relative_to(run)), 'sha256': digest(target),
                        'caption': caption, 'publication_authorized': False})
            page.evaluate('window.scrollTo(0,0)')
            page.keyboard.press('Tab')
            result['checks']['keyboard_first_focus'] = page.evaluate("document.activeElement.tagName")
            toggle = page.locator('[data-expand-all]')
            if toggle.count() and toggle.first.is_visible():
                toggle.first.click()
                result['checks']['expand_all'] = page.locator('details:not([open])').count() == 0
                toggle.first.click()
                result['checks']['collapse_all'] = page.locator('details[open]').count() == 0
            page.set_viewport_size({'width': 390, 'height': 844})
            page.evaluate('window.scrollTo(0,0)')
            result['checks']['mobile'] = page.evaluate(PAGE_METRICS)
            shot(page, 'mobile-first.png')
            shot(page, 'mobile-full.png', full_page=True)
            if figures.count():
                shot(figures.first, 'mobile-first-figure.png')
            page.set_viewport_size({'width': 1440, 'height': 1000})
            page.emulate_media(media='print')
            page.evaluate("window.dispatchEvent(new Event('beforeprint')); window.scrollTo(0,0)")
            shot(page, 'print-style-preview.png')
            result['checks']['print_style_preview_captured'] = True
            page.evaluate("window.dispatchEvent(new Event('afterprint'))")
            nojs = browser.new_context(viewport={'width': 1440, 'height': 1000}, java_script_enabled=False,
                                       color_scheme='light', service_workers='block')
            attach(nojs)
            np = nojs.new_page()
            load(np)
            np.evaluate('document.fonts.ready')
            result['checks']['no_js'] = {'same_title': np.locator('h1').inner_text() == original_title,
                'same_core_dom_text': bool(original_text) and np.evaluate(CORE_TEXT) == original_text,
                'main_visible': np.locator('main').is_visible(), 'metrics': np.evaluate(PAGE_METRICS)}
            shot(np, 'desktop-no-js.png')
            browser.close()
        failures = []
        for name in ('desktop', 'mobile'):
            m = result['checks'][name]
            if m['horizontal_overflow_px'] > 1 or m['broken_images'] or m['broken_anchors']:
                failures.append(name + ': overflow/broken images/broken anchors')
        no_js = result['checks']['no_js']
        if not all(no_js[k] for k in ('same_title', 'same_core_dom_text', 'main_visible')):
            failures.append('No-JS core content mismatch')
        for k in ('expand_all', 'collapse_all'):
            if result['checks'].get(k) is False:
                failures.append(k + ' failed')
        if result['page_errors'] or result['blocked_requests']:
            failures.append('Page errors or attempted external resources')
        if digest(report) != source_hash:
            failures.append('HTML changed during capture; this batch is stale')
        result['automated_status'] = 'passed' if not failures else 'failed'
        result['failures'] = failures
    except Exception as exc:
        result['automated_status'] = 'failed'
        result['file_protocol_verified'] = False
        result['failures'] = [str(exc)]
    finally:
        write_json(output / 'capture.json', result)
    return output, result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--browser', help='Path to an already installed Chromium executable; otherwise auto-detect.')
    parser.add_argument('--load-mode', choices=['file', 'content'], default='file',
                        help='Default file://. Explicit content mode for restricted hosts; does NOT verify file://.')
    parser.add_argument('--export-figures', action='store_true', help='Export only explicitly tagged content figures; no upload.')
    args = parser.parse_args()
    old_umask = os.umask(0o077)
    try:
        output, result = capture(args.run, args.browser, args.export_figures, args.load_mode)
        print(json.dumps({'capture_dir': str(output), 'automated_status': result['automated_status'],
            'failures': result['failures'], 'visual_review': 'not_reviewed'}, ensure_ascii=False, indent=2))
        return 0 if result['automated_status'] == 'passed' else 1
    except (PolicyError, OSError, ValueError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        os.umask(old_umask)

if __name__ == '__main__':
    raise SystemExit(main())
