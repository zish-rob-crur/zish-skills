import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import unittest
from check_report import check_html

BASE = '''<!doctype html><html lang="zh-CN"><head><title>Test</title>
<meta name="viewport" content="width=device-width"><style>@media print {body {color:black}}</style>
</head><body><main><h1 id="answer">Answer</h1><a href="#answer">Answer</a></main></body></html>'''

class PreflightTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(check_html(BASE), ([], []))
    def test_external_script(self):
        self.assertTrue(check_html(BASE.replace('</body>', '<script src="https://cdn.example/x.js"></script></body>'))[0])
    def test_relative_image(self):
        self.assertTrue(check_html(BASE.replace('</main>', '<img alt="test" src="x.png"></main>'))[0])
    def test_broken_anchor(self):
        self.assertTrue(check_html(BASE.replace('href="#answer"', 'href="#missing"'))[0])
    def test_placeholder(self):
        self.assertTrue(check_html(BASE.replace('Answer</h1>', '{{TITLE}}</h1>'))[0])
    def test_external_evidence_link_allowed(self):
        self.assertFalse(check_html(BASE.replace('href="#answer"', 'href="https://example.org/source"'))[0])
    def test_unsafe_url(self):
        self.assertTrue(check_html(BASE.replace('href="#answer"', 'href="javascript:alert(1)"'))[0])
    def test_missing_svg_name(self):
        self.assertTrue(check_html(BASE.replace('</main>', '<svg></svg></main>'))[0])
    def test_named_svg(self):
        self.assertFalse(check_html(BASE.replace('</main>', '<svg role="img" aria-label="Test figure"></svg></main>'))[0])
    def test_inline_css_resource(self):
        self.assertTrue(check_html(BASE.replace('</style>', 'body{background:url(background.png)}</style>'))[0])

if __name__ == '__main__':
    unittest.main()
