#!/usr/bin/env python3
"""Update the shared theme and existing shared navigation in an external report."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from report_workspace import PolicyError, assert_external, load_run

THEME_PATH = Path(__file__).resolve().parents[1] / 'assets/report-theme.css'
NAVIGATION_PATH = THEME_PATH.with_name('report-navigation.js')
THEME_ID = 'report-theme'
STYLE_BLOCK = re.compile(r'<style\b(?P<attrs>[^>]*)>(?P<css>.*?)</style\s*>', re.I | re.S)
THEME_ATTR = re.compile(r'''(?:^|\s)id\s*=\s*(?:"report-theme"|'report-theme'|report-theme(?=\s|$))''', re.I)


def theme_blocks(html: str) -> list[re.Match]:
    return [m for m in STYLE_BLOCK.finditer(html) if THEME_ATTR.search(m['attrs'])]


def apply_theme(html: str, css: str) -> str:
    blocks = theme_blocks(html)
    if len(blocks) > 1:
        raise ValueError('Multiple report-theme blocks; resolve the duplicate before applying the theme.')
    block = f'<style id="{THEME_ID}">\n{css.strip()}\n</style>'
    if blocks:
        start, end = blocks[0].span()
        return html[:start] + block + html[end:]
    head = re.search(r'<head\b[^>]*>', html, re.I)
    if not head:
        raise ValueError('Missing <head>; cannot insert the report theme.')
    return html[:head.end()] + '\n' + block + html[head.end():]


def check_theme(html: str, css: str) -> list[str]:
    blocks = theme_blocks(html)
    if len(blocks) != 1:
        return ['Expected one inline style with id="report-theme"; apply the shared theme.']
    if blocks[0]['css'].strip() != css.strip():
        return ['Inline report theme differs from assets/report-theme.css; reapply the shared theme.']
    return []


def sync_navigation(html: str, javascript: str) -> str:
    """Refresh an existing shared script without adding navigation or changing other HTML."""
    class NavigationParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.line_offsets = [0] + [match.end() for match in re.finditer('\n', html)]
            self.blocks = []
            self.start = None

        def source_offset(self):
            line, column = self.getpos()
            return self.line_offsets[line - 1] + column

        def handle_starttag(self, tag, attrs):
            ids = [value for name, value in attrs if name == 'id']
            if tag != 'script' or 'report-navigation' not in ids:
                return
            if len(ids) != 1 or any(name == 'src' for name, _ in attrs):
                raise ValueError('Shared navigation must have one id and inline script content.')
            types = [value for name, value in attrs if name == 'type']
            if len(types) > 1 or any(value not in (None, '', 'text/javascript', 'application/javascript') for value in types):
                raise ValueError('Shared navigation must be a classic JavaScript script.')
            self.start = self.source_offset()

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            if self.start is not None:
                raise ValueError('Shared navigation requires a closing </script> tag.')

        def handle_endtag(self, tag):
            if tag == 'script' and self.start is not None:
                self.blocks.append((self.start, html.index('>', self.source_offset()) + 1))
                self.start = None

    parser = NavigationParser()
    parser.feed(html)
    parser.close()
    if parser.start is not None:
        raise ValueError('Shared navigation requires a closing </script> tag.')
    if len(parser.blocks) > 1:
        raise ValueError('Multiple report-navigation blocks; resolve the duplicate before updating.')
    if not parser.blocks:
        return html
    start, end = parser.blocks[0]
    block = f'<script id="report-navigation">\n{javascript.strip()}\n</script>'
    return html[:start] + block + html[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    try:
        run, meta = load_run(args.run)
        report = run / 'delivery/report.html'
        if report.parent.is_symlink() or report.is_symlink():
            raise PolicyError('Symlink report paths are not accepted.')
        assert_external(report, Path(meta['workspace']))
        html = report.read_text(encoding='utf-8')
        updated = apply_theme(html, THEME_PATH.read_text(encoding='utf-8'))
        updated = sync_navigation(updated, NAVIGATION_PATH.read_text(encoding='utf-8'))
        report.write_text(updated, encoding='utf-8')
        print('Shared theme and any existing shared navigation updated. Local overrides and rendered appearance still require review.')
        return 0
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
