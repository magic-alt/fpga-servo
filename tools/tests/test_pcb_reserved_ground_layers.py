"""Whole-board reserved return planes reject every foreign routing family."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.rules import power_layout
try:
    import pcbnew as p
except ImportError:
    p = None


class GroundPolicyConfigurationTests(unittest.TestCase):
    def test_both_projects_explicitly_reserve_in1(self):
        from pcbtools.project import resolve_project
        for name in ['ads8588s', 'ad7606c']:
            self.assertEqual(resolve_project(name).parameters.get('reserved_ground_layers'),
                             [{'layer': 'In1.Cu', 'net': '/GND'}])


@unittest.skipIf(p is None, 'pcbnew required for reserved return layer geometry')
class NativeReservedGroundTests(unittest.TestCase):
    def setUp(self):
        factory = getattr(power_layout, 'reserved_ground_api', None)
        self.assertIsNotNone(factory, 'whole-board reserved-ground guard is missing')
        self.api = factory()
        self.board = p.BOARD()
        self.board.SetCopperLayerCount(4)
        self.config = [{'layer': 'In1.Cu', 'net': '/GND'}]
        for name in ['/GND', '/VA_5V', '/NON_ADC_SIGNAL']:
            self.board.Add(p.NETINFO_ITEM(self.board, name))

    def point(self, x, y):
        return p.VECTOR2I(p.FromMM(x), p.FromMM(y))

    def track(self, net='/VA_5V', arc=False, layer=None):
        item = p.PCB_ARC(self.board) if arc else p.PCB_TRACK(self.board)
        item.SetStart(self.point(10, 10))
        item.SetEnd(self.point(14, 10))
        if arc:
            item.SetMid(self.point(12, 12))
        item.SetWidth(p.FromMM(0.3))
        item.SetLayer(p.In1_Cu if layer is None else layer)
        self.board.Add(item)
        if net:
            item.SetNet(self.board.FindNet(net))
        return item

    def zone(self, net='/VA_5V', rule_area=False):
        item = p.ZONE(self.board)
        item.SetLayer(p.In1_Cu)
        item.SetIsRuleArea(rule_area)
        outline = item.Outline()
        outline.NewOutline()
        for x, y in [(10, 10), (15, 10), (15, 15), (10, 15)]:
            outline.Append(self.point(x, y))
        self.board.Add(item)
        if net:
            item.SetNet(self.board.FindNet(net))
        return item

    def test_power_track_is_rejected(self):
        item = self.track()
        report, errors = self.api.audit(self.board, self.config)
        self.assertEqual(len(errors), 1)
        self.assertEqual(report['violations'][0]['uuid'], item.m_Uuid.AsString())

    def test_non_adc_signal_is_rejected(self):
        self.track('/NON_ADC_SIGNAL')
        self.assertEqual(len(self.api.audit(self.board, self.config)[1]), 1)

    def test_arc_is_rejected(self):
        self.track(arc=True)
        self.assertEqual(len(self.api.audit(self.board, self.config)[1]), 1)

    def test_foreign_copper_zone_is_rejected_even_unfilled(self):
        self.zone()
        self.assertEqual(len(self.api.audit(self.board, self.config)[1]), 1)

    def test_empty_net_track_and_zone_are_rejected(self):
        self.track(None)
        self.zone(None)
        self.assertEqual(len(self.api.audit(self.board, self.config)[1]), 2)

    def test_gnd_track_arc_and_zone_are_allowed(self):
        self.track('/GND')
        self.track('/GND', arc=True)
        self.zone('/GND')
        self.assertEqual(self.api.audit(self.board, self.config)[1], [])

    def test_foreign_through_via_is_an_antipad_not_a_plane_track(self):
        item = p.PCB_VIA(self.board)
        item.SetPosition(self.point(12, 12))
        item.SetWidth(p.FromMM(0.6))
        item.SetDrill(p.FromMM(0.3))
        item.SetLayerPair(p.F_Cu, p.B_Cu)
        self.board.Add(item)
        item.SetNet(self.board.FindNet('/VA_5V'))
        self.assertEqual(self.api.audit(self.board, self.config)[1], [])

    def test_rule_area_is_not_copper(self):
        self.zone(None, rule_area=True)
        self.assertEqual(self.api.audit(self.board, self.config)[1], [])

    def reloaded_footprint_zone(self, *, rule_area=False, net='/VA_5V'):
        footprint = p.FOOTPRINT(self.board)
        footprint.SetReference('U99')
        self.board.Add(footprint)
        zone = p.ZONE(footprint)
        zone.SetLayer(p.In1_Cu)
        zone.SetIsRuleArea(rule_area)
        outline = zone.Outline()
        outline.NewOutline()
        for x,y in [(10,10),(15,10),(15,15),(10,15)]:
            outline.Append(self.point(x,y))
        footprint.Add(zone)
        if net:
            zone.SetNet(self.board.FindNet(net))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'footprint-zone.kicad_pcb'
            p.SaveBoard(str(path),self.board)
            loaded = p.LoadBoard(str(path))
        actual = next(f for f in loaded.GetFootprints() if f.GetReference()=='U99')
        self.assertEqual(len(list(loaded.Zones())),0)
        self.assertEqual(len(list(actual.Zones())),1)
        return loaded

    def test_saved_reloaded_foreign_footprint_copper_zone_is_rejected(self):
        board = self.reloaded_footprint_zone()
        report,errors = self.api.audit(board,self.config)
        self.assertEqual(len(errors),1)
        self.assertEqual(report['checked_copper_zones'],1)
        self.assertEqual(report['violations'][0]['net'],'/VA_5V')

    def test_saved_reloaded_footprint_rule_area_is_not_copper(self):
        board = self.reloaded_footprint_zone(rule_area=True,net=None)
        report,errors = self.api.audit(board,self.config)
        self.assertEqual(errors,[])
        self.assertEqual(report['rule_areas_not_copper'],1)
        self.assertEqual(report['checked_copper_zones'],0)

    def test_footprint_gnd_copper_and_duplicate_zone_UUID_count_once(self):
        board = self.reloaded_footprint_zone(net='/GND')
        actual = next(f for f in board.GetFootprints() if f.GetReference()=='U99')
        proxy = SimpleNamespace(GetEnabledLayers=board.GetEnabledLayers,
            GetLayerName=board.GetLayerName,GetTracks=board.GetTracks,
            GetFootprints=board.GetFootprints,Zones=lambda:list(actual.Zones()))
        report,errors = self.api.audit(proxy,self.config)
        self.assertEqual(errors,[])
        self.assertEqual(report['checked_copper_zones'],1)

    def test_missing_or_ambiguous_config_fails_closed(self):
        for config in [None, [], {}, [{'layer':'In1.Cu'}], self.config*2,
                       [{'layer':'In1.Cu','net':''}], [{'layer':'In1.Cu','net':'*'}]]:
            with self.subTest(config=config):
                self.assertTrue(self.api.audit(self.board, config)[1])

    def test_disabled_or_non_copper_layer_fails_closed(self):
        self.board.SetCopperLayerCount(2)
        for layer in ['In1.Cu', 'F.SilkS', 'missing']:
            self.assertTrue(self.api.audit(self.board, [{'layer':layer,'net':'/GND'}])[1])

    def test_other_layer_is_allowed_and_policy_is_configured_not_hardcoded(self):
        self.track(layer=p.In2_Cu)
        self.assertEqual(self.api.audit(self.board, self.config)[1], [])
        self.assertTrue(self.api.audit(self.board, [{'layer':'In2.Cu','net':'/GND'}])[1])

    def test_native_dispatch_checks_missing_policy(self):
        from pcbtools.rules import run_rules
        with tempfile.TemporaryDirectory() as folder:
            board = Path(folder)/'board.kicad_pcb'
            p.SaveBoard(str(board), self.board)
            board.with_suffix('.kicad_dru').write_text('(version 1)',encoding='utf-8')
            project = SimpleNamespace(board=board,root=Path(folder),rule_sets=['power_layout'],parameters={})
            with patch('pcbtools.rules.power_layout.vendor_api') as vendor, \
                    patch('pcbtools.rules.power_layout.kelvin_api') as kelvin, \
                    patch('pcbtools.rules.power_layout.escape_api') as escape, \
                    patch('pcbtools.board.corners_api') as corners:
                vendor.return_value.check.return_value=[]
                vendor.return_value.check_internal_pad_rules.return_value=[]
                kelvin.return_value.audit.return_value=({},[])
                escape.return_value.audit.return_value=({},[])
                corners.return_value.audit.return_value=[]
                findings=run_rules(project,'pcb',{})
            selected=[f for f in findings if f.rule_id=='pcb.reserved_ground_layers']
            self.assertEqual(len(selected),1)
            self.assertEqual(selected[0].status,'FAIL')
