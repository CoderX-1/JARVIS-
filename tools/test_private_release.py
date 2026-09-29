import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from private_release import build, decrypt_private, encrypt_private, unpack


class PrivateReleaseTests(unittest.TestCase):
    def test_encryption_authenticates_password_and_ciphertext(self):
        payload = b'OPENAI_API_KEY=fixture-not-a-real-key\n'
        envelope = encrypt_private(payload, 'example passphrase at least sixteen')
        self.assertEqual(decrypt_private(envelope, 'example passphrase at least sixteen'), payload)
        self.assertNotIn('fixture-not-a-real-key', json.dumps(envelope))
        with self.assertRaisesRegex(ValueError, 'Wrong passphrase'):
            decrypt_private(envelope, 'wrong passphrase')
        envelope['ciphertext'] = envelope['ciphertext'][:-4] + 'AAAA'
        with self.assertRaises(ValueError):
            decrypt_private(envelope, 'example passphrase at least sixteen')

    def test_fixture_release_round_trip_and_wrong_password_leaves_no_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, live, models = (root / name for name in ('source', 'live', 'models'))
            for directory in (source / 'tools', source / 'core', live / 'config', models):
                directory.mkdir(parents=True, exist_ok=True)
            (source / 'RUN-JARVIS.ps1').write_text('Write-Host "fixture"', encoding='utf-8')
            (source / 'tools' / 'private_release.py').write_text('# fixture', encoding='utf-8')
            (source / 'tools' / 'Install-JARVIS.ps1').write_text('# fixture', encoding='utf-8')
            (source / 'core' / 'agent.py').write_text('# fixture', encoding='utf-8')
            (live / '.env').write_text('OPENAI_API_KEY=fixture-not-a-real-key\n', encoding='utf-8')
            configs = {
                'backtalk.json': {'agent_dir': 'C:/Projects/JARVIS', 'extra_dirs': ['private'],
                                  'mic_device': 'old mic'},
                'barehands.json': {'orbs': [{'kind': 'notes', 'path': 'C:/private'},
                                             {'kind': 'media', 'path': 'media'}]},
                'ai-visualizer.json': {'bus_dir': 'C:/Projects/JARVIS/runtime/signals'},
            }
            for name, data in configs.items():
                (live / 'config' / name).write_text(json.dumps(data), encoding='utf-8')
            (models / 'fixture.bin').write_bytes(b'local model')
            subprocess.run(['git', 'init', '-q'], cwd=source, check=True)
            archive = root / 'JARVIS-private-release.zip'
            build(source, live / '.env', live / 'config', models, archive,
                  'example passphrase at least sixteen')
            self.assertNotIn(b'fixture-not-a-real-key', archive.read_bytes())
            damaged = root / 'damaged.zip'
            with zipfile.ZipFile(archive) as original, zipfile.ZipFile(damaged, 'w') as changed:
                for name in original.namelist():
                    content = original.read(name)
                    changed.writestr(name, b'tampered' if name == 'app/models/fixture.bin' else content)
            with self.assertRaisesRegex(ValueError, 'length mismatch|checksum mismatch'):
                unpack(damaged, root / 'bad-install', 'example passphrase at least sixteen')
            forged = root / 'forged.zip'
            with zipfile.ZipFile(archive) as original, zipfile.ZipFile(forged, 'w') as changed:
                manifest = json.loads(original.read('manifest.json'))
                manifest['app/models/fixture.bin'] = {
                    'sha256': hashlib.sha256(b'tampered').hexdigest(), 'bytes': len(b'tampered')}
                for name in original.namelist():
                    content = original.read(name)
                    if name == 'app/models/fixture.bin':
                        content = b'tampered'
                    elif name == 'manifest.json':
                        content = json.dumps(manifest, sort_keys=True).encode('utf-8')
                    changed.writestr(name, content)
            with self.assertRaisesRegex(ValueError, 'authentication failed'):
                unpack(forged, root / 'forged-install', 'example passphrase at least sixteen')
            target = root / 'installed'
            with self.assertRaisesRegex(ValueError, 'Wrong passphrase'):
                unpack(archive, target, 'wrong password')
            self.assertFalse(target.exists())
            result = unpack(archive, target, 'example passphrase at least sixteen')
            self.assertFalse(result['dependencies_ready'])
            self.assertEqual((target / '.env').read_text(encoding='utf-8'),
                             'OPENAI_API_KEY=fixture-not-a-real-key\n')
            self.assertEqual((target / 'models' / 'fixture.bin').read_bytes(), b'local model')
            config = json.loads((target / 'config' / 'backtalk.json').read_text(encoding='utf-8'))
            self.assertEqual(config['agent_dir'], target.as_posix())
            self.assertNotIn('mic_device', config)
            self.assertEqual(config['extra_dirs'], [])
            with self.assertRaisesRegex(ValueError, 'already'):
                unpack(archive, target, 'example passphrase at least sixteen')

    def test_rejects_extra_unmanifested_zip_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('manifest.json', '{}')
                archive.writestr('private/secrets.json', json.dumps(
                    encrypt_private(b'{"env":"","configs":{}}', 'long example passphrase')))
                archive.writestr('Install-JARVIS.ps1', '')
                archive.writestr('app/../escape.txt', 'bad')
            with self.assertRaises(ValueError):
                unpack(path, Path(folder) / 'installed', 'long example passphrase')


if __name__ == '__main__':
    unittest.main()
