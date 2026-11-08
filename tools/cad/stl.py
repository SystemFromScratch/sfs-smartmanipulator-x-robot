import numpy as np, struct, os
def load_stl(p):
    d=open(p,'rb').read()
    n=struct.unpack('<I',d[80:84])[0]
    if 84+50*n==len(d):
        a=np.frombuffer(d[84:],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]),count=n)
        return a['v'].reshape(-1,3,3).astype(np.float64)
    v=[list(map(float,l.split()[1:4])) for l in d.decode(errors='ignore').splitlines() if l.strip().startswith('vertex')]
    return np.array(v).reshape(-1,3,3)
def area(t): return 0.5*np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).sum()
def pdims(t):
    p=t.reshape(-1,3); c=p-p.mean(0); w,v=np.linalg.eigh(c.T@c); q=c@v; return np.sort(q.max(0)-q.min(0))[::-1]
