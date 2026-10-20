"""Prototype gates reject stale, incomplete and suppressed evidence."""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import load_project
from pcbtools.verification import native_summary


class ManufacturingTests(unittest.TestCase):
    def test_actual_frozen_manufacturing_intent_has_its_required_profile(self):
        from pcbtools.manufacturing import freeze_design, check_frozen_design
        from pcbtools.rules.fabrication_intent import check_project

        repo = Path(__file__).resolve().parents[2]
        for project_id in ('ads8588s', 'ad7606c'):
            with self.subTest(project=project_id):
                project = load_project(repo / f'tools/projects/{project_id}.json')
                frozen, evidence = freeze_design(project, self.root / project_id)
                profile = project.parameters['fabrication_profile']
                self.assertIn(profile, evidence['files'])
                self.assertEqual((frozen.root / profile).read_bytes(),
                                 (project.root / profile).read_bytes())
                self.assertEqual(check_project(frozen), [])
                check_frozen_design(evidence)
                (frozen.root / profile).chmod(0o666)
                (frozen.root / profile).unlink()
                with self.assertRaises(ValueError):
                    check_frozen_design(evidence)

    def test_actual_ads_frozen_fast_candidate_inputs_are_complete_and_required(self):
        from pcbtools.manufacturing import freeze_design, check_frozen_design
        from pcbtools.rules.adc import fast_api

        repo = Path(__file__).resolve().parents[2]
        project = load_project(repo / 'tools/projects/ads8588s.json')
        self.assertNotIn('baseline_config', project.parameters)
        frozen, evidence = freeze_design(project, self.root / 'actual-ads-snapshot')
        self.assertNotEqual(frozen.root, project.root)
        # Exercise the actual rule's default frozen root, without injecting live
        # repository paths or mocking either input reader.
        self.assertEqual(fast_api(frozen).check(), [])
        inputs = [
            'hardware/ad7606c_servo/ad7606c_fast_candidate_profile_2026-10-12.json',
            'hardware/ad7606c_servo/adc_fast_candidates_2026-10-12.csv',
        ]
        for name in inputs:
            with self.subTest(missing=name):
                self.assertIn(name, evidence['files'])
                path = frozen.root / name
                data = path.read_bytes()
                path.chmod(0o666)
                path.unlink()
                try:
                    with self.assertRaises(FileNotFoundError):
                        fast_api(frozen).check()
                    with self.assertRaises(ValueError):
                        check_frozen_design(evidence)
                finally:
                    path.write_bytes(data)
                    path.chmod(0o444)
                self.assertEqual(fast_api(frozen).check(), [])
                check_frozen_design(evidence)

    def native_fabrication_fixture(self):
        out = self.root / 'native-export'
        (out / 'gerbers').mkdir(parents=True)
        (out / 'drill').mkdir()
        for name in ['assembly.csv', 'assembly-native.csv', 'assembly-bom.csv',
                     'assembly-consistency.json', 'board.step', 'drawing.pdf',
                     'bom.csv', 'bom-source.xml']:
            (out / name).write_text('fixture native deliverable')
        # Literal filenames observed from KiCad 10 --no-protel-ext output;
        # keep independent of the validator's logical-to-native layer mapping.
        for suffix in ['F_Cu', 'In1_Cu', 'In2_Cu', 'B_Cu', 'F_Mask', 'B_Mask',
                       'F_Paste', 'B_Paste', 'F_Silkscreen', 'B_Silkscreen', 'Edge_Cuts']:
            (out / 'gerbers' / ('fixture-' + suffix + '.gbr')).write_text('G04 Native filename fixture*\nM02*')
        (out / 'drill' / 'fixture-PTH.drl').write_text('M48\n%\nM30')
        return out

    def test_native_silkscreen_filenames_are_required(self):
        from pcbtools.manufacturing import validate_fabrication_outputs
        out = self.native_fabrication_fixture()
        hashes = validate_fabrication_outputs(out)
        self.assertIn('gerbers/fixture-F_Silkscreen.gbr', hashes)
        self.assertIn('gerbers/fixture-B_Silkscreen.gbr', hashes)
        (out / 'gerbers' / 'fixture-F_Silkscreen.gbr').rename(out / 'gerbers' / 'fixture-F_SilkS.gbr')
        with self.assertRaises(ValueError):
            validate_fabrication_outputs(out)

    def test_duplicate_or_legacy_ambiguous_gerbers_are_rejected(self):
        from pcbtools.manufacturing import validate_fabrication_outputs
        out = self.native_fabrication_fixture()
        validate_fabrication_outputs(out)
        for name in ['other-F_Silkscreen.gbr', 'fixture-F_SilkS.gbr', 'other-F_Cu.gbr']:
            extra = out / 'gerbers' / name
            extra.write_text('extra unproven manufacturing layer')
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_fabrication_outputs(out)
            extra.unlink()

    def test_review_registry_is_excluded_but_all_other_spec_fields_are_bound(self):
        from pcbtools.manufacturing import fabrication_spec_sha256
        self.ready_profile()
        profile = json.loads((self.root / 'fab.json').read_text())
        digest = fabrication_spec_sha256(profile)
        profile['reviews'] = {'changed': 'registry'}
        self.assertEqual(fabrication_spec_sha256(profile), digest)
        profile['manufacturing_requirements'] = {'hole_tolerance_mm': 0.1}
        self.assertNotEqual(fabrication_spec_sha256(profile), digest)

    def test_missing_review_spec_digest_is_rejected(self):
        self.ready_profile()
        review = json.loads((self.root / 'component.json').read_text())
        del review['fabrication_spec_sha256']
        self.write('component.json', review)
        profile = json.loads((self.root / 'fab.json').read_text())
        profile['reviews']['component']['sha256'] = hashlib.sha256((self.root / 'component.json').read_bytes()).hexdigest()
        self.write('fab.json', profile)
        self.assertTrue(any(f.rule_id == 'prototype.review.component' and f.status == 'FAIL' for f in self.review_findings()))

    def test_frozen_child_sheet_and_input_tampering(self):
        from pcbtools.manufacturing import freeze_design, check_frozen_design
        child = self.root / 'child.kicad_sch'
        child.write_text('(kicad_sch (uuid "child") (lib_symbols))')
        schematic = self.project.schematic
        schematic.write_text('(kicad_sch (uuid "root") (lib_symbols) (sheet (uuid "instance") (property "Sheetfile" ' + json.dumps(child.as_posix()) + ')))')
        frozen, evidence = freeze_design(self.project, self.root / 'artifacts' / 'snapshot')
        self.assertNotIn(child.as_posix(), frozen.schematic.read_text())
        check_frozen_design(evidence)
        frozen.board.chmod(0o666)
        frozen.board.write_text('tampered')
        with self.assertRaises(ValueError):
            check_frozen_design(evidence)

    def test_snapshot_rejects_change_between_review_and_copy(self):
        from pcbtools.manufacturing import freeze_design, design_source_hashes
        reviewed = design_source_hashes(self.project)
        self.project.board.write_text(self.project.board.read_text() + '\n; changed before copy')
        with self.assertRaisesRegex(ValueError, 'reviewed inputs'):
            freeze_design(self.project, self.root / 'artifacts' / 'snapshot', reviewed)

    def test_dielectric_type_and_permittivity_mismatch_are_rejected(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        stack = json.loads((self.root / 'fab.json').read_text())['stackup']
        board = self.project.board
        original = board.read_text()
        for replacement in ('(type "core")', '', '(type "prepreg") (type "prepreg")'):
            board.write_text(original.replace('(type "prepreg")', replacement, 1))
            with self.assertRaises(ValueError):
                check_stackup(self.project, stack)
        board.write_text(original.replace('(epsilon_r 4.1)', '(epsilon_r 4.2)', 1))
        with self.assertRaises(ValueError):
            check_stackup(self.project, stack)

    def test_changed_manufacturing_spec_cannot_reuse_old_reviews(self):
        self.ready_profile()
        profile = json.loads((self.root / 'fab.json').read_text())
        profile['manufacturer'] = 'A different unreviewed manufacturer'
        profile['manufacturing_requirements'] = {'via_covering': 'unreviewed open vias'}
        self.write('fab.json', profile)
        self.assertTrue(any(f.status == 'FAIL' for f in self.review_findings()))

    def test_prototype_native_and_geometry_checks_read_snapshot(self):
        from pcbtools.verification import verify
        self.ready_profile()
        native_sources, audited_roots = [], []
        def native(command, cwd, timeout):
            if command[0] == 'git':
                return {'exit_code': 0, 'status': 'PASS', 'stdout': 'fixture', 'stderr': ''}
            if command[-1] == '--version':
                return {'exit_code': 0, 'status': 'PASS', 'stdout': '10.0.0', 'stderr': ''}
            native_sources.append(Path(command[-1]))
            target = Path(command[command.index('--output') + 1])
            if 'kicadxml' in command:
                target.write_text('<export><design><source>fixture</source></design><components><comp ref="R1"/></components><nets><net name="GND"><node ref="R1" pin="1"/></net></nets></export>')
            elif 'kicadsexpr' in command:
                target.write_text('(export (design (source "fixture")) (components (comp (ref "R1"))) (nets (net (name "GND") (node (ref "R1") (pin "1")))))')
            elif 'erc' in command:
                target.write_text(json.dumps({'sheets': [{'violations': []}]}))
            elif 'drc' in command:
                target.write_text(json.dumps({'violations': [], 'unconnected_items': [], 'schematic_parity': []}))
            else:
                target.write_bytes(b'%PDF fixture')
            return {'exit_code': 0, 'status': 'PASS', 'stdout': '', 'stderr': ''}
        def audit(project, *args):
            audited_roots.append(project.root)
            return []
        with patch('pcbtools.verification.run_native', side_effect=native), patch('pcbtools.schematic.check_schematic', side_effect=audit), patch('pcbtools.board.check_board', side_effect=audit), patch('pcbtools.rules.run_rules', side_effect=audit):
            report = verify(self.project, 'prototype')
        self.assertEqual(report.evidence['prototype_ready'], 'PASS')
        root = Path(report.evidence['frozen_design']['root'])
        self.assertTrue(native_sources)
        self.assertTrue(all(path.is_relative_to(root) for path in native_sources))
        self.assertTrue(all(path == root for path in audited_roots))

    def test_actual_referenced_model_is_hashed_outside_library_directory(self):
        from pcbtools.manufacturing import design_source_hashes
        (self.root / 'models').mkdir()
        model = self.root / 'models' / 'part.step'
        model.write_text('mechanical revision A')
        board = self.root / 'top.kicad_pcb'
        board.write_text(board.read_text() + '\n(footprint "fixture:part" (model "${KIPRJMOD}/models/part.step"))')
        before = design_source_hashes(self.project)
        model.write_text('mechanical revision B')
        self.assertNotEqual(before, design_source_hashes(self.project))

    def test_actual_external_or_missing_model_blocks_freeze(self):
        from pcbtools.manufacturing import design_source_hashes
        board = self.root / 'top.kicad_pcb'
        original = board.read_text()
        for name in ('${KICAD10_3DMODEL_DIR}/part.step', '${KIPRJMOD}/missing.step'):
            with self.subTest(name=name):
                board.write_text(original + '\n(footprint "fixture:part" (model "' + name + '"))')
                with self.assertRaises(ValueError):
                    design_source_hashes(self.project)

    def test_unselected_library_model_does_not_block_actual_board(self):
        from pcbtools.manufacturing import design_source_hashes
        library = self.root / 'fixture.pretty'
        library.mkdir()
        (library / 'unused.kicad_mod').write_text('(footprint "unused" (model "${UNKNOWN}/unused.step"))')
        self.assertIn('fixture.pretty/unused.kicad_mod', design_source_hashes(self.project))

    def test_export_uses_one_frozen_board_during_ABA_source_change(self):
        from pcbtools.manufacturing import export_fabrication
        from pcbtools.report import exit_code
        report = self.prototype_report()
        board = self.root / 'top.kicad_pcb'
        original = board.read_bytes()
        observed = []
        def exporter(command, cwd, timeout):
            source = Path(command[-1])
            observed.append((source, source.read_bytes()))
            result = self.fake_export(command, cwd, timeout)
            if command[3] == 'gerbers':
                board.write_bytes(original + b'\n; temporarily changed drill geometry\n')
            if command[3] == 'drill':
                board.write_bytes(original)
            return result
        def bom(project, output, cli):
            self.assertNotEqual(project.schematic, self.project.schematic)
            self.fake_bom(project, output, cli)
        with patch('pcbtools.verification.verify', return_value=report), patch('pcbtools.manufacturing.run_native', side_effect=exporter), patch('pcbtools.export.export_bom', side_effect=bom):
            result = export_fabrication(self.project, self.root / 'artifacts', {})
        self.assertEqual(exit_code(result), 0)
        self.assertTrue(all(source != board for source, _ in observed))
        self.assertEqual(len({data for _, data in observed}), 1)

    def test_frozen_tables_and_model_references_resolve_inside_snapshot(self):
        from pcbtools.manufacturing import freeze_design
        model = self.root / 'models' / 'part.step'
        model.parent.mkdir()
        model.write_text('exact model bytes')
        library = self.root / 'fixture.pretty'
        library.mkdir()
        (library / 'part.kicad_mod').write_text('(footprint "part")')
        self.write('sym-lib-table', {})
        (self.root / 'fp-lib-table').write_text('(fp_lib_table (lib (name "fixture") (uri "' + library.as_posix() + '")))')
        board = self.root / 'top.kicad_pcb'
        board.write_text(board.read_text() + '\n(footprint "fixture:part" (model "' + model.as_posix() + '"))')
        frozen, evidence = freeze_design(self.project, self.root / 'artifacts' / 'snapshot')
        self.assertNotIn(self.root.as_posix() + '/models', frozen.board.read_text())
        self.assertNotIn(library.as_posix(), (frozen.schematic.parent / 'fp-lib-table').read_text())
        snapshot_model = frozen.root / 'models' / 'part.step'
        self.assertEqual(snapshot_model.read_bytes(), model.read_bytes())
        model.write_text('changed original')
        self.assertEqual(snapshot_model.read_text(), 'exact model bytes')

    def test_same_total_different_individual_dielectric_is_rejected(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        profile = json.loads((self.root / 'fab.json').read_text())
        board = self.root / 'top.kicad_pcb'
        board.write_text(board.read_text().replace('(thickness 0.1)', '(thickness 0.25)', 1).replace('(thickness 1.19)', '(thickness 1.04)', 1))
        with self.assertRaises(ValueError):
            check_stackup(self.project, profile['stackup'])

    def test_selected_native_legend_minima_reject_weaker_or_missing_settings(self):
        from pcbtools.manufacturing import check_native_settings
        minima = {'min_silk_clearance': 0.15, 'min_text_height': 1.0,
                  'min_text_thickness': 0.15}
        self.project.parameters['native_manufacturing_minima'] = minima
        self.settings['board']['design_settings']['rules'] = dict(minima)
        self.write('top.kicad_pro', self.settings)
        check_native_settings(self.project)
        for key, minimum in minima.items():
            for value in (None, minimum / 2, float('nan')):
                with self.subTest(key=key, value=value):
                    rules = dict(minima)
                    if value is None:
                        del rules[key]
                    else:
                        rules[key] = value
                    self.settings['board']['design_settings']['rules'] = rules
                    self.write('top.kicad_pro', self.settings)
                    with self.assertRaisesRegex(ValueError, key):
                        check_native_settings(self.project)

    def test_selected_project_rejects_broad_footprint_clearance_override(self):
        from pcbtools.manufacturing import check_native_settings
        self.project.parameters['forbid_footprint_clearance_overrides'] = True
        check_native_settings(self.project)
        self.project.board.write_text('(kicad_pcb (footprint "example" (property "Reference" "U12") (clearance 0.2)))')
        with self.assertRaisesRegex(ValueError, 'clearance override'):
            check_native_settings(self.project)

    def test_selected_project_rejects_pad_clearance_override(self):
        from pcbtools.manufacturing import check_native_settings
        self.project.parameters['forbid_footprint_clearance_overrides'] = True
        self.project.board.write_text('(kicad_pcb (footprint "example" (property "Reference" "U12") (pad "1" smd rect (clearance 0.1))))')
        with self.assertRaisesRegex(ValueError, 'clearance override'):
            check_native_settings(self.project)

    def test_footprint_zone_connection_clearance_is_not_a_local_override(self):
        from pcbtools.manufacturing import check_native_settings
        self.project.parameters['forbid_footprint_clearance_overrides'] = True
        self.project.board.write_text('(kicad_pcb (footprint "example" (property "Reference" "L1") (zone (name "manufacturer core keepout") (connect_pads (clearance 0)))))')
        check_native_settings(self.project)

    def test_quoted_clearance_example_is_not_a_local_override(self):
        from pcbtools.manufacturing import check_native_settings
        self.project.parameters['forbid_footprint_clearance_overrides'] = True
        self.project.board.write_text('(kicad_pcb (footprint "example" (property "Reference" "L1") (property "Value" "example (clearance 0.2)")))')
        check_native_settings(self.project)

    def test_zone_does_not_conceal_actual_footprint_or_pad_override(self):
        from pcbtools.manufacturing import check_native_settings
        self.project.parameters['forbid_footprint_clearance_overrides'] = True
        for override in ['(clearance 0.2)', '(pad "1" smd rect (clearance 0.1))']:
            with self.subTest(override=override):
                self.project.board.write_text('(kicad_pcb (footprint "example" (property "Reference" "L1") (zone (connect_pads (clearance 0))) ' + override + '))')
                with self.assertRaisesRegex(ValueError, 'clearance override'):
                    check_native_settings(self.project)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "top.kicad_sch").write_text('(kicad_sch (version 20250114) (uuid "root") (paper "A4") (lib_symbols))')
        (self.root / "top.kicad_pcb").write_text('(kicad_pcb (general (thickness 1.6)) (layers (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (2 "B.Cu" signal)) (setup (stackup (layer "F.Cu" (type "copper") (thickness 0.07)) (layer "dielectric 1" (type "prepreg") (thickness 0.1) (material "FR4 Tg170") (epsilon_r 4.1)) (layer "In1.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 2" (type "core") (thickness 1.19) (material "FR4 Tg170") (epsilon_r 4.1)) (layer "In2.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 3" (type "prepreg") (thickness 0.1) (material "FR4 Tg170") (epsilon_r 4.1)) (layer "B.Cu" (type "copper") (thickness 0.07)))))')
        board = self.root / "top.kicad_pcb"
        board.write_text(board.read_text().replace('(general ', '(footprint "Fixture:R_0603" (layer "F.Cu") (at 10 20 90) (property "Reference" "R1") (property "Value" "10k") (attr smd)) (general ', 1))
        self.settings = {"board": {"design_settings": {"rule_severities": {"clearance": "error"}, "drc_exclusions": []}}, "erc": {"rule_severities": {"pin_not_connected": "warning"}, "erc_exclusions": []}}
        self.write("top.kicad_pro", self.settings)
        self.write("config.json", {"schema_version": 1, "id": "fixture", "root": ".", "schematic": "top.kicad_sch", "board": "top.kicad_pcb", "output": "artifacts", "parameters": {"fabrication_profile": "fab.json"}})
        self.write("fab.json", {"schema_version": 1, "project_id": "fixture"})
        self.project = load_project(self.root / "config.json")

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data), encoding="utf-8")

    def ready_profile(self):
        from pcbtools.manufacturing import design_source_hashes, REQUIRED_REVIEWS, fabrication_spec_sha256
        hashes = design_source_hashes(self.project)
        (self.root / "engineering.txt").write_text("Fixture engineering calculations, dimensions and source references.")
        evidence = {"path": "engineering.txt", "sha256": hashlib.sha256((self.root / "engineering.txt").read_bytes()).hexdigest()}
        profile = {"schema_version": 1, "project_id": "fixture", "manufacturer": "Fixture manufacturer", "stackup": {"profile_id": "actual-orderable-stackup", "copper_layers": 4, "thickness_mm": 1.6, "copper_oz": [2, 1, 1, 2], "copper_thickness_mm": [0.070, 0.035, 0.035, 0.070], "dielectric_material": "FR4 Tg170", "dielectric_layers": [{"name": "dielectric " + str(i), "type": "core" if i == 2 else "prepreg", "thickness_mm": 1.19 if i == 2 else 0.1, "epsilon_r": 4.1} for i in (1, 2, 3)], "evidence": evidence}}
        spec_digest = fabrication_spec_sha256(profile)
        reviews = {}
        for subject in REQUIRED_REVIEWS:
            self.write(subject + ".json", {"schema_version": 1, "project_id": "fixture", "subject": subject, "status": "PASS", "reviewer": "Test fixture", "reviewed_utc": "2026-10-18T00:00:00Z", "source_hashes": hashes, "fabrication_spec_sha256": spec_digest, "evidence": [evidence]})
            reviews[subject] = {"path": subject + ".json", "sha256": hashlib.sha256((self.root / (subject + ".json")).read_bytes()).hexdigest()}
        profile["reviews"] = reviews
        self.write("fab.json", profile)

    def test_manufacturer_finished_copper_is_distinct_from_nominal_oz(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        board = self.root / "top.kicad_pcb"
        board.write_text(board.read_text().replace("(thickness 0.035)", "(thickness 0.030)"))
        profile = json.loads((self.root / "fab.json").read_text())
        profile["stackup"]["profile_id"] = "JLC041621-3313"
        profile["stackup"]["copper_thickness_mm"] = [0.070, 0.030, 0.030, 0.070]
        check_stackup(self.project, profile["stackup"])

    def test_missing_actual_copper_thickness_is_not_inferred(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        profile = json.loads((self.root / "fab.json").read_text())
        del profile["stackup"]["copper_thickness_mm"]
        with self.assertRaises(ValueError):
            check_stackup(self.project, profile["stackup"])

    def test_native_copper_must_match_actual_manufacturer_thickness(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        profile = json.loads((self.root / "fab.json").read_text())
        profile["stackup"]["copper_thickness_mm"] = [0.070, 0.030, 0.030, 0.070]
        with self.assertRaises(ValueError):
            check_stackup(self.project, profile["stackup"])

    def test_nonfinite_manufacturer_dimensions_are_rejected(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        profile = json.loads((self.root / "fab.json").read_text())
        for key, value in (("thickness_mm", float("nan")), ("copper_thickness_mm", [0.07, float("nan"), 0.035, 0.07]), ("copper_oz", [2, float("inf"), 1, 2])):
            with self.subTest(key=key):
                stackup = dict(profile["stackup"])
                stackup[key] = value
                with self.assertRaises(ValueError):
                    check_stackup(self.project, stackup)

    def test_native_stackup_artwork_layers_have_no_physical_thickness(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        board = self.root / "top.kicad_pcb"
        # KiCad saves silk/paste entries without thickness and mask entries
        # with coating thickness. They are not laminate/core thicknesses.
        text = board.read_text().replace('(stackup ', '''(stackup
            (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
            (layer "F.Paste" (type "Top Solder Paste"))
            (layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))
            (layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))
            (layer "B.Paste" (type "Bottom Solder Paste"))
            (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
        ''')
        board.write_text(text)
        check_stackup(self.project, json.loads((self.root / "fab.json").read_text())["stackup"])

    def test_four_layer_stack_requires_three_native_dielectrics(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        board = self.root / "top.kicad_pcb"
        board.write_text(board.read_text().replace('"dielectric 3"', '"unrelated layer"'))
        with self.assertRaises(ValueError):
            check_stackup(self.project, json.loads((self.root / "fab.json").read_text())["stackup"])

    def test_duplicate_native_stackup_layer_is_rejected(self):
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        board = self.root / "top.kicad_pcb"
        layer = '(layer "In1.Cu" (type "copper") (thickness 0.035))'
        board.write_text(board.read_text().replace(layer, layer + layer))
        with self.assertRaises(ValueError):
            check_stackup(self.project, json.loads((self.root / "fab.json").read_text())["stackup"])

    def test_kicad_native_roundtrip_stackup_remains_accepted(self):
        try:
            import pcbnew
        except ImportError:
            self.skipTest("Native pcbnew required for stackup save/readback")
        from pcbtools.manufacturing import check_stackup
        self.ready_profile()
        board = self.root / "top.kicad_pcb"
        text = board.read_text().replace('(kicad_pcb ', '(kicad_pcb (version 20260206) (generator "pcbnew") ')
        text = text.replace('(2 "B.Cu" signal)', '(2 "B.Cu" signal) (13 "F.Paste" user) (15 "B.Paste" user) (5 "F.SilkS" user) (7 "B.SilkS" user) (1 "F.Mask" user) (3 "B.Mask" user)')
        text = text.replace('(stackup ', '(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste")) (layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen")) ')
        board.write_text(text)
        native = pcbnew.LoadBoard(str(board))
        pcbnew.SaveBoard(str(board), native)
        saved = board.read_text(encoding="utf-8")
        self.assertIn('"F.SilkS"', saved)
        self.assertIn('"B.Paste"', saved)
        check_stackup(self.project, json.loads((self.root / "fab.json").read_text())["stackup"])

    def review_findings(self):
        from pcbtools.manufacturing import check_prototype_inputs
        return check_prototype_inputs(self.project)[0]

    def test_missing_profile_blocks(self):
        self.assertTrue(any(f.status == "FAIL" for f in self.review_findings()))

    def test_complete_reviews_accept_frozen_actual_inputs(self):
        self.ready_profile()
        self.assertTrue(all(f.status == "PASS" for f in self.review_findings()))

    def test_missing_and_stale_review_rejected(self):
        self.ready_profile()
        (self.root / "component.json").unlink()
        self.assertTrue(any(f.status == "FAIL" for f in self.review_findings()))
        self.ready_profile()
        (self.root / "top.kicad_pcb").write_text((self.root / "top.kicad_pcb").read_text() + "\n")
        self.assertTrue(any(f.status == "FAIL" for f in self.review_findings()))

    def test_review_evidence_tampering_rejected(self):
        self.ready_profile()
        (self.root / "engineering.txt").write_text("changed")
        self.assertTrue(any(f.status == "FAIL" for f in self.review_findings()))

    def test_disabled_checks_and_exclusions_rejected(self):
        self.ready_profile()
        self.settings["board"]["design_settings"]["rule_severities"]["clearance"] = "ignore"
        self.settings["erc"]["erc_exclusions"] = ["hidden"]
        self.write("top.kicad_pro", self.settings)
        findings = self.review_findings()
        self.assertTrue(any(f.rule_id == "prototype.native_settings" and f.status == "FAIL" for f in findings))

    def test_zero_exit_with_missing_fabrication_outputs_rejected(self):
        from pcbtools.manufacturing import validate_fabrication_outputs
        with self.assertRaises(ValueError):
            validate_fabrication_outputs(self.root)

    def prototype_report(self):
        from pcbtools.manufacturing import check_prototype_inputs, design_source_hashes
        from pcbtools.report import RunReport, Finding
        self.ready_profile()
        out = self.root / "artifacts" / "fresh"
        out.mkdir(parents=True)
        findings, evidence = check_prototype_inputs(self.project)
        evidence.update({"output": str(out), "prototype_ready": "PASS", "steps": [], "design_source_hashes": design_source_hashes(self.project)})
        return RunReport("fixture", findings + [Finding("native.drc", "PASS", "fixture")], evidence)

    def fake_bom(self, project, output, cli):
        (output / "bom-source.xml").write_text('<export><components><comp ref="R1"><value>10k</value><footprint>Fixture:R_0603</footprint><fields><field name="MPN">RC0603</field></fields></comp></components></export>')
        (output / "bom.csv").write_text('Ref,Qty,Value / Part,MPN,Package,Status / note\nR1,1,10k,RC0603,Fixture:R_0603,Fitted\n')

    def fake_export(self, command, cwd, timeout):
        from pcbtools.manufacturing import GERBER_LAYERS
        target = Path(command[command.index("--output") + 1])
        if command[3] == "gerbers":
            for layer in GERBER_LAYERS:
                suffix = {'F.SilkS': 'F_Silkscreen', 'B.SilkS': 'B_Silkscreen'}.get(layer, layer.replace('.', '_'))
                (target / ("fixture-" + suffix + ".gbr")).write_text("Native export fixture")
        elif command[3] == "drill":
            (target / "fixture-PTH.drl").write_text("M48 fixture")
            (target / "fixture-NPTH.drl").write_text("M48 fixture")
        elif command[3] == "pos":
            target.write_text('Ref,Val,Package,PosX,PosY,Rot,Side\nR1,10k,R_0603,10,-20,90,top\n')
        else:
            target.write_text("Native export fixture")
        return {"exit_code": 0, "status": "PASS", "stdout": "", "stderr": ""}

    def test_successful_fabrication_keeps_physical_release_blocked(self):
        from pcbtools.manufacturing import export_fabrication
        from pcbtools.report import exit_code
        report = self.prototype_report()
        def bom(project, output, cli):
            self.fake_bom(project, output, cli)
        with patch("pcbtools.verification.verify", return_value=report), patch("pcbtools.manufacturing.run_native", side_effect=self.fake_export), patch("pcbtools.export.export_bom", side_effect=bom):
            result = export_fabrication(self.project, self.root / "artifacts", {})
        self.assertEqual(exit_code(result), 0)
        self.assertEqual(result.evidence["pcb_release"], "BLOCKED")
        self.assertEqual(len(result.evidence["fabrication_outputs_sha256"]), 21)

    def test_fabrication_assembly_identity_guard_is_required(self):
        from pcbtools.manufacturing import export_fabrication
        from pcbtools.report import exit_code
        report = self.prototype_report()
        def wrong_pose(command, cwd, timeout):
            result = self.fake_export(command, cwd, timeout)
            if command[3] == 'pos':
                target = Path(command[command.index('--output') + 1])
                target.write_text(target.read_text().replace('10,-20,90', '11,-20,90'))
            return result
        with patch('pcbtools.verification.verify', return_value=report), patch('pcbtools.manufacturing.run_native', side_effect=wrong_pose), patch('pcbtools.export.export_bom', side_effect=self.fake_bom):
            result = export_fabrication(self.project, self.root / 'artifacts', {})
        self.assertEqual(exit_code(result), 1)
        self.assertEqual(result.evidence['fabrication_export'], 'BLOCKED')

    def test_fabrication_refuses_stale_source_after_verification(self):
        from pcbtools.manufacturing import export_fabrication
        report = self.prototype_report()
        (self.root / "top.kicad_pcb").write_text("changed board")
        with patch("pcbtools.verification.verify", return_value=report):
            result = export_fabrication(self.project, self.root / "artifacts", {})
        self.assertEqual(result.evidence["fabrication_export"], "BLOCKED")
        self.assertEqual(result.evidence["prototype_ready"], "BLOCKED")
        self.assertFalse((Path(result.evidence["output"]) / "gerbers").exists())

    def test_spoofed_summary_count_cannot_override_native_arrays(self):
        target = self.root / "erc.json"
        self.write("erc.json", {"sheets": [{"violations": []}], "errors": 1})
        self.assertEqual(native_summary("erc", target, 0).status, "FAIL")

    def test_copper_weight_and_native_stackup_are_required(self):
        self.ready_profile()
        board = self.root / "top.kicad_pcb"
        board.write_text(board.read_text().replace("(thickness 0.07)", "(thickness 0.035)"))
        findings = self.review_findings()
        self.assertTrue(any(f.rule_id == "prototype.profile" and f.status == "FAIL" for f in findings))

    def test_native_zero_exit_missing_files_blocks_export(self):
        from pcbtools.manufacturing import export_fabrication
        from pcbtools.report import exit_code
        report = self.prototype_report()
        with patch("pcbtools.verification.verify", return_value=report), patch("pcbtools.manufacturing.run_native", return_value={"exit_code": 0, "status": "PASS"}), patch("pcbtools.export.export_bom", return_value=1):
            result = export_fabrication(self.project, self.root / "artifacts", {})
        self.assertEqual(exit_code(result), 1)
        self.assertEqual(result.evidence["fabrication_export"], "BLOCKED")

    def test_prototype_and_fabrication_cli_are_explicit(self):
        from pcbtools.cli import parser
        self.assertEqual(parser().parse_args(["verify", "--project", "ads8588s", "--scope", "prototype"]).scope, "prototype")
        self.assertEqual(parser().parse_args(["export", "--project", "ads8588s", "--kind", "fabrication"]).kind, "fabrication")

    def test_native_unknown_exclusion_count_cannot_be_spoofed(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "drc.json"
            target.write_text(json.dumps({"violations": [], "unconnected_items": [], "schematic_parity": [], "exclusions": 1}))
            self.assertEqual(native_summary("drc", target, 0).status, "FAIL")

    def test_manufacturing_domain_available(self):
        self.assertIsNotNone(importlib.util.find_spec("pcbtools.manufacturing"))


if __name__ == "__main__":
    unittest.main()
