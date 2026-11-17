import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from new_agent import ROOT, foundation, initialize, literal
from render_concepts import render


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_fresh_instances_have_independent_state(self):
        first = initialize(self.base / 'first', 'first', 55432)
        second = initialize(self.base / 'second', 'second', 55433)
        self.assertNotEqual(first['instance_id'], second['instance_id'])
        a = json.loads((self.base / 'first/instance.json').read_text())
        b = json.loads((self.base / 'second/instance.json').read_text())
        self.assertNotEqual(a['compose_project'], b['compose_project'])
        self.assertNotEqual((self.base / 'first/.env').read_text(), (self.base / 'second/.env').read_text())
        self.assertEqual(first['memories'], 0)
        self.assertEqual((self.base / 'first/foundation.json').read_bytes(), (ROOT / 'foundation/concepts.json').read_bytes())
        sql = (self.base / 'first/init/30-foundation.sql').read_text()
        self.assertEqual(sql.count('INSERT INTO ethica.concepts'), 17)
        self.assertNotIn('INSERT INTO ethica.memories', sql)
        self.assertEqual(stat.S_IMODE((self.base / 'first/.env').stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.base / 'first').stat().st_mode), 0o700)
        self.assertNotIn('PASSWORD', (self.base / 'first/init/30-foundation.sql').read_text())

    def test_existing_instance_is_untouched(self):
        target = self.base / 'existing'
        target.mkdir()
        marker = target / 'keep.txt'
        marker.write_text('keep this')
        with self.assertRaises(ValueError):
            initialize(target, 'valid')
        self.assertEqual(marker.read_text(), 'keep this')

    def test_public_tree_and_symlink_to_it_are_rejected(self):
        with self.assertRaises(ValueError):
            initialize(ROOT / 'instances/new', 'new')
        alias = self.base / 'alias'
        alias.symlink_to(ROOT, target_is_directory=True)
        with self.assertRaises(ValueError):
            initialize(alias / 'private-agent', 'new')

    def test_input_cannot_change_sql_or_compose_structure(self):
        for agent_id in ('../escape', 'UPPER', "bad';--", 'a\nservices:', '', '-x'):
            with self.subTest(agent_id=agent_id), self.assertRaises(ValueError):
                initialize(self.base / 'bad', agent_id)
        for port in (0, 543, 65536, '55432', True):
            with self.subTest(port=port), self.assertRaises(ValueError):
                initialize(self.base / 'bad', 'valid', port)
        self.assertFalse((self.base / 'bad').exists())
        self.assertEqual(literal("someone's account"), "'someone''s account'")
        with self.assertRaises(ValueError):
            literal('bad\x00text')

    def test_render_preserves_every_statement_and_meaning(self):
        text = render()
        for row in foundation():
            self.assertIn(row['concept'], text)
            self.assertIn(row['meaning'], text)
        self.assertEqual((ROOT / 'foundation/concepts.md').read_text(), text)


if __name__ == '__main__':
    unittest.main()
