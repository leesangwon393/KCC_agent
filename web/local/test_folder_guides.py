import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from folder_guides import folder_summary, validate_folders, write_guides


class FolderGuidesTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        self.data.mkdir()
        self.folders = [self.root / '강의', self.root / '영수증']
        for folder in self.folders:
            folder.mkdir()

    def test_selected_folders_get_grounded_guides_and_existing_readme_is_preserved(self):
        (self.folders[0] / '운영관리-강의.pdf').write_bytes(b'not read')
        (self.folders[0] / 'README.md').write_text('Owner README')
        outside = self.root / 'outside.txt'
        outside.write_text('PRIVATE CONTENT')
        (self.folders[0] / 'outside-link').symlink_to(outside)
        seen = []
        def generate(summary):
            seen.append(summary)
            return '# 폴더 지침\n강의 관련 자료를 보관합니다.\n'
        result = write_guides(self.folders, self.data, generate, lambda *_: None)
        self.assertEqual(len(result), 2)
        self.assertCountEqual(seen[0]['entries'], [
            {'name': 'README.md', 'kind': 'file'}, {'name': '운영관리-강의.pdf', 'kind': 'file'}
        ])
        self.assertEqual((self.folders[0] / 'README.md').read_text(), 'Owner README')
        self.assertNotIn('PRIVATE CONTENT', json.dumps(seen))
        projects = json.loads((self.data / 'projects.json').read_text())
        self.assertEqual({v['folder'] for v in projects.values()}, {str(f) for f in self.folders})
        self.assertFalse((self.root / '_project.md').exists())

    def test_existing_guidance_is_reused_without_model_or_overwrite(self):
        for folder in self.folders:
            (folder / '_project.md').write_text('My existing rules')
        write_guides(self.folders, self.data, None, lambda *_: None)
        for folder in self.folders:
            self.assertEqual((folder / '_project.md').read_text(), 'My existing rules')

    def test_failure_keeps_previous_selection_and_retry_reuses_successful_guides(self):
        previous = '{"previous":{}}'
        (self.data / 'projects.json').write_text(previous)
        calls = []
        def generate(summary):
            calls.append(summary['folder'])
            if len(calls) == 2:
                raise ValueError('model failed')
            return '# Guide\nTest'
        with self.assertRaises(ValueError):
            write_guides(self.folders, self.data, generate, lambda *_: None)
        self.assertEqual((self.data / 'projects.json').read_text(), previous)
        self.assertTrue((self.folders[0] / '_project.md').exists())
        write_guides(self.folders, self.data, lambda _: '# Retry', lambda *_: None)
        self.assertEqual((self.folders[0] / '_project.md').read_text(), '# Guide\nTest')

    def test_paths_are_limited_and_symlink_guide_cannot_write_outside_selection(self):
        for values in [[], ['relative'], [str(self.root), str(self.folders[0])], [str(self.root / 'missing')]]:
            with self.assertRaises((ValueError, OSError)):
                validate_folders(values)
        self.assertEqual(validate_folders([str(self.folders[0])] * 2), [self.folders[0].resolve()])
        target = self.root / 'owner.md'
        target.write_text('Keep')
        (self.folders[0] / '_project.md').symlink_to(target)
        with self.assertRaises(ValueError):
            write_guides(self.folders, self.data, lambda _: '# Replace', lambda *_: None)
        self.assertEqual(target.read_text(), 'Keep')

class AddFolderTests(unittest.TestCase):
    setUp = FolderGuidesTests.setUp
    def test_append_preserves_existing_metadata_and_generates_only_new_folder(self):
        existing = {'legacy-key': {'name': 'My existing', 'folder': str(self.folders[0].resolve()), 'keywords': ['custom']}}
        (self.data / 'projects.json').write_text(json.dumps(existing))
        (self.folders[0] / '_project.md').write_text('Owner rules')
        called = []
        def generate(summary):
            called.append(summary['folder'])
            return '# New folder guide'
        write_guides([f.resolve() for f in self.folders], self.data, generate, lambda *_: None, append=True)
        result = json.loads((self.data / 'projects.json').read_text())
        self.assertEqual(result['legacy-key'], existing['legacy-key'])
        self.assertEqual(len(result), 2)
        self.assertEqual(called, [self.folders[1].name])
        self.assertEqual((self.folders[0] / '_project.md').read_text(), 'Owner rules')
        write_guides([self.folders[1].resolve()], self.data, None, lambda *_: None, append=True)
        self.assertEqual(json.loads((self.data / 'projects.json').read_text()), result)

    def test_append_failure_and_nested_selection_preserve_current_projects(self):
        existing = {'old': {'name': 'Keep', 'folder': str(self.folders[0].resolve())}}
        original = json.dumps(existing)
        (self.data / 'projects.json').write_text(original)
        with self.assertRaises(RuntimeError):
            write_guides([self.folders[1].resolve()], self.data,
                         lambda _: (_ for _ in ()).throw(RuntimeError('model failed')), lambda *_: None, append=True)
        self.assertEqual((self.data / 'projects.json').read_text(), original)
        child = self.folders[0] / 'child'; child.mkdir()
        with self.assertRaises(ValueError):
            write_guides([child.resolve()], self.data, None, lambda *_: None, append=True)
        self.assertEqual((self.data / 'projects.json').read_text(), original)
