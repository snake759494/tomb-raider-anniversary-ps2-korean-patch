"""작은 SCH 파일도 포함하여 전체 아카이브의 영상용 자막을 추출/재구성한다."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LINE=re.compile(rb'(?m)^(lang_[a-z]+ [0-9-]+ [0-9:]+ ")([^\r\n]*)("\r?$)')
CUE=re.compile(rb'\\\(([0-9.]+)\)(.*?)(?=\\\([0-9.]+\)|$)')

def extract():
 es=json.loads((ROOT/'analysis/bigfile_index.json').read_text())
 out=[]
 with (ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso').open('rb') as f:
  for e in es:
   f.seek(662598*2048+e['offset']);h=f.read(min(e['size'],64))
   if not h.startswith(b'Version ') or b'TextEntry' not in h:continue
   f.seek(662598*2048+e['offset']);b=f.read(e['size']);cues=[]
   for m in LINE.finditer(b):
    if m[1].startswith(b'lang_japanese '):
     for c in CUE.finditer(m[2]):cues.append(dict(time=c[1].decode(),source=c[2].decode('cp932')))
   assert cues, e
   out.append(dict(entry=e['index'],raw=b.hex(),cues=cues))
 (ROOT/'analysis/movie_subtitles.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 return out

def rebuild(rows,texts,enc):
 result={}
 for x in rows:
  def line(m):
   if not m[1].startswith(b'lang_japanese '):return m[0]
   def cue(c):return b'\\('+c[1]+b')'+enc(texts[c[2].decode('cp932')])
   return m[1]+CUE.sub(cue,m[2])+m[3]
  result[x['entry']]=LINE.sub(line,bytes.fromhex(x['raw']))
 return result

def fontbuild(rows,texts,cmap):
 """영상 전용 180자 표와 783번 아틀라스를 재배치한다. 영문 채널 문자도 보존한다."""
 import struct,numpy as np
 from PIL import Image,ImageFont,ImageDraw
 import gs
 elf=bytearray((ROOT/'analysis/SLPS_258.56').read_bytes())
 old={}
 for i in range(180):
  code,x,y,w,h=struct.unpack_from('<H4B',elf,0x29ac20+i*6)
  assert h==19
  old[code]=(x,y,w)
 chars=set()
 for row in rows:
  for m in LINE.finditer(bytes.fromhex(row['raw'])):
   for c in CUE.finditer(m[2]):
    s=c[2].decode('cp932')
    chars.update(texts[s] if m[1].startswith(b'lang_japanese ') else s)
 assert len(chars)==180,('영상 문자표 정원',len(chars))
 b=bytearray((ROOT/'analysis/war/783.raw').read_bytes())
 source=np.frombuffer(gs.unswizzle8(b[1184:66720],256,256),np.uint8).reshape(256,256)
 pal=np.frombuffer(b[144:1168],np.uint8).reshape(256,4);lk=np.arange(256);lk=(lk&~24)|((lk&8)<<1)|((lk&16)>>1);pal=pal[lk]
 candidates=np.where(np.min(pal[:,:3],axis=1)>200)[0]
 clear=int(candidates[np.argmin(pal[candidates,3])]);dest=np.full((256,256),clear,dtype=np.uint8)
 font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-bRg.ttf'),64)
 entries=[];x=y=0
 for c in sorted(chars,key=lambda c:cmap[c] if c in cmap else ord(c)):
  if c in cmap:
   code=cmap[c];w=19;im=Image.new('L',(72,72));d=ImageDraw.Draw(im);bb=d.textbbox((0,0),c,font=font)
   d.text(((72-bb[2]+bb[0])//2-bb[0],(72-bb[3]+bb[1])//2-bb[1]),c,font=font,fill=128)
   arr=np.array(im.resize((19,19),Image.Resampling.LANCZOS))
   pixels=candidates[np.argmin(abs(arr[:,:,None].astype(int)-pal[candidates,3].astype(int)),axis=2)]
  else:
   code=ord(c);ox,oy,w=old[code];pixels=source[oy:oy+19,ox:ox+w]
  if x+w>256:x=0;y+=19
  assert y+19<=256
  dest[y:y+19,x:x+w]=pixels
  entries.append(dict(char=c,code=code,x=x,y=y,w=w,h=19));x+=w
 for i,g in enumerate(entries):struct.pack_into('<H4B',elf,0x29ac20+i*6,g['code'],g['x'],g['y'],g['w'],g['h'])
 b[1184:66720]=gs.swizzle8(dest.tobytes(),256,256)
 ar=pal[dest];Image.fromarray((ar[:,:,:3]*(ar[:,:,3:4]/128)).clip(0,255).astype('uint8')).save(ROOT/'build/movie_font.png')
 (ROOT/'build/movie_glyphs.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf8')
 return bytes(elf),bytes(b)

if __name__=='__main__':
 rows=extract();print('영상 자막 파일',len(rows),'자막',sum(len(x['cues']) for x in rows))
