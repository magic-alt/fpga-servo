import pcbnew as p, collections, json, sys
b=p.LoadBoard(sys.argv[1]); zones=[z for z in b.Zones() if not z.GetIsRuleArea()]; nets={z.GetNetCode() for z in zones}
items=[t for t in b.GetTracks() if t.GetNetCode() in nets]+[pd for f in b.GetFootprints() for pd in f.Pads() if pd.GetNetCode() in nets]
parent=list(range(len(items))); shapes={}; cells=collections.defaultdict(list)
def root(i):
 while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
 return i
def union(i,j): parent[root(i)]=root(j)
step=p.FromMM(5)
for i,a in enumerate(items):
 for l in (p.F_Cu,p.B_Cu):
  if not a.IsOnLayer(l): continue
  shape=a.GetEffectiveShape(l); shapes[i,l]=shape; box=shape.BBox(); keys=[(a.GetNetCode(),l,x,y) for x in range(box.GetLeft()//step,box.GetRight()//step+1) for y in range(box.GetTop()//step,box.GetBottom()//step+1)]
  candidates={j for k in keys for j in cells[k]}
  for j in candidates:
   if shape.Collide(shapes[j,l]): union(i,j)
  for k in keys: cells[k].append(i)
polygons=[]
for z in zones:
 l=z.GetLayer(); polys=z.GetFilledPolysList(l)
 for index in range(polys.OutlineCount()):
  shape=polys.UnitSet(index); hits=[i for i,a in enumerate(items) if a.GetNetCode()==z.GetNetCode() and (i,l) in shapes and shape.Collide(shapes[i,l])]
  parent.append(len(parent)); node=len(parent)-1
  for i in hits: union(node,i)
  box=shape.BBox()
  polygons.append({'net':z.GetNetname(),'layer':b.GetLayerName(l),'index':index,'area_mm2':shape.Area()/1e12,'bbox_mm':[p.ToMM(box.GetLeft()),p.ToMM(box.GetTop()),p.ToMM(box.GetRight()),p.ToMM(box.GetBottom())],'native_island':z.IsIsland(l,index),'contacts':len(hits),'node':node,'removal_always':z.GetIslandRemovalMode()==p.ISLAND_REMOVAL_MODE_ALWAYS})
seeds={root(i) for i,a in enumerate(items) if isinstance(a,p.PAD)}
for row in polygons: row['pad_connected']=root(row.pop('node')) in seeds
report={'polygons':polygons,'count':len(polygons),'disconnected':sum(not r['pad_connected'] for r in polygons),'native_islands':sum(r['native_island'] for r in polygons)}
json.dump(report,open(sys.argv[2],'w'),indent=2)
print('COPPER',report['count'],'pad connected',report['count']-report['disconnected'],'isolated',report['disconnected'],'native islands',report['native_islands'])
for z in zones:
 rows=[r for r in polygons if r['net']==z.GetNetname() and r['layer']==b.GetLayerName(z.GetLayer())]
 print(z.GetNetname(),b.GetLayerName(z.GetLayer()),'polygons',len(rows),'area',round(sum(r['area_mm2'] for r in rows),3),'mm2')
