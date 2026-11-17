from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_public import inspect_text
import check_public


class PublicCheckTests(unittest.TestCase):
    def test_unreviewed_and_binary_files_are_blocked(self):
        self.assertTrue(inspect_text('private/archive.json', b'{}'))
        self.assertTrue(inspect_text('README.md', b'\xff'))

    def test_likely_secrets_are_flagged_without_echoing_values(self):
        samples = [
            'AK' + 'IA' + 'A' * 16,
            'gh' + 'p_' + 'x' * 36,
            '-----BEGIN ' + 'PRIVATE KEY-----',
            'postgresql://' + 'example:generated-secret@localhost/db',
            'ETHICA_APP_' + 'PASSWORD=' + 'f' * 64,
            '/' + 'Users/' + 'example/private.txt',
        ]
        for sample in samples:
            with self.subTest(kind=sample[:5]):
                errors = inspect_text('README.md', sample.encode())
                self.assertTrue(errors)
                self.assertNotIn(sample, '\n'.join(errors))

    def test_generic_public_material_passes(self):
        self.assertEqual(inspect_text('README.md', b'Fresh instances begin with zero memories.'), [])

    def test_staged_secret_is_found_after_worktree_is_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True, capture_output=True)
            path = root / 'README.md'
            path.write_text('gh' + 'p_' + 'x' * 36)
            subprocess.run(['git', '-C', directory, 'add', 'README.md'], check=True, capture_output=True)
            path.write_text('Public text without the staged credential.')
            with patch.object(check_public, 'ROOT', root), patch.object(check_public, 'PUBLIC_FILES', {'README.md'}):
                _, errors = check_public.check()
            self.assertTrue(any(e.startswith('index: README.md: possible provider token') for e in errors))


if __name__ == '__main__':
    unittest.main()
