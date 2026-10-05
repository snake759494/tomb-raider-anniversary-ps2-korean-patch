from pathlib import Path
import struct,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import gs
ROOT=Path(__file__).resolve().parents[1]
def build():
 changes={};audit=[]
 for n in (1160,1714,2626,3208):
  b=(ROOT/f'analysis/war/{n}.raw').read_bytes();pal=np.frombuffer(b[144:1168],np.uint8).reshape(256,4);lk=np.arange(256);lk=(lk&~24)|((lk&8)<<1)|((lk&16)>>1);pal=pal[lk]
  tiles=[];p=1168;spans=[]
  for j in range(2):
   size=(struct.unpack_from('<I',b,p)[0]&0x7fff)*16;assert size==65536
   raw=b[p+16:p+16+size];linear=gs.unswizzle8(raw,256,256);assert gs.swizzle8(linear,256,256)==raw
   tiles.append(np.frombuffer(linear,np.uint8).reshape(256,256));spans.append(p+16);p+=16+size
  assert p==len(b);idx=np.concatenate(tiles,axis=1).copy();original=idx.copy();mask=np.zeros(idx.shape,bool)
  left=['시점 초기화','걷기/수동 잡기' if n in (1160,2626) else '대상 조준','대형 구급약','무기 교체','소형 구급약','무기 교체','이동']
  right=['대상 조준' if n in (1160,2626) else '걷기/수동 잡기','무기 공격' if n in (1160,3208) else '웅크리기/구르기','행동/줍기','웅크리기/구르기' if n in (1160,3208) else '무기 공격','점프','그래플','수동 조준']
  ys=[36,65,93,120,150,178,205]
  labels=[((40,y-2,169,y+16),t,'right') for y,t in zip(ys,left)]
  labels += [((342,y-2,505,y+16),t,'left') for y,t in zip(ys,right)]
  labels += [((229,37,280,53),'일시정지','center'),((229,53,280,69),'메뉴','center'),((169,233,207,249),'소지품','right'),((307,233,370,249),'시점 이동','left')]
  white=np.where(np.min(pal[:,:3],axis=1)>230)[0];assert len(white)>2
  transparent=int(np.argmin(pal[:,3]));font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-bRg.ttf'),48)
  for (l,t,r,bt),s,align in labels:
   canvas=Image.new('L',((r-l)*4,(bt-t)*4));d=ImageDraw.Draw(canvas);bb=d.textbbox((0,0),s,font=font);w=bb[2]-bb[0];h=bb[3]-bb[1];assert w<=canvas.width,(n,s,w,canvas.width)
   x=0 if align=='left' else canvas.width-w if align=='right' else (canvas.width-w)//2
   d.text((x-bb[0],(canvas.height-h)//2-bb[1]),s,font=font,fill=128)
   a=np.array(canvas.resize((r-l,bt-t),Image.Resampling.LANCZOS));mapped=white[np.argmin(abs(a[:,:,None].astype(int)-pal[white,3].astype(int)),axis=2)];mapped[a==0]=transparent;idx[t:bt,l:r]=mapped;mask[t:bt,l:r]=True
  assert np.array_equal(idx[~mask],original[~mask]);out=bytearray(b)
  for j,pos in enumerate(spans):out[pos:pos+65536]=gs.swizzle8(idx[:,j*256:(j+1)*256].tobytes(),256,256)
  changes[n]=bytes(out);ar=pal[idx];preview=(ar[:,:,:3]*(ar[:,:,3:4]/128)).clip(0,255).astype('uint8');Image.fromarray(preview).save(ROOT/f'build/controls_{n}_ko.png')
  audit.append(dict(entry=n,labels=[x[1] for x in labels],outside_labels_unchanged=True,container_and_palette_unchanged=True))
 (ROOT/'build/controls_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
 return changes
if __name__=='__main__':build()
