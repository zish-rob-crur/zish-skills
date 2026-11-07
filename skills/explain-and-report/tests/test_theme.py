import sys
sys.dont_write_bytecode = True
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_report_theme import THEME_PATH, NAVIGATION_PATH, apply_theme, check_theme, sync_navigation
from check_report import check_html
from report_workspace import init_run

CSS = THEME_PATH.read_text(encoding='utf-8')
PAGE = '''<!doctype html><html lang="en"><head><title>Example</title>
<meta name="viewport" content="width=device-width"><style>.routes {display:grid}</style>
</head><body><main><h1>Example</h1><p>Evidence remains unchanged.</p></main></body></html>'''


class ThemeTests(unittest.TestCase):
    def test_apply_preserves_content_and_layout_and_is_repeatable(self):
        result = apply_theme(PAGE, CSS)
        self.assertEqual(result.split('<body>')[1], PAGE.split('<body>')[1])
        self.assertIn('<style>.routes {display:grid}</style>', result)
        self.assertEqual(apply_theme(result, CSS), result)
        self.assertEqual(check_html(result), ([], []))
        self.assertEqual(check_theme(result, CSS), [])

    def test_missing_or_changed_theme_is_detected(self):
        self.assertTrue(check_theme(PAGE, CSS))
        altered = apply_theme(PAGE, CSS).replace('--bg: #0f1418', '--bg: #ffffff')
        self.assertTrue(check_theme(altered, CSS))
        self.assertEqual(check_theme(apply_theme(altered, CSS), CSS), [])

    def test_duplicate_theme_is_rejected(self):
        page = apply_theme(PAGE, CSS).replace('</head>', '<style id="report-theme"></style></head>')
        with self.assertRaises(ValueError):
            apply_theme(page, CSS)

    def test_unrelated_style_attribute_is_not_replaced(self):
        page = PAGE.replace('<style>', '<style data-id="report-theme">')
        result = apply_theme(page, CSS)
        self.assertIn('<style data-id="report-theme">.routes {display:grid}</style>', result)
        self.assertEqual(check_theme(result, CSS), [])

    def test_navigation_sync_preserves_other_content_and_is_repeatable(self):
        old = '<script id="report-navigation">oldNavigation();</script>'
        extra = '<script id="custom-controller">customController();</script>'
        page = PAGE.replace('</body>', old + extra + '</body>')
        updated = sync_navigation(page, 'currentNavigation();')
        self.assertEqual(updated, page.replace(old, '<script id="report-navigation">\ncurrentNavigation();\n</script>'))
        self.assertEqual(sync_navigation(updated, 'currentNavigation();'), updated)

    def test_navigation_is_not_added_or_matched_inside_unrelated_content(self):
        self.assertEqual(sync_navigation(PAGE, 'current();'), PAGE)
        page = PAGE.replace('</body>', '''<!-- <script id="report-navigation">comment();</script> -->
<script data-id="report-navigation">unrelated();</script>
<script data-note=' id="report-navigation"'>another();</script>
<script>const label = 'id="report-navigation"';</script></body>''')
        self.assertEqual(sync_navigation(page, 'current();'), page)

    def test_navigation_supports_html_id_spellings_and_line_endings(self):
        for opening in ["<script id='report-navigation'>", '<SCRIPT ID=report-navigation>', '<script id="report&#45;navigation">']:
            with self.subTest(opening=opening):
                page = PAGE.replace('</body>', opening + 'old();</script>tail</body>').replace('\n', '\r\n')
                updated = sync_navigation(page, 'current();')
                self.assertEqual(updated, page.replace(opening + 'old();</script>', '<script id="report-navigation">\ncurrent();\n</script>'))

    def test_ambiguous_or_non_inline_navigation_is_rejected(self):
        candidates = [
            '<script id="report-navigation"></script><script id="report-navigation"></script>',
            '<script id="custom" id="report-navigation"></script>',
            '<script id="report-navigation" id="report-navigation"></script>',
            '<script id="report-navigation" src="navigation.js"></script>',
            '<script id="report-navigation" type="application/json">{}</script>',
            '<script id="report-navigation" type="module"></script>',
            '<script id="report-navigation"/>',
            '<script id="report-navigation">unfinished();',
        ]
        for script in candidates:
            with self.subTest(script=script):
                with self.assertRaises(ValueError):
                    sync_navigation(PAGE.replace('</body>', script + '</body>'), 'current();')

    def test_bundled_html_examples_share_current_theme_and_navigation(self):
        navigation = (ROOT / 'assets/report-navigation.js').read_text().strip()
        for name in ('report-shell.html', 'reference-layout.html', 'reference-report.html', 'flow-patterns.html', 'mechanism-walkthrough.html'):
            with self.subTest(name=name):
                html = (ROOT / 'assets' / name).read_text()
                self.assertEqual(check_theme(html, CSS), [])
                scripts = re.findall(r'<script id="report-navigation">(.*?)</script>', html, re.S)
                self.assertEqual([script.strip() for script in scripts], [navigation])

    def test_cli_works_in_external_run_and_rejects_symlink(self):
        with tempfile.TemporaryDirectory(prefix='report-theme-test-') as tmp:
            base = Path(tmp)
            workspace = base / 'project'
            workspace.mkdir()
            run = init_run(workspace, 'theme-test', base / 'outputs')
            report = run / 'delivery/report.html'
            old_navigation = '<script id="report-navigation">oldNavigation();</script>'
            report.write_text(PAGE.replace('</body>', old_navigation + '</body>'))
            command = [sys.executable, '-B', str(ROOT / 'scripts/apply_report_theme.py'), '--run', str(run)]
            applied = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(check_theme(report.read_text(), CSS), [])
            navigation = re.search(r'<script id="report-navigation">(.*?)</script>', report.read_text(), re.S)[1]
            self.assertEqual(navigation.strip(), NAVIGATION_PATH.read_text().strip())
            self.assertIn('<p>Evidence remains unchanged.</p>', report.read_text())
            duplicate = PAGE.replace('</body>', old_navigation * 2 + '</body>')
            report.write_text(duplicate)
            denied_duplicate = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(denied_duplicate.returncode, 0)
            self.assertEqual(report.read_text(), duplicate)
            report.unlink()
            target = workspace / 'source.html'
            target.write_text(PAGE)
            report.symlink_to(target)
            denied = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(target.read_text(), PAGE)


if __name__ == '__main__':
    unittest.main()
