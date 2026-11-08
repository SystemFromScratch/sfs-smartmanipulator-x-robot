"""Hull-overlap check of the collision meshes at a few poses (input for the SRDF)."""
import sys, itertools, numpy as np, xml.etree.ElementTree as ET
from scipy.spatial import Delaunay
sys.argv=[sys.argv[0],'out/test.urdf','out/meshes','/dev/null','']
exec(open('fk_render.py').read().split('groups = []')[0])
from stl import load_stl
links=[l.get('name') for l in r.findall('link') if l.find('collision') is not None and l.get('name')!='electronics_box']
def hulls(qd):
    global q, cache
    q=qd; cache={"world":np.eye(4)}
    H={}
    for l in links:
        el=[x for x in r.findall('link') if x.get('name')==l][0]
        t=load_stl('out/meshes/'+el.find('collision/geometry/mesh').get('filename').split('meshes/')[1])
        W=T(l); p=np.unique(t.reshape(-1,3),axis=0)@W[:3,:3].T+W[:3,3]
        H[l]=(p,Delaunay(p))
    return H
def touching(H,a,b,tol=0.0):
    pa,da=H[a]; pb,db=H[b]
    return (db.find_simplex(pa)>=0).any() or (da.find_simplex(pb)>=0).any()
adj=set()
for j in r.findall('joint'):
    a,b=j.find('parent').get('link'),j.find('child').get('link')
    if a in links and b in links: adj.add(frozenset((a,b)))
poses={'zero':{}, 'ready':dict(j2_shoulder=0.5,j3_elbow=0.8,j5_wrist=0.6), 'closed':dict(gripper=1.45), 'assembly':dict(j2_shoulder=0.7416,j3_elbow=0.4674,j4_forearm_roll=0.1426,j5_wrist=0.9151)}
res={}
for n,qd in poses.items():
    H=hulls(qd)
    res[n]={frozenset(p) for p in itertools.combinations(links,2) if frozenset(p) not in adj and touching(H,*p)}
    print(n, sorted(tuple(sorted(p)) for p in res[n]))
print('adjacent', sorted(tuple(sorted(p)) for p in adj))
