"""Independent review regressions. Run from repository root with KiCad Python."""
import sys
import unittest
sys.path.insert(0, 'tools')
from test_pcb_kelvin import fixture, v, p
from check_pcb_kelvin import audit

class ReviewKelvinRegressions(unittest.TestCase):
    def test_outer_exit_rejected(self):
        board = fixture()
        for track in board.GetTracks():
            if track.GetStart() == v(-2.4, 16.5):
                track.SetEnd(v(-5, 17))
            elif track.GetStart() == v(-2.4, 20):
                track.SetStart(v(-5, 17))
        rows, errors = audit(board)
        self.assertFalse(rows[0]['passed'], errors)

    def test_arc_outer_exit_rejected(self):
        board = fixture()
        old = next(t for t in board.GetTracks() if t.GetStart() == v(-2.4, 16.5))
        board.Remove(old)
        arc = p.PCB_ARC(board)
        arc.SetStart(v(-2.4, 16.5))
        arc.SetMid(v(-5, 17))
        arc.SetEnd(v(-2.4, 20))
        arc.SetWidth(p.FromMM(.25))
        arc.SetLayer(p.F_Cu)
        arc.SetNet(board.FindNet('/SW_U'))
        board.Add(arc)
        rows, errors = audit(board)
        self.assertFalse(rows[0]['passed'], errors)

    def test_inner_layer_bridge_rejected(self):
        board = fixture()
        board.SetCopperLayerCount(4)
        net = board.FindNet('/SW_U')
        for xy in [(-2.4, 19), (-3.1, 12)]:
            via = p.PCB_VIA(board)
            via.SetPosition(v(*xy))
            via.SetWidth(p.FromMM(.6))
            via.SetDrill(p.FromMM(.3))
            via.SetLayerPair(p.F_Cu, p.B_Cu)
            via.SetNet(net)
            board.Add(via)
        track = p.PCB_TRACK(board)
        track.SetStart(v(-2.4, 19))
        track.SetEnd(v(-3.1, 12))
        track.SetWidth(p.FromMM(.25))
        track.SetLayer(p.In1_Cu)
        track.SetNet(net)
        board.Add(track)
        rows, errors = audit(board)
        self.assertFalse(rows[0]['passed'], errors)

    def test_full_contact_must_stay_in_inner_half(self):
        board = fixture()
        for track in board.GetTracks():
            if track.GetStart() == v(-2.4, 16.5):
                track.SetStart(v(-3.05, 16.5))
                track.SetEnd(v(-3.05, 20))
            elif track.GetStart() == v(-2.4, 20):
                track.SetStart(v(-3.05, 20))
        rows, errors = audit(board)
        self.assertFalse(rows[0]['passed'], errors)

if __name__ == '__main__':
    unittest.main()
