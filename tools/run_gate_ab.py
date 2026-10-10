#!/usr/bin/env python3
"""Collect fresh Gate A/B evidence on macOS/Linux/Windows without design edits.

Exit 0: requested automated checks passed; 1: execution/check failed;
2: --strict-gates requested and engineering gates remain blocked.
--with-drc includes unfinished PCB DRC as a blocking automated check.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from kicad_native import extract_forms, property_value

ROOT = Path(__file__).resolve().parents[1]
SCH = ROOT / 'hardware/ax7010_servo_reva.kicad_sch'
BOARD = ROOT / 'hardware/ax7010_servo_reva.kicad_pcb'


def source_hashes() -> dict[str, str]:
    paths = set()
    for directory in ('hardware', 'fpga', 'tools', '.github/workflows'):
        for path in (ROOT / directory).rglob('*'):
            if (path.is_file() and '.history' not in path.parts
                    and '__pycache__' not in path.parts
                    and path.suffix not in ('.pyc', '.kicad_prl', '.lck')):
                paths.add(path)
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/gate-ab')
    parser.add_argument('--kicad-cli', default='kicad-cli')
    parser.add_argument('--ngspice', default='ngspice')
    parser.add_argument('--with-drc', action='store_true')
    parser.add_argument('--strict-gates', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')
    out = Path(tempfile.mkdtemp(prefix=stamp, dir=args.output.resolve()))
    report = {
        'schema_version': 1, 'started_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'FAILED', 'source_hashes_before': source_hashes(), 'steps': [],
        'tools': {'python': sys.version},
        'erc': {'status': 'NOT_RUN'}, 'drc': {'status': 'NOT_RUN'},
        'gate_a': {'status': 'BLOCKED'}, 'gate_b': {'status': 'BLOCKED'},
        'scope': 'Automated evidence only; no engineering or fabrication sign-off',
    }

    def run(name: str, command: list[str], timeout: int = 180) -> int:
        # Never dump the environment; subprocess inherits it without logging it.
        record = {'name': name, 'command': command, 'log': name + '.log'}
        try:
            proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                  timeout=timeout)
            record['exit_code'] = proc.returncode
            log = proc.stdout + '\n' + proc.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            record['exit_code'] = 1
            log = str(exc)
        (out / record['log']).write_text(log, encoding='utf-8')
        report['steps'].append(record)
        print(f"{name}: exit {record['exit_code']}", flush=True)
        return record['exit_code']

    def native_summary(name: str, path: Path, code: int) -> None:
        result = {'status': 'FAILED', 'exit_code': code}
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
            def invalid(reason: str) -> None:
                result['error'] = reason
                report[name] = result

            if (not isinstance(data, dict)
                    or data.get('$schema') != f'https://schemas.kicad.org/{name}.v1.json'
                    or data.get('source') != (SCH.name if name == 'erc' else BOARD.name)
                    or not isinstance(data.get('date'), str)
                    or not str(data.get('kicad_version', '')).startswith('10.')
                    or not isinstance(data.get('included_severities'), list)
                    or not {'error', 'warning', 'exclusion'}.issubset(data['included_severities'])
                    or not isinstance(data.get('ignored_checks'), list)):
                invalid('Missing or invalid native report metadata')
                return
            if name == 'erc':
                def expected_sheets(path: Path, prefix: str) -> set[str]:
                    result = {prefix}
                    for sheet in extract_forms(path.read_text(encoding='utf-8'), 'sheet'):
                        uuid = re.search(r'\(uuid\s+"([^"]+)"', sheet.text).group(1)
                        filename = property_value(sheet.text, 'Sheetfile')
                        result |= expected_sheets(path.parent / filename, prefix + '/' + uuid)
                    return result

                root_uuid = re.search(r'\(uuid\s+"([^"]+)"', SCH.read_text(encoding='utf-8')).group(1)
                expected = expected_sheets(SCH, '/' + root_uuid)
                sheets = data.get('sheets')
                if (not isinstance(sheets, list) or len(sheets) != len(expected)
                        or any(not isinstance(s, dict) or not isinstance(s.get('violations'), list)
                               for s in sheets)
                        or {s.get('uuid_path') for s in sheets} != expected):
                    invalid('ERC sheet coverage or explicit violations arrays missing')
                    return
                items = [item for sheet in sheets for item in sheet['violations']]
            else:
                required = ('violations', 'unconnected_items', 'schematic_parity')
                if any(not isinstance(data.get(key), list) for key in required):
                    invalid('DRC collections missing')
                    return
                items = data['violations']
            if any(not isinstance(x, dict) or x.get('severity') not in
                   ('error', 'warning', 'exclusion') for x in items):
                invalid('Invalid violation record')
                return
            result.update({
                'errors': sum(x.get('severity') == 'error' for x in items),
                'warnings': sum(x.get('severity') == 'warning' for x in items),
                'exclusions': sum(x.get('severity') == 'exclusion' or bool(x.get('excluded', False)) for x in items),
                'violations': len(items),
                'ignored_checks': data.get('ignored_checks', []),
                'included_severities': data.get('included_severities', []),
            })
            if name == 'drc':
                result['unconnected'] = len(data.get('unconnected_items', []))
                result['schematic_parity'] = len(data.get('schematic_parity', []))
            # Require native exit success plus an explicitly present report structure.
            structure = 'sheets' if name == 'erc' else 'violations'
            result['status'] = ('PASS' if code == 0 and structure in data
                                and not items and not result.get('unconnected', 0)
                                and not result.get('schematic_parity', 0) else 'FAILED')
        report[name] = result

    try:
        run('git_sha', ['git', 'rev-parse', 'HEAD'])
        run('git_status', ['git', 'status', '--short'])
        report['git_sha'] = (out / 'git_sha.log').read_text().strip()
        cli = shutil.which(args.kicad_cli)
        if cli is None and args.kicad_cli == 'kicad-cli':
            fallback = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
            if fallback.is_file():
                cli = str(fallback)
        if cli is None:
            raise RuntimeError(f'KiCad CLI unavailable: {args.kicad_cli}')
        if run('kicad_version', [cli, '--version']):
            raise RuntimeError('KiCad version query failed')
        report['tools']['kicad'] = (out / 'kicad_version.log').read_text().strip()
        if not report['tools']['kicad'].startswith('10.'):
            raise RuntimeError('This project requires KiCad 10')
        if run('ngspice_version', [args.ngspice, '--version']):
            raise RuntimeError('ngspice version query failed')
        report['tools']['ngspice'] = (out / 'ngspice_version.log').read_text().strip()
        erc_code = run('erc', [cli, 'sch', 'erc', '--severity-all',
                               '--exit-code-violations', '--format', 'json',
                               '-o', str(out / 'erc.json'), str(SCH)])
        native_summary('erc', out / 'erc.json', erc_code)
        xml = out / 'netlist.xml'
        net = out / 'board.net'
        xml_ok = run('export_xml', [cli, 'sch', 'export', 'netlist', '--format',
                                   'kicadxml', '-o', str(xml), str(SCH)]) == 0 and xml.is_file()
        net_ok = run('export_native', [cli, 'sch', 'export', 'netlist',
                                      '-o', str(net), str(SCH)]) == 0 and net.is_file()
        for check in ('native_schematic', 'kicad_grid', 'schematic_layout',
                      'schematic_connectivity', 'power_wiring', 'design'):
            run('check_' + check, [sys.executable, str(ROOT / f'tools/check_{check}.py')])
        for name, location in [('pcb_regressions', 'tools/test_pcb_checks.py'),
                               ('tutorial_regressions', 'tools/ai_pcb_guide/tests/test_board_parity_audit.py')]:
            run(name, [sys.executable, str(ROOT / location)])
        if net_ok:
            for check in ('netlist_safety', 'ocp_behavior', 'pcb_parity', 'pcb_constraints'):
                run('check_' + check, [sys.executable, str(ROOT / f'tools/check_{check}.py'), str(net)])
        if xml_ok:
            run('adc_regressions', [sys.executable, str(ROOT / 'tools/test_adc_validity.py'),
                                    '--netlist', str(xml), '-v'])
            run('adc_validity', [sys.executable, str(ROOT / 'tools/check_adc_validity.py'),
                                 str(xml), '--output', str(out / 'adc_validity.json')])
            run('qualification', [sys.executable, str(ROOT / 'tools/gate_ab_verify.py'),
                                  '--netlist', str(xml), '--output', str(out / 'qualification.json'),
                                  '--spice-output', str(out / 'spice'), '--ngspice', args.ngspice])
            # Set only the two test inputs; never inspect or serialize inherited values.
            os.putenv('GATE_AB_NETLIST', str(xml))
            os.putenv('GATE_AB_NGSPICE', args.ngspice)
            run('gate_ab_regressions', [sys.executable, '-m', 'unittest', 'discover',
                                       '-s', 'tools', '-p', 'test_gate_ab_verify.py', '-v'])
        if args.with_drc:
            code = run('drc', [cli, 'pcb', 'drc', '--schematic-parity', '--refill-zones',
                               '--severity-all', '--exit-code-violations', '--format', 'json',
                               '-o', str(out / 'drc.json'), str(BOARD)], timeout=300)
            native_summary('drc', out / 'drc.json', code)
        if not xml_ok or not net_ok:
            raise RuntimeError('Fresh export failed; dependent checks were not run')
        if any(x['exit_code'] for x in report['steps']):
            raise RuntimeError('One or more checks failed; see step logs')
        if report['erc']['status'] != 'PASS' or (args.with_drc and report['drc']['status'] != 'PASS'):
            raise RuntimeError('Native report did not establish a clean result')
        report['status'] = 'PASS_AUTOMATED_ONLY'
    except (OSError, ValueError, RuntimeError) as exc:
        report['error'] = str(exc)
    finally:
        report['source_hashes_after'] = source_hashes()
        if report['source_hashes_before'] != report['source_hashes_after']:
            report['status'] = 'FAILED'
            report['error'] = 'Source files changed during evidence collection'
        report['artifacts_sha256'] = {
            str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.rglob('*')) if p.is_file()
        }
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        (out / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f"Evidence: {out}\nAutomated: {report['status']}; Gate A/B: BLOCKED")
    if report['status'] == 'FAILED':
        return 1
    return 2 if args.strict_gates else 0


if __name__ == '__main__':
    raise SystemExit(main())
