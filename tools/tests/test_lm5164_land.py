"""U12 thermal-pad apertures must not expose ordinary unfilled via holes."""
from pathlib import Path
import sys
import unittest
import tempfile
import dataclasses
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
from pcbtools.rules.aux_power import check_project, controller_land_errors, controller_internal_rule_errors


class Lm5164LandTests(unittest.TestCase):
    def test_old_generic_u12_is_rejected_by_daily_contract(self):
        project = resolve_project('ads8588s')
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            text = (project.schematic.parent/'aux_power.kicad_sch').read_text(encoding='utf-8')
            text = text.replace('fpga-servo:TI_DDA0008B_LM5164','Package_SO:TI_SO-PowerPAD-8')
            (folder/'aux_power.kicad_sch').write_text(text,encoding='utf-8')
            shutil.copytree(project.schematic.parent/'fpga-servo.pretty',folder/'fpga-servo.pretty')
            fixture = dataclasses.replace(project,schematic=folder/project.schematic.name)
            errors = check_project(fixture)
            self.assertTrue(any('U12' in error and 'Footprint' in error for error in errors),errors)

    def test_real_local_land_and_controller_contract(self):
        for name in ['ads8588s','ad7606c']:
            project=resolve_project(name)
            self.assertEqual(check_project(project),[])
            self.assertEqual(controller_land_errors(self.land(project)),[])

    @staticmethod
    def land(project):
        return (project.schematic.parent/'fpga-servo.pretty/TI_DDA0008B_LM5164.kicad_mod').read_text()

    def test_mask_union_cannot_reopen_via_region(self):
        text=self.land(resolve_project('ads8588s'))
        self.assertTrue(controller_land_errors(text.replace('(layers "F.Cu")','(layers "F.Cu" "F.Mask")')))

    def test_mask_graphic_cannot_bypass_separate_pad_aperture(self):
        text=self.land(resolve_project('ads8588s'))
        bypass='(fp_rect (start -1.475 -2.45) (end 1.475 2.45) (stroke (width .1) (type default)) (fill solid) (layer "F.Mask"))'
        self.assertTrue(controller_land_errors(text.replace('(attr smd)','(attr smd)\n'+bypass)))

    def test_aperture_cannot_be_numbered_or_wrong_size(self):
        text=self.land(resolve_project('ads8588s'))
        for bad in [text.replace('(pad ""','(pad "9"'),text.replace('(size 2.71 3.4)','(size 2.95 4.9)')]:
            self.assertTrue(controller_land_errors(bad))

    def test_signal_geometry_and_missing_physical_ep_fail(self):
        text=self.land(resolve_project('ads8588s'))
        self.assertTrue(controller_land_errors(text.replace('(size 1.55 0.6)','(size 1.91 0.61)')))
        self.assertTrue(controller_land_errors(text.replace('(pad "9"','(pad "10"')))

    def test_selected_controller_requires_narrow_same_instance_rule(self):
        rule='(rule "U12 internal lands" (condition "A.Type == \'Pad\' && B.Type == \'Pad\' && A.Reference == \'U12\' && B.Reference == \'U12\'") (constraint clearance (min 0.45mm)))'
        self.assertEqual(controller_internal_rule_errors(rule),[])
        for bad in ['',rule.replace("A.Type == 'Pad'","A.Type == 'Track'"),rule.replace("B.Reference == 'U12'","B.Reference == 'U13'"),rule.replace('.45mm','.2mm'),rule+rule]:
            self.assertTrue(controller_internal_rule_errors(bad))


if __name__ == '__main__':
    unittest.main()
