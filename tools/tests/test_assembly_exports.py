"""Assembly exports must describe purchased fitted parts and actual native poses."""
import csv
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools import export


class AssemblyExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.board = self.out / 'top.kicad_pcb'
        self.project = SimpleNamespace(parameters={'copper_only_refs': {
            'TP1': 'TestPoint:TestPoint_Pad_D2.0mm'}}, require_board=lambda: self.board)
        self.parts = {
            'R1': ('10k', 'R:R_0603', 'RC0603', 'F.Cu', 10, 20, 90),
            'C1': ('1uF', 'C:C_0603', 'GRM0603', 'B.Cu', 30, 40, 180),
            'TP1': ('TEST', 'TestPoint:TestPoint_Pad_D2.0mm', 'UNVERIFIED', 'F.Cu', 50, 60, 0),
            'D1': ('TVS', 'D:D_0603', 'UNQUALIFIED', 'F.Cu', 70, 80, 0),
        }
        root = ET.Element('export')
        components = ET.SubElement(root, 'components')
        forms = []
        self.positions = []
        self.bom = []
        for ref, (value, fpid, mpn, layer, x, y, rotation) in self.parts.items():
            comp = ET.SubElement(components, 'comp', ref=ref)
            ET.SubElement(comp, 'value').text = value
            ET.SubElement(comp, 'footprint').text = fpid
            fields = ET.SubElement(comp, 'fields')
            ET.SubElement(fields, 'field', name='MPN').text = mpn
            if ref == 'D1':
                ET.SubElement(comp, 'property', name='dnp')
            forms.append(f'(footprint "{fpid}" (layer "{layer}") (at {x} {y} {rotation}) '
                         f'(property "Reference" "{ref}") (property "Value" "{value}") '
                         f'(attr {"dnp" if ref == "D1" else "smd"}))')
            if ref != 'D1':
                self.positions.append(dict(Ref=ref, Val=value, Package=fpid.split(':')[1],
                    PosX=x, PosY=-y, Rot=rotation, Side='top' if layer=='F.Cu' else 'bottom'))
            self.bom.append({'Ref':ref, 'Qty':1, 'Value / Part':value, 'Manufacturer':'Fixture',
                'MPN':mpn, 'Package':fpid, 'LCSC':'UNVERIFIED', 'Status / note':'Fitted'})
        external = ET.SubElement(components, 'comp', ref='J6')
        ET.SubElement(external, 'property', name='exclude_from_board')
        self.bom.append({'Ref':'J6', 'Qty':1, 'Value / Part':'', 'Manufacturer':'Fixture',
            'MPN':'TBD', 'Package':'', 'LCSC':'UNVERIFIED', 'Status / note':'External'})
        ET.ElementTree(root).write(self.out / 'bom-source.xml')
        self.board.write_text('(kicad_pcb '+''.join(forms)+')')
        self.write_csv('assembly.csv', self.positions)
        self.write_csv('bom.csv', self.bom)

    def write_csv(self, name, rows):
        with (self.out / name).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_copper_geometry_and_dnp_are_not_purchase_or_placement_items(self):
        export.export_assembly(self.project, self.out)
        for name in ['assembly.csv', 'assembly-bom.csv']:
            with (self.out / name).open(newline='', encoding='utf-8') as stream:
                self.assertEqual({r['Ref'] for r in csv.DictReader(stream)}, {'R1','C1'})
        self.assertTrue((self.out / 'assembly-consistency.json').is_file())

    def test_same_ref_wrong_geometry_identity_cannot_be_silently_filtered(self):
        self.project.parameters['copper_only_refs']['TP1'] = 'TestPoint:Wrong'
        with self.assertRaises(ValueError):
            export.export_assembly(self.project, self.out)

    def test_named_copper_geometry_with_purchased_mpn_is_rejected(self):
        tree = ET.parse(self.out / 'bom-source.xml')
        tree.find("components/comp[@ref='TP1']/fields/field[@name='MPN']").text = 'REAL-TEST-LOOP'
        tree.write(self.out / 'bom-source.xml')
        with self.assertRaises(ValueError):
            export.export_assembly(self.project, self.out)

    def test_cpl_pose_value_package_side_and_duplicates_fail_closed(self):
        for key, bad in [('Val','wrong'),('Package','wrong'),('PosX',11),
                         ('PosY',20),('Rot',0),('Side','bottom'),('PosX','nan')]:
            with self.subTest(key=key, bad=bad):
                rows = [dict(row) for row in self.positions]
                rows[0][key] = bad
                self.write_csv('assembly.csv', rows)
                with self.assertRaises(ValueError):
                    export.export_assembly(self.project, self.out)
        self.write_csv('assembly.csv', self.positions + [self.positions[0]])
        with self.assertRaises(ValueError):
            export.export_assembly(self.project, self.out)

    def test_missing_fitted_part_and_dnp_extra_fail_closed(self):
        for rows in [self.positions[1:], self.positions+[dict(self.positions[0], Ref='D1')]]:
            self.write_csv('assembly.csv', rows)
            with self.assertRaises(ValueError):
                export.export_assembly(self.project, self.out)

    def test_unqualified_fitted_mpn_fails_closed(self):
        tree = ET.parse(self.out / 'bom-source.xml')
        tree.find("components/comp[@ref='R1']/fields/field[@name='MPN']").text = 'UNVERIFIED'
        tree.write(self.out / 'bom-source.xml')
        with self.assertRaises(ValueError):
            export.export_assembly(self.project, self.out)

    def test_inventory_extra_reference_is_not_silently_discarded(self):
        self.write_csv('bom.csv', self.bom+[dict(self.bom[0], Ref='R999')])
        with self.assertRaises(ValueError):
            export.export_assembly(self.project, self.out)


if __name__ == '__main__':
    unittest.main()
