import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
#!/usr/bin/env python3
"""Exercise the evidence runner's failure isolation at its CLI boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil

ROOT = Path(__file__).resolve().parents[2]


class RunnerTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ngspice') and sys.platform != 'win32',
                         'Requires ngspice and POSIX executable script')
    def test_incomplete_native_erc_report_cannot_claim_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            cli = out / 'fake-kicad'
            cli.write_text('#!' + sys.executable + "\n" +
                           "import sys, pathlib\n" +
                           "if '--version' in sys.argv: print('10.0.3'); sys.exit(0)\n" +
                           "if 'erc' in sys.argv:\n" +
                           "    pathlib.Path(sys.argv[sys.argv.index('--output')+1]).write_text('{\"sheets\":[{}]}')\n" +
                           "    sys.exit(0)\n" +
                           "sys.exit(1)\n")
            cli.chmod(0o755)
            result = subprocess.run([
                sys.executable, str(ROOT / 'tools/pcb.py'), 'verify', '--project', 'ads8588s', '--scope', 'schematic',
                '--output', str(out), '--kicad-cli', str(cli),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            record = json.loads(next(out.glob('*/manifest.json')).read_text())['evidence']
            self.assertEqual(record['erc']['status'], 'FAIL')

    def test_schematic_scope_cannot_request_pcb_release_drc(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / 'tools/pcb.py'), 'verify', '--project', 'ads8588s', '--scope', 'schematic',
                '--output', folder, '--with-drc'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 64)
            self.assertFalse(list(Path(folder).glob('*/manifest.json')))

    def test_schematic_scope_does_not_turn_missing_tools_into_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / 'tools/pcb.py'), 'verify', '--project', 'ads8588s', '--scope', 'schematic',
                '--output', folder, '--kicad-cli', str(Path(folder) / 'missing-cli')],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            record = json.loads(next(Path(folder).glob('*/manifest.json')).read_text())['evidence']
            self.assertTrue(any(s['exit_code'] for s in record['steps']))
            self.assertEqual(record['delivery_scope'], 'SCHEMATIC_BOM')
            self.assertEqual(record['pcb_release'], 'BLOCKED')
            self.assertEqual(record['gate_a']['status'], 'BLOCKED')

    def test_missing_cli_writes_failure_and_does_not_reuse_old_netlist(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            (out / 'netlist.xml').write_text('historical netlist')
            for _ in range(2):
                result = subprocess.run([
                    sys.executable, str(ROOT / 'tools/pcb.py'), 'verify', '--project', 'ads8588s', '--scope', 'schematic',
                    '--output', str(out), '--kicad-cli', str(out / 'missing-kicad'),
                ], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
            manifests = list(out.glob('*/manifest.json'))
            self.assertEqual(len(manifests), 2)
            for path in manifests:
                record = json.loads(path.read_text())['evidence']
                self.assertTrue(any(s['exit_code'] for s in record['steps']))
                self.assertEqual(record['erc']['status'], 'NOT_RUN')
                self.assertEqual(record['gate_a']['status'], 'BLOCKED')
                self.assertFalse((path.parent / 'netlist.xml').exists())
                self.assertTrue(record['source_hashes_before'])
                self.assertEqual(record['source_hashes_before'], record['source_hashes_after'])
            self.assertEqual((out / 'netlist.xml').read_text(), 'historical netlist')


if __name__ == '__main__':
    unittest.main()
