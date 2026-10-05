"""GS local memory swizzle emulation. Textures stored as PSMCT32 uploads that are sampled as PSMT8/PSMT4."""
import numpy as np
BLK32=np.array([[0,1,4,5,16,17,20,21],[2,3,6,7,18,19,22,23],[8,9,12,13,24,25,28,29],[10,11,14,15,26,27,30,31]])
BLK8=BLK32
BLK4=np.array([[0,2,8,10],[1,3,9,11],[4,6,12,14],[5,7,13,15],[16,18,24,26],[17,19,25,27],[20,22,28,30],[21,23,29,31]])
COL32=np.array([[0,1,4,5,8,9,12,13],[2,3,6,7,10,11,14,15]])
def _col8():
    A=[[0,4,16,20,32,36,48,52],[2,6,18,22,34,38,50,54]]; A=[r+[v+8 for v in r] for r in A]
    A=[[0,4,16,20,32,36,48,52,2,6,18,22,34,38,50,54],[8,12,24,28,40,44,56,60,10,14,26,30,42,46,58,62]]
    B=[[33,37,49,53,1,5,17,21,35,39,51,55,3,7,19,23],[41,45,57,61,9,13,25,29,43,47,59,63,11,15,27,31]]
    t=[]
    for c in range(4):
        base=(c>>1)*128
        if c&1==0: rows=A+B
        else: rows=[[v-1+64 for v in r] for r in B]+[[v+65 for v in r] for r in A]
        t+= [[v+base for v in r] for r in rows]
    return np.array(t)
def _col4():
    A=[[0,8,32,40,64,72,96,104,2,10,34,42,66,74,98,106,4,12,36,44,68,76,100,108,6,14,38,46,70,78,102,110],
       [16,24,48,56,80,88,112,120,18,26,50,58,82,90,114,122,20,28,52,60,84,92,116,124,22,30,54,62,86,94,118,126]]
    B=[[65,73,97,105,1,9,33,41,67,75,99,107,3,11,35,43,69,77,101,109,5,13,37,45,71,79,103,111,7,15,39,47],
       [81,89,113,121,17,25,49,57,83,91,115,123,19,27,51,59,85,93,117,125,21,29,53,61,87,95,119,127,23,31,55,63]]
    t=[]
    for c in range(4):
        base=(c>>1)*256
        if c&1==0: rows=A+B
        else: rows=[[v-1+128 for v in r] for r in B]+[[v+129 for v in r] for r in A]
        t+=[[v+base for v in r] for r in rows]
    return np.array(t)
COL8=_col8();COL4=_col4()
def addr32(w,h,bw,bp=0):
    ys,xs=np.mgrid[0:h,0:w]
    page=(ys>>5)*bw+(xs>>6)
    blk=BLK32[(ys>>3)&3,(xs>>3)&7]
    cw=COL32[ys&1,xs&7]+((ys>>1)&3)*16
    return (bp*64+page*2048+blk*64+cw)*4      # byte address
def addr8(w,h,bw,bp=0):
    ys,xs=np.mgrid[0:h,0:w]
    page=(ys>>6)*(bw>>1)+(xs>>7)
    blk=BLK8[(ys>>4)&3,(xs>>4)&7]
    return bp*256+page*8192+blk*256+COL8[ys&15,xs&15]
def addr4(w,h,bw,bp=0):
    """nibble address"""
    ys,xs=np.mgrid[0:h,0:w]
    page=(ys>>7)*(bw>>1)+(xs>>7)
    blk=BLK4[(ys>>4)&7,(xs>>5)&3]
    return (bp*256+page*8192+blk*256)*2+COL4[ys&15,xs&31]
def mem_from32(data,w,h,bw):
    mem=np.zeros(max(int(addr32(w,h,bw).max())+4, 1<<16)+8192*8,np.uint8)
    a=addr32(w,h,bw).ravel()
    words=np.frombuffer(data[:w*h*4],np.uint8).reshape(-1,4)
    for k in range(4): mem[a+k]=words[:,k]
    return mem
def _bw(W): return max(1,(W+63)//64)
def unswizzle8(data,w,h):
    """data: PSMT8 texture uploaded as PSMCT32 (w/2 x h/2). returns w*h index bytes"""
    W,H=w//2,h//2;bw=2*_bw(W)
    mem=mem_from32(data,W,H,_bw(W))
    return mem[addr8(w,h,bw)].tobytes()
def swizzle8(idx,w,h):
    W,H=w//2,h//2;bw=2*_bw(W)
    mem=np.zeros(1<<22,np.uint8);mem[addr8(w,h,bw).ravel()]=np.frombuffer(bytes(idx),np.uint8)
    a=addr32(W,H,_bw(W)).ravel()
    out=np.stack([mem[a+k] for k in range(4)],1)
    return out.tobytes()
def unswizzle4(data,w,h):
    W,H=w//2,h//4;bw=2*_bw(W)
    mem=mem_from32(data,W,H,_bw(W))
    na=addr4(w,h,bw).ravel()
    b=mem[na>>1];v=np.where(na&1,b>>4,b&15)
    return v.astype(np.uint8).tobytes()
def swizzle4(idx,w,h):
    W,H=w//2,h//4;bw=2*_bw(W)
    mem=np.zeros(1<<22,np.uint8)
    na=addr4(w,h,bw).ravel();v=np.frombuffer(bytes(idx),np.uint8)&15
    lo=(na&1)==0
    np.bitwise_or.at(mem,na[lo]>>1,v[lo]);np.bitwise_or.at(mem,na[~lo]>>1,v[~lo]<<4)
    a=addr32(W,H,_bw(W)).ravel()
    return np.stack([mem[a+k] for k in range(4)],1).tobytes()

def unswizzle4_w(data,w,h,W):
    H=len(data)//4//W;mem=mem_from32(data,W,H,_bw(W))
    na=addr4(w,h,max(2,2*_bw(w//2))).ravel()
    if (na>>1).max()>=len(mem): raise ValueError
    b=mem[na>>1];return np.where(na&1,b>>4,b&15).astype(np.uint8).tobytes()
def swizzle4_w(idx,w,h,W,n):
    H=n//4//W;mem=np.zeros(1<<22,np.uint8)
    na=addr4(w,h,max(2,2*_bw(w//2))).ravel();v=np.frombuffer(bytes(idx),np.uint8)&15
    lo=(na&1)==0
    np.bitwise_or.at(mem,na[lo]>>1,v[lo]);np.bitwise_or.at(mem,na[~lo]>>1,v[~lo]<<4)
    a=addr32(W,H,_bw(W)).ravel()
    return np.stack([mem[a+k] for k in range(4)],1).tobytes()
def unswizzle8_w(data,w,h,W):
    H=len(data)//4//W;mem=mem_from32(data,W,H,_bw(W))
    a=addr8(w,h,max(2,2*_bw(w//2))).ravel()
    if a.max()>=len(mem): raise ValueError
    return mem[a].tobytes()
def swizzle8_w(idx,w,h,W,n):
    H=n//4//W;mem=np.zeros(1<<22,np.uint8);mem[addr8(w,h,max(2,2*_bw(w//2))).ravel()]=np.frombuffer(bytes(idx),np.uint8)
    a=addr32(W,H,_bw(W)).ravel();return np.stack([mem[a+k] for k in range(4)],1).tobytes()
