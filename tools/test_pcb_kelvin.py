import sys,unittest
sys.path.insert(0,'tools')
import pcbnew as p
from check_pcb_kelvin import audit

def v(x,y):return p.VECTOR2I(round(x*1e6),round(y*1e6))
def fixture():
 b=p.BOARD()
 for i,phase in enumerate(['U','V','W','BUS'],1):
  y=i*15
  sh=p.FOOTPRINT(b);sh.SetReference(f'RSH{i}');b.Add(sh)
  amp=p.FOOTPRINT(b);amp.SetReference(f'U{i+1}');b.Add(amp)
  load=p.FOOTPRINT(b);load.SetReference(f'LOAD{i}');b.Add(load)
  for num,inp,x,net in [('1','8',-3.1,'/SW_'+phase),('2','1',3.1,'/PH_'+phase)]:
   net = ('/VBUS_PROT' if num=='1' else '/VBUS_BRIDGE') if phase=='BUS' else net
   ni=p.NETINFO_ITEM(b,net);b.Add(ni)
   for parent,n,xx,yy,sx,sy in [(sh,num,x,y,2.1,4),(amp,inp,x,y+7,.8,.8),(load,num,x,y-7,1,1)]:
    pad=p.PAD(parent);pad.SetNumber(n);pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetShape(p.PAD_SHAPE_RECT);pad.SetLayerSet(p.PAD.SMDMask());pad.SetPosition(v(xx,yy));pad.SetSize(v(sx,sy));pad.SetNet(ni);parent.Add(pad)
   pickup=x+(.7 if num=='1' else -.7)
   for a,z,w in [((x,y-7),(x,y),1),((pickup,y+1.5),(pickup,y+5),.25),((pickup,y+5),(x,y+7),.25)]:
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(p.FromMM(w));t.SetLayer(p.F_Cu);t.SetNet(ni);b.Add(t)
 return b
class KelvinTwoTerminal(unittest.TestCase):
 def test_independent_pad_pickups(self):
  rows,errors=audit(fixture());self.assertFalse(errors,errors);self.assertEqual(len(rows),8)
 def test_external_bridge_rejected(self):
  b=fixture();net=b.FindNet('/SW_U');t=p.PCB_TRACK(b);t.SetStart(v(-3.1,12));t.SetEnd(v(-2.4,19));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t)
  rows,errors=audit(b);self.assertTrue(errors);self.assertFalse(rows[0]['passed'])
 def test_missing_pickup_rejected(self):
  b=fixture();t=next(t for t in b.GetTracks() if t.GetStart()==v(-2.4,16.5));b.Remove(t)
  rows,errors=audit(b);self.assertTrue(errors);self.assertFalse(rows[0]['passed'])
 def test_force_side_pickup_rejected(self):
  b=fixture();t=next(t for t in b.GetTracks() if t.GetStart()==v(-2.4,16.5));t.SetStart(v(-3.8,16.5))
  rows,errors=audit(b);self.assertTrue(errors);self.assertFalse(rows[0]['passed'])
if __name__=='__main__':unittest.main()
