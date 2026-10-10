"""Regression tests for the narrowly bounded package escape exception."""

import unittest
from pathlib import Path
from check_pcb_escape import check_rules, condition, audit

try:
    import pcbnew as p
except ImportError:
    p = None

ROOT = Path(__file__).resolve().parents[1]
RULES = "(version 1)\n" + "\n".join(
    f'(rule "{ref} bounded pad escape" (condition "{condition(ref)}") '
    f"(constraint clearance (min {gap}mm)))"
    for ref, gap in [("U1", 0.25), ("U18", 0.2)]
)


class EscapeRuleTests(unittest.TestCase):
    def test_exact_scoped_rules(self):
        self.assertEqual(check_rules(RULES), [])

    def test_no_exception_is_optional_for_old_baselines(self):
        self.assertEqual(check_rules("(version 1)", required=False), [])

    def test_missing_exception_partner_is_rejected(self):
        self.assertTrue(check_rules(RULES[: RULES.index('(rule "U18')]))

    def test_foreign_package_scope_is_rejected(self):
        self.assertTrue(
            check_rules(RULES.replace("B.Reference == 'U1'", "B.Reference == 'Q1'"))
        )

    def test_clearance_reduction_is_rejected(self):
        self.assertTrue(check_rules(RULES.replace("0.25mm", "0.01mm")))

    def test_duplicate_exception_is_rejected(self):
        self.assertTrue(check_rules(RULES + RULES[RULES.index("(rule") :]))

    def test_severity_override_is_rejected(self):
        self.assertTrue(
            check_rules(RULES.replace("(condition", "(severity ignore) (condition", 1))
        )


@unittest.skipIf(p is None, "native pcbnew required for physical escape audits")
class NativeEscapeTests(unittest.TestCase):
    def setUp(self):
        self.board = p.LoadBoard(str(ROOT / "hardware/ax7010_servo_reva.kicad_pcb"))

    def via(self):
        return next(
            t
            for g in self.board.Groups()
            if g.GetName() == "U1_pad_escape"
            for t in self.board.GetTracks()
            if isinstance(t, p.PCB_VIA)
            and t.m_Uuid.AsString() in {v.m_Uuid.AsString() for v in g.GetItems()}
        )

    def test_actual_pad_connected_escape(self):
        self.assertEqual(audit(self.board)[1], [])

    def test_u1_back_escape_has_physical_via_path(self):
        group = next(g for g in self.board.Groups() if g.GetName() == "U1_pad_escape")
        ids = {v.m_Uuid.AsString() for v in group.GetItems()}
        self.assertTrue(
            any(
                not isinstance(v, p.PCB_VIA)
                and v.GetLayer() == p.B_Cu
                and v.m_Uuid.AsString() in ids
                for v in self.board.GetTracks()
            )
        )
        self.assertEqual(audit(self.board)[1], [])

    def test_u18_back_track_is_rejected(self):
        fp = next(f for f in self.board.GetFootprints() if f.GetReference() == "U18")
        pd = next(iter(fp.Pads()))
        track = p.PCB_TRACK(self.board)
        track.SetStart(pd.GetPosition())
        track.SetEnd(pd.GetPosition() + p.VECTOR2I(p.FromMM(0.2), 0))
        track.SetLayer(p.B_Cu)
        track.SetWidth(p.FromMM(0.2))
        track.SetNetCode(pd.GetNetCode())
        self.board.Add(track)
        next(g for g in self.board.Groups() if g.GetName() == "U18_pad_escape").AddItem(
            track
        )
        self.assertTrue(audit(self.board)[1])

    def test_foreign_net_via_is_rejected(self):
        self.via().SetNet(self.board.FindNet("/ADC_BUSY"))
        self.assertTrue(audit(self.board)[1])

    def test_via_outside_package_is_rejected(self):
        self.via().SetPosition(p.VECTOR2I(p.FromMM(120), p.FromMM(80)))
        self.assertTrue(audit(self.board)[1])

    def test_detached_local_via_is_rejected(self):
        self.via().SetPosition(p.VECTOR2I(p.FromMM(62), p.FromMM(54.7)))
        self.assertTrue(audit(self.board)[1])

    def test_undersized_drill_is_rejected(self):
        self.via().SetDrill(p.FromMM(0.2))
        self.assertTrue(audit(self.board)[1])

    def test_oversized_local_via_is_rejected(self):
        self.via().SetWidth(p.FromMM(0.8))
        self.assertTrue(audit(self.board)[1])


if __name__ == "__main__":
    unittest.main()
