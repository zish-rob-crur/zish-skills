import sys
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from report_workspace import PolicyError, assert_external, check_run, default_home, init_run, load_run, resolve_report_html

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='explain-report-test-')
        self.base = Path(self.tmp.name).resolve()
        self.source = self.base / 'project'
        self.source.mkdir()
        self.output = self.base / 'outputs'
    def tearDown(self):
        self.tmp.cleanup()
    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.source), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    def repo(self):
        if not shutil.which('git'):
            self.skipTest('git executable required for Git-specific test')
        self.git('init', '-q')
    def test_external_accepted(self):
        self.assertEqual(assert_external(self.output, self.source), self.output)
    def test_source_directory_rejected_without_git(self):
        with self.assertRaises(PolicyError):
            init_run(self.source, 'report', self.source / 'reports')
    def test_relative_root_rejected(self):
        with self.assertRaises(PolicyError):
            init_run(self.source, 'report', Path('reports'))
    def test_skill_directory_rejected(self):
        from report_workspace import SKILL_ROOT
        with self.assertRaises(PolicyError):
            assert_external(SKILL_ROOT / 'qa', self.source)
    def test_other_git_repo_rejected(self):
        self.output.mkdir(); (self.output / '.git').mkdir()
        with self.assertRaises(PolicyError):
            init_run(self.source, 'report', self.output / 'reports')
    def test_worktree_gitfile_rejected(self):
        self.output.mkdir(); (self.output / '.git').write_text('gitdir: /not/followed')
        with self.assertRaises(PolicyError):
            assert_external(self.output / 'reports', self.source)
    def test_bare_repo_rejected(self):
        self.output.mkdir(); (self.output/'HEAD').write_text('ref: refs/heads/main')
        (self.output/'objects').mkdir(); (self.output/'refs').mkdir()
        with self.assertRaises(PolicyError):
            assert_external(self.output/'reports', self.source)
    def test_symlink_from_source_outside_rejected(self):
        self.output.mkdir(); (self.source / 'alias').symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(PolicyError):
            init_run(self.source, 'report', self.source / 'alias')
    def test_symlink_into_source_rejected(self):
        (self.base / 'alias').symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(PolicyError):
            init_run(self.source, 'report', self.base / 'alias' / 'reports')
    def test_source_alias_escape_rejected(self):
        alias = self.base/'source-alias'; alias.symlink_to(self.source, target_is_directory=True)
        self.output.mkdir(); (self.source/'out').symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(PolicyError):
            init_run(alias, 'report', alias/'out')
    def test_invalid_topic_rejected(self):
        for topic in ['../../escape', '', '客户名字', 'x'*49]:
            with self.subTest(topic=topic), self.assertRaises(PolicyError):
                init_run(self.source, topic, self.output)
    def test_runs_are_unique(self):
        a=init_run(self.source,'report',self.output); b=init_run(self.source,'report',self.output)
        self.assertNotEqual(a,b)
    def test_manifest_defaults_do_not_authorize_publish(self):
        run=init_run(self.source,'report',self.output)
        _,meta=load_run(run)
        self.assertEqual(meta['publication_status'],'not_requested')
        self.assertTrue(check_run(run)['ok'])
    def test_moved_run_rejected(self):
        run=init_run(self.source,'report',self.output)
        moved=run.with_name('moved');run.rename(moved)
        with self.assertRaises(PolicyError): load_run(moved)
    def test_symlink_inside_run_rejected(self):
        run=init_run(self.source,'report',self.output)
        (run/'qa'/'source').symlink_to(self.source,target_is_directory=True)
        self.assertFalse(check_run(run)['ok'])
    def test_symlink_manifest_rejected(self):
        run=init_run(self.source,'report',self.output)
        saved=run/'manifest.saved';(run/'manifest.json').rename(saved)
        (run/'manifest.json').symlink_to(saved)
        with self.assertRaises(PolicyError): load_run(run)
    def test_gitmarker_inside_run_rejected(self):
        run=init_run(self.source,'report',self.output)
        (run/'qa'/'.git').mkdir()
        self.assertFalse(check_run(run)['ok'])
    def test_environment_root(self):
        with patch.dict(os.environ, {'EXPLAIN_REPORT_HOME': str(self.output)}):
            self.assertEqual(default_home(),self.output)
    def test_relative_environment_rejected(self):
        with patch.dict(os.environ, {'EXPLAIN_REPORT_HOME':'relative'}):
            with self.assertRaises(PolicyError): default_home()
    def test_existing_staged_image_preserved(self):
        self.repo();(self.source/'existing.png').write_bytes(b'fixture')
        self.git('add','existing.png')
        before=self.git('ls-files','--stage')
        run=init_run(self.source,'report',self.output)
        self.assertTrue(check_run(run)['ok'])
        self.assertEqual(before,self.git('ls-files','--stage'))
    def test_new_untracked_image_detected(self):
        self.repo();run=init_run(self.source,'report',self.output)
        (self.source/'accidental.png').write_bytes(b'fixture')
        result=check_run(run)
        self.assertFalse(result['ok']);self.assertIn('accidental.png',result['repository_image_candidates'])
        self.assertTrue((self.source/'accidental.png').exists())
    def test_new_staged_svg_detected(self):
        self.repo();run=init_run(self.source,'report',self.output)
        (self.source/'accidental.svg').write_text('<svg/>');self.git('add','accidental.svg')
        self.assertFalse(check_run(run)['ok'])
    def test_existing_image_content_change_detected(self):
        self.repo();(self.source/'existing.png').write_bytes(b'before');self.git('add','existing.png')
        run=init_run(self.source,'report',self.output)
        (self.source/'existing.png').write_bytes(b'after')
        self.assertFalse(check_run(run)['ok'])
    def test_unrelated_text_changes_not_reverted(self):
        self.repo();run=init_run(self.source,'report',self.output)
        (self.source/'work.py').write_text('answer=42')
        self.assertTrue(check_run(run)['ok']);self.assertTrue((self.source/'work.py').exists())
    def test_nested_source_protects_repo_root(self):
        self.repo();nested=self.source/'sub';nested.mkdir()
        with self.assertRaises(PolicyError):init_run(nested,'report',self.source/'reports')
    def test_posix_private_run_permissions(self):
        if os.name != 'posix':self.skipTest('POSIX only')
        run=init_run(self.source,'report',self.output)
        self.assertEqual(run.stat().st_mode & 0o777,0o700)
        self.assertEqual((run/'manifest.json').stat().st_mode & 0o777,0o600)
    def test_custom_output_directory_allows_repo_doc_and_keeps_run_external(self):
        self.repo()
        custom_dir = self.source / 'docs' / 'reports'
        run = init_run(self.source, 'sync-adr', self.output, output=custom_dir)
        _, meta = load_run(run)
        expected = custom_dir.resolve() / 'sync-adr.html'
        self.assertEqual(resolve_report_html(run, meta), expected)
        self.assertEqual(meta['output_path'], str(expected))
        expected.write_text('<!doctype html><title>ok</title>')
        self.assertTrue(check_run(run)['ok'])
    def test_custom_output_explicit_html_and_output_dir_mode(self):
        explicit = self.source / 'custom-brief.html'
        run = init_run(self.source, 'sync-adr', self.output, output=explicit)
        _, meta = load_run(run)
        self.assertEqual(resolve_report_html(run, meta), explicit.resolve())
        dir_run = init_run(self.source, 'sync-adr', self.output, output=self.source / 'my.folder', output_is_dir=True)
        _, dir_meta = load_run(dir_run)
        self.assertEqual(resolve_report_html(dir_run, dir_meta), (self.source / 'my.folder/sync-adr.html').resolve())
        existing_file = self.source / 'not-a-dir.txt'
        existing_file.write_text('x')
        with self.assertRaises(PolicyError):
            init_run(self.source, 'sync-adr', self.output, output=existing_file, output_is_dir=True)
    def test_custom_output_inside_skill_source_rejected(self):
        from report_workspace import SKILL_ROOT
        with self.assertRaises(PolicyError):
            init_run(self.source, 'bad', self.output, output=SKILL_ROOT / 'bad.html')

if __name__=='__main__':unittest.main()
