"""검증된 일본판 원본에서 재빌드에 필요한 자료만 추출한다."""
from pathlib import Path
import struct,json,hashlib,subprocess,sys,re
import pycdlib
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso'
EXPECTED='c045214d7863be1d1e40f445809ce9db9b4ecbc539ef2b6c69783f51bb8c7640'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def save(name,x):(ROOT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def main():
 assert digest(SOURCE)==EXPECTED,'지원하지 않는 원본 ISO입니다.'
 for d in ['analysis/candidates','analysis/war','build']:(ROOT/d).mkdir(parents=True,exist_ok=True)
 iso=pycdlib.PyCdlib();iso.open(str(SOURCE));rows=[]
 for d,ds,fs in iso.walk(iso_path='/'):
  for name in fs:
   p=d.rstrip('/')+'/'+name;r=iso.get_record(iso_path=p);rows.append(dict(path=p,lba=r.extent_location(),size=r.data_length))
 iso.get_file_from_iso(local_path=str(ROOT/'analysis/SLPS_258.56'),iso_path='/SLPS_258.56;1');iso.close();save('analysis/iso_files.json',rows)
 arc=next(x for x in rows if x['path']=='/BIGFILE.DAT;1');base=arc['lba']*2048
 with SOURCE.open('rb') as f:
  f.seek(base);n=struct.unpack('<I',f.read(4))[0];assert n==3376;hs=struct.unpack('<%dI'%n,f.read(n*4));es=[]
  for i,h in enumerate(hs):
   size,off,mask,comp=struct.unpack('<4I',f.read(16));es.append(dict(index=i,hash=f'{h:08x}',size=size,offset=off*2048,mask=f'{mask:08x}',compressed=comp))
  save('analysis/bigfile_index.json',es)
  for i in [1670,3244,2471,1335,595,2817,2077,913,1160,1714,2626,3208,783]:
   e=es[i];assert e['offset']+e['size']<=arc['size'];f.seek(base+e['offset']);b=f.read(e['size']);p='candidates/1670_7ff9a638.bin' if i==1670 else f'war/{i}.raw';(ROOT/'analysis'/p).write_bytes(b)
 def decode(raw):
  return ''.join('{ICON:'+p.hex()+'}' if p.startswith(b'\xe1\xa0') else p.decode('cp932') for p in re.split(rb'(\xe1\xa0[\x00-\xff])',raw))
 b=(ROOT/'analysis/candidates/1670_7ff9a638.bin').read_bytes();n=struct.unpack_from('<I',b,4)[0];loc=[]
 for i in range(n-1):
  off=struct.unpack_from('<I',b,12+4*i)[0]
  if off:
   raw=b[off:b.index(0,off)];loc.append(dict(id=i,offset=off,source=decode(raw),raw=raw.hex()))
 save('analysis/locals_ja.json',loc)
 subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/extract_subtitles.py')],cwd=ROOT,check=True)
 sub=json.loads((ROOT/'analysis/subtitles.json').read_text(encoding='utf8'))
 for x in sub:
  for t in x['texts']:
   if t['lang']==5:t['source']=decode(bytes.fromhex(t['raw']))
 save('analysis/subtitles.json',sub)
 b=(ROOT/'analysis/SLPS_258.56').read_bytes();gs=[]
 for i in range(1250):
  c,x,y,w,h=struct.unpack_from('<H4B',b,0x298ed0+i*6);gs.append(dict(code=c,x=x,y=y,w=w,h=h&31,page=h>>5))
 save('analysis/glyphs.json',gs)
 import movie_subtitles
 movie_subtitles.extract()
 print('추출 완료: 메뉴',len(loc),'자막 블록',len(sub))
if __name__=='__main__':main()
