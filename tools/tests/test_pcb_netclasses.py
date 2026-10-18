import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.board import audit_netclasses


class NetclassContractTests(unittest.TestCase):
    def setUp(self):
        self.contract={'required':{'/gate_inverter/GH_U':'GATE'},'minimums':{'GATE':{'clearance':.25,'track_width':.4}}}
        self.project={'net_settings':{'classes':[{'name':'GATE','clearance':.25,'track_width':.4}],
          'netclass_patterns':[{'pattern':'/gate_inverter/GH_U','netclass':'GATE'}]}}
        self.netlist='(export (nets (net (name "/gate_inverter/GH_U"))))'
    def audit(self):
        return audit_netclasses(json.dumps(self.project),self.netlist,self.contract)
    def test_actual_name_and_original_limits_pass(self):
        self.assertEqual(self.audit(),[])
    def test_stale_sheet_name_fails(self):
        self.project['net_settings']['netclass_patterns'][0]['pattern']='/Gate Driver {slash} Inverter/GH_U'
        self.assertTrue(any('assignment' in e for e in self.audit()))
    def test_missing_fresh_net_fails(self):
        self.netlist='(export (nets (net (name "/other"))))'
        self.assertTrue(any('absent' in e for e in self.audit()))
    def test_weakened_clearance_fails(self):
        self.project['net_settings']['classes'][0]['clearance']=.2
        self.assertTrue(any('clearance' in e for e in self.audit()))
    def test_conflicting_exact_assignment_fails(self):
        self.project['net_settings']['netclass_patterns'].append({'pattern':'/gate_inverter/GH_U','netclass':'Default'})
        self.assertTrue(any('assignment' in e for e in self.audit()))


if __name__=='__main__':unittest.main()
