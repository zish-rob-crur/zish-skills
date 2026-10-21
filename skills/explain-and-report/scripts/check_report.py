#!/usr/bin/env python3
"""Dependency-free HTML preflight. Not an HTML validator, security audit or visual test."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: list[str] = []
        self.errors: list[str] = []
        self.titles: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {key: value or '' for key, value in attrs}
        self.tags.append((tag, d))
        if 'id' in d:
            self.ids.append(d['id'])
        if tag == 'title':
            self.in_title = True
        if tag in {'iframe', 'object', 'embed', 'base'}:
            self.errors.append(f'Unsupported embedded/redirecting resource: <{tag}>')
        for attr in ('src', 'poster', 'srcset'):
            if attr in d and not d[attr].startswith('data:'):
                self.errors.append(f'Non-inlined resource: <{tag} {attr}="{d[attr]}">')
        if tag == 'link' and set(d.get('rel', '').split()) & {'stylesheet', 'preload', 'prefetch', 'modulepreload', 'icon'}:
            if not d.get('href', '').startswith('data:'):
                self.errors.append(f'Non-inlined <link>: {d.get("href", "")}')
        if tag in {'use', 'image'}:
            value = d.get('href', d.get('xlink:href', ''))
            if value and not value.startswith(('#', 'data:')):
                self.errors.append(f'External SVG resource: {value}')
        for attr in ('href', 'action', 'formaction', 'xlink:href'):
            if re.match(r'\s*(?:javascript|vbscript):', d.get(attr, ''), re.I):
                self.errors.append(f'Executable URL on <{tag}>')
        if tag == 'meta' and d.get('http-equiv', '').lower() == 'refresh':
            self.errors.append('Meta refresh is not allowed')
        if tag == 'img' and not d.get('alt'):
            self.errors.append('Image has no non-empty alt text')
        if tag == 'svg' and d.get('aria-hidden') != 'true':
            if not (d.get('aria-label') or d.get('aria-labelledby')):
                self.errors.append('Meaningful SVG has no accessible name')

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.titles.append(data)


def check_html(text: str) -> tuple[list[str], list[str]]:
    parser = ReportParser()
    parser.feed(text)
    errors = list(parser.errors)
    warnings: list[str] = []
    tags = [tag for tag, _ in parser.tags]
    if not re.search(r'<!doctype\s+html', text, re.I):
        errors.append('Missing HTML doctype')
    if not ''.join(parser.titles).strip():
        errors.append('Missing page title')
    if not any(tag == 'html' and d.get('lang') for tag, d in parser.tags):
        errors.append('Missing document language')
    if not any(tag == 'meta' and d.get('name', '').lower() == 'viewport' for tag, d in parser.tags):
        errors.append('Missing viewport meta')
    if tags.count('h1') != 1:
        errors.append('Expected exactly one h1')
    if 'main' not in tags:
        errors.append('Missing main landmark')
    if re.search(r'\{\{[^{}]+\}\}', text):
        errors.append('Unreplaced {{...}} placeholder')
    if len(parser.ids) != len(set(parser.ids)):
        errors.append('Duplicate HTML IDs')
    ids = set(parser.ids)
    for tag, attrs in parser.tags:
        href = attrs.get('href', '')
        if tag == 'a' and href.startswith('#') and href[1:] and href[1:] not in ids:
            errors.append(f'Broken fragment link: {href}')
        for target in attrs.get('aria-labelledby', '').split():
            if target not in ids:
                errors.append(f'Missing aria-labelledby target: {target}')
    if re.search(r'@import\b', text, re.I):
        errors.append('CSS @import conflicts with offline delivery')
    for match in re.finditer(r'url\(\s*[\'\"]?([^\s\)\'\"]+)', text, re.I):
        if not match.group(1).startswith(('data:', '#')):
            errors.append(f'Non-inlined CSS resource: {match.group(1)}')
    if re.search(r'\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\b|sendBeacon\s*\(|import\s*\()', text):
        warnings.append('Possible network/dynamic code detected; review it manually (code examples can also match)')
    if re.search(r'\bon\w+\s*=|\.innerHTML\b', text, re.I):
        warnings.append('Inline event handler or innerHTML detected; review escaping and trust boundaries')
    if '@media print' not in text:
        warnings.append('No print stylesheet detected')
    if tags.count('figure') > tags.count('figcaption'):
        warnings.append('Some figures may lack captions')
    if len(text.encode('utf-8')) > 2_000_000:
        warnings.append('File exceeds 2 MB; check whether raw logs or assets can be reduced')
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def main() -> int:
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('report', type=Path)
    args = argp.parse_args()
    try:
        text = args.report.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    errors, warnings = check_html(text)
    for message in errors:
        print('ERROR:', message)
    for message in warnings:
        print('WARN:', message)
    print(f'{len(errors)} error(s), {len(warnings)} warning(s). This is a static preflight, not a fact/security/visual audit.')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
