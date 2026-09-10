import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('obsidian_install', ROOT / 'obsidian-setup/install.py')
install = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(install)


class ObsidianSetupTests(unittest.TestCase):
    def test_existing_vault_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'existing'
            target.mkdir()
            note = target / 'mine.md'
            note.write_text('private original')
            with self.assertRaises(FileExistsError):
                install.build(target, 'Researcher')
            self.assertEqual(note.read_text(), 'private original')

    def test_owner_cannot_inject_yaml_or_paths(self):
        for owner in ['A\nstatus: done', '../private', '<script>', 'A"B', '']:
            with self.subTest(owner=owner), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    install.build(Path(tmp) / 'new', owner)

    def test_checksum_mismatch_leaves_no_partial_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'new'
            with patch.object(install, 'read_asset', return_value=b'corrupt payload'):
                with self.assertRaisesRegex(ValueError, 'SHA-256'):
                    install.build(target, 'Researcher')
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_display_patch_checks_both_hashes(self):
        before = 'alpha beta'; after = 'alpha gamma'
        spec = {'before_sha256':hashlib.sha256(before.encode()).hexdigest(),
                'after_sha256':hashlib.sha256(after.encode()).hexdigest(),
                'edits':[{'start':6,'end':10,'text':'gamma'}]}
        self.assertEqual(install.apply_display_patch(before.encode(), spec), after.encode())
        with self.assertRaises(ValueError):
            install.apply_display_patch(b'different version', spec)
        spec['after_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            install.apply_display_patch(before.encode(), spec)

    def test_public_configuration_has_no_personal_state(self):
        root = ROOT / 'obsidian-setup/vault'
        operon = json.loads((root / '.obsidian/plugins/operon/data.json').read_text())
        self.assertFalse(operon['automation']['taskAutomationPolicy']['fileTaskAutoArchiveEnabled'])
        self.assertEqual(operon['state']['pinnedTasks']['itemsById'], {})
        self.assertEqual(operon['views']['kanbanOrder']['boards'], {})
        self.assertEqual(operon['integrations']['externalCalendarSources']['sources'], [])
        self.assertEqual(operon['integrations']['developerApi']['consumersById'], {})
        for p in root.rglob('*'):
            if p.is_file():
                self.assertNotIn('runtime', p.parts)
                self.assertNotRegex(p.read_text(), r'/(?:Users|home)/[^/\s]+/')

    def test_locked_plugins_match_enabled_configuration(self):
        root = ROOT / 'obsidian-setup'
        lock = json.loads((root/'plugins.lock.json').read_text())['plugins']
        enabled = json.loads((root/'vault/.obsidian/community-plugins.json').read_text())
        self.assertEqual(len(lock), 16)
        self.assertEqual(set(enabled), {p['id'] for p in lock if p['enabled']})
        self.assertEqual(len(enabled), 14)
        for plugin in lock:
            self.assertTrue({'main.js','manifest.json'} <= {a['name'] for a in plugin['assets']})
            self.assertTrue(all(a['url'].startswith('https://github.com/') for a in plugin['assets']))

    def test_workspace_and_table_resolve_current_operon_presets(self):
        root = ROOT / 'obsidian-setup/vault'
        config = json.loads((root/'.obsidian/plugins/operon/data.json').read_text())
        presets = {p['id'] for p in config['views']['kanbanPresets']['kanbanPresets']}
        workspace = json.loads((root/'.obsidian/workspace.json').read_text())
        leaves = workspace['main']['children'][0]['children']
        self.assertEqual({leaf['state']['state']['presetId'] for leaf in leaves}, presets)
        dashboard = (root/'Dashboard.md').read_text()
        self.assertIn('```operon-table\n', dashboard)
        binding = config['views']['tablePresets']['fileBindings'][0]
        self.assertIn(binding['id'], dashboard)
        self.assertEqual(json.loads((root/binding['path']).read_text())['id'], binding['id'])


if __name__ == '__main__':
    unittest.main()
