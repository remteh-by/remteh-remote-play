from pathlib import Path
from PIL import Image
import json
r=Path(__file__).resolve().parents[1]/'desktop/linux/assets/controller-lab'
p=r/'media/remteh-gamepad/ds4-20261011a/tools/gamepad-test/artwork/dualshock-4-front.png'
im=Image.open(p).convert('RGBA');w,h=im.size;a=im.getchannel('A').tobytes()
inside=lambda x,y: 0<=x<w and 0<=y<h and a[y*w+x]>=200
edges={}
def edge(start,end):edges.setdefault(start,[]).append(end)
for y in range(h):
 for x in range(w):
  if not inside(x,y):continue
  if not inside(x,y-1):edge((x,y),(x+1,y))
  if not inside(x+1,y):edge((x+1,y),(x+1,y+1))
  if not inside(x,y+1):edge((x+1,y+1),(x,y+1))
  if not inside(x-1,y):edge((x,y+1),(x,y))
loops=[]
while edges:
 start=next(iter(edges));point=start;points=[point]
 for _ in range(20000):
  possible=edges.get(point)
  if not possible:break
  nxt=possible.pop()
  if not possible:del edges[point]
  point=nxt
  if point==start:loops.append(points);break
  points.append(point)
loop=max(loops,key=lambda pts:abs(sum(x*y2-x2*y for (x,y),(x2,y2) in zip(pts,pts[1:]+pts[:1]))))
# Remove only collinear intermediate vertices. Keep source contour geometry.
keep=[]
for i,b in enumerate(loop):
 a=loop[i-1];c=loop[(i+1)%len(loop)]
 if (b[0]-a[0])*(c[1]-b[1]) != (b[1]-a[1])*(c[0]-b[0]):keep.append(b)
path='M'+'L'.join(f'{x} {y}' for x,y in keep)+'Z'
(r/'photo-masks.json').write_text(json.dumps({'ds4':{'source':'original photo alpha contour; UI clip only, raster unchanged','threshold':200,'points':keep}},separators=(',',':'))+'\n')
(r/'photo-masks.js').write_text('export const DS4_BODY_PATH='+json.dumps(path)+';\n')
print('mask vertices',len(keep),'source remains unchanged')
