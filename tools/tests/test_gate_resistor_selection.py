"""Same resistance does not approve an unreviewed gate-pulse substitute."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pcbtools.rules.protection import gate_resistor_errors

class GateResistorSelectionTests(unittest.TestCase):
    def test_old_general_resistor_is_rejected_despite_same_value_and_package_size(self):
        selection={'mpn':'CRCW060333R0FKEAHP','footprint':'fpga-servo:Vishay_CRCW0603_HP'}
        parts={f'RG{i}':{'MPN':selection['mpn'],'Value':'33R','Footprint':selection['footprint']} for i in range(1,7)}
        self.assertEqual(gate_resistor_errors(parts,selection),[])
        parts['RG3']['MPN']='RS-03K33R0FT'
        self.assertTrue(gate_resistor_errors(parts,selection))

    def test_wrong_land_or_value_and_missing_gate_resistor_fail(self):
        selection={'mpn':'CRCW060333R0FKEAHP','footprint':'fpga-servo:Vishay_CRCW0603_HP'}
        parts={f'RG{i}':{'MPN':selection['mpn'],'Value':'33R','Footprint':selection['footprint']} for i in range(1,7)}
        for field,value in [('Value','3.3R'),('Footprint','Resistor_SMD:R_0603_1608Metric')]:
            altered={r:dict(p) for r,p in parts.items()};altered['RG1'][field]=value
            self.assertTrue(gate_resistor_errors(altered,selection))
        parts.pop('RG6');self.assertTrue(gate_resistor_errors(parts,selection))
