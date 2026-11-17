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
    def test_high_inline_code_density_warns_only_outside_details_and_dl(self):
        dense = '<p>' + ' '.join(f'<code>f{i}</code>' for i in range(6)) + '</p>'
        errors, warnings = check_html(BASE.replace('</main>', dense + '</main>'))
        self.assertEqual(errors, [])
        self.assertTrue(any('>=6 inline <code> tags' in w for w in warnings))
        in_details = f'<details><summary>Code</summary>{dense}</details>'
        self.assertEqual(check_html(BASE.replace('</main>', in_details + '</main>')), ([], []))
        in_dl = f'<dl><dt id="C1">C1</dt><dd>{dense}</dd></dl>'
        self.assertEqual(check_html(BASE.replace('</main>', in_dl + '</main>')), ([], []))
    def test_long_svg_text_warns_but_svg_desc_is_allowed(self):
        long_label = '这是一个明显超过三十六个字符并且容易与邻近图例互相挤压碰撞的超长SVG标签文本'
        svg_with_long_text = f'<svg role="img" aria-label="Chart"><desc>{long_label}</desc><text x="10" y="20">{long_label}</text></svg>'
        errors, warnings = check_html(BASE.replace('</main>', svg_with_long_text + '</main>'))
        self.assertEqual(errors, [])
        self.assertTrue(any('SVG <text> label(s) exceed 36 characters' in w for w in warnings))
        svg_with_long_desc_only = f'<svg role="img" aria-label="Chart"><desc>{long_label}</desc><text x="10" y="20">短标签</text></svg>'
        self.assertEqual(check_html(BASE.replace('</main>', svg_with_long_desc_only + '</main>')), ([], []))
    def test_meta_commentary_phrase_warns(self):
        html = BASE.replace('</main>', '<p>通过悬浮目录可以查看，也可以一句话怎么讲清楚。</p></main>')
        errors, warnings = check_html(html)
        self.assertEqual(errors, [])
        self.assertTrue(any('meta-commentary phrase detected' in w for w in warnings))

if __name__ == '__main__':
    unittest.main()
