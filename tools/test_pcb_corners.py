"""Run with KiCad's pcbnew-capable Python."""
import unittest
import pcbnew as p
from check_pcb_corners import audit


class CornerTests(unittest.TestCase):
    def board(self, segments):
        board = p.BOARD()
        for a, b in segments:
            track = p.PCB_TRACK(board)
            track.SetStart(p.VECTOR2I(p.FromMM(a[0]), p.FromMM(a[1])))
            track.SetEnd(p.VECTOR2I(p.FromMM(b[0]), p.FromMM(b[1])))
            track.SetLayer(p.F_Cu)
            track.SetWidth(p.FromMM(0.25))
            board.Add(track)
        return board

    def test_exposed_right_angle(self):
        rows = audit(self.board([((0, 0), (2, 0)), ((2, 0), (2, 2))]))
        self.assertEqual([r['category'] for r in rows], ['exposed_bend'])

    def test_bevel_and_straight_tracks_pass(self):
        for segments in [
            [((0, 0), (1.8, 0)), ((1.8, 0), (2, .2)), ((2, .2), (2, 2))],
            [((0, 0), (2, 0)), ((2, 0), (4, 0))],
        ]:
            self.assertEqual(audit(self.board(segments)), [])

    def test_t_junction_is_not_a_bend(self):
        self.assertEqual(audit(self.board([
            ((0, 0), (2, 0)), ((2, 0), (4, 0)), ((2, 0), (2, 2)),
        ])), [])

    def test_quantization_stub_is_reported(self):
        rows = audit(self.board([((0, 0), (2, 0)), ((2, 0), (2, .0001))]))
        self.assertEqual(rows[0]['category'], 'sub_micron_stub')

    def test_via_anchor_is_reported(self):
        board = self.board([((0, 0), (2, 0)), ((2, 0), (2, 2))])
        via = p.PCB_VIA(board)
        via.SetPosition(p.VECTOR2I(p.FromMM(2), 0))
        via.SetWidth(p.FromMM(.6))
        via.SetDrill(p.FromMM(.3))
        board.Add(via)
        self.assertEqual(audit(board)[0]['category'], 'pad_or_via_anchor')


if __name__ == '__main__':
    unittest.main()
