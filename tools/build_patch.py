"""Deterministic PS2 Anniversary Korean build. Never modifies source ISO."""
from pathlib import Path
import json,struct,re,collections,hashlib,shutil,sys,math
import numpy as np
from PIL import Image,ImageFont,ImageDraw
import gs
import movie_subtitles
import level_subtitles
ROOT=Path(__file__).resolve().parents[1]
def readj(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def writej(p,obj):(ROOT/p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
ES=readj('analysis/bigfile_index.json');FILES=readj('analysis/iso_files.json');BASE=next(x['lba']*2048 for x in FILES if x['path']=='/BIGFILE.DAT;1')
LOC=readj('analysis/locals_ja.json');SUB=readj('analysis/subtitles.json');GLYPHS=readj('analysis/glyphs.json');PAGES=[3244,2471,1335,595,2817,2077,913]
ICONS=re.compile(r'\{ICON:([0-9a-f]+)\}')
FORMAT=re.compile(r'%(?:[-+0 #]*\d*(?:\.\d+)?[diuoxXfFeEgGcs%])')
JP=re.compile('[\u3040-\u30ff\u4e00-\u9fff]')
def normalized(s):
 for a,b in {'\u3000':' ','：':':','／':'/','（':'(', '）':')','！':'!','？':'?','、':',','。':'.','「':'"','」':'"','『':'"','』':'"','〜':'~','～':'~','…':'...','・':' ','“':'"','”':'"','‘':"'",'’':"'",'−':'-','－':'-','–':'-','—':'-','％':'%','＆':'&','　':' '}.items():s=s.replace(a,b)
 for a,b in {'라틀랜드':'러틀랜드','라트랜드':'러틀랜드','니심라':'니시무라','티와낙':'티와나쿠','지퍼':'집','알리스터':'앨리스터','갈라리':'갈랄리','헬스팩':'구급약','모바일 라이트':'휴대용 조명','수류탄 발사기':'유탄 발사기','샷건':'산탄총','서울리버':'소울 리버','세이브':'저장','무한대':'무한','탄수':'탄약'}.items():s=s.replace(a,b)
 return s

def translations():
 rows=movie_subtitles.extract();level=level_subtitles.extract()
 sources={x['source'] for x in LOC}|{t['source'] for x in SUB for t in x['texts'] if t['lang']==5}|{c['source'] for x in rows for c in x['cues']}|{x['source'] for x in level}
 corpus=readj('translation/ko_by_sha256.json');result={};errors=[]
 for source in sources:
  key=hashlib.sha256(source.encode('utf8')).hexdigest()
  target=corpus.get(key,source)
  if JP.search(target):errors.append(('missing',key))
  if collections.Counter(ICONS.findall(source))!=collections.Counter(ICONS.findall(target)):errors.append(('icons',key))
  if FORMAT.findall(source)!=FORMAT.findall(target):errors.append(('formats',key))
  result[source]=target
 assert len(corpus)==2360 and len(result)==2402
 assert not errors,errors[:3]
 writej('translation/final_text.json',result)
 return result


def fontbuild(texts):
 # Keep all original low-code glyphs and non-Hangul punctuation. Use existing 18x18 Japanese cells.
 chars=sorted({c for s in texts.values() for c in ICONS.sub('',s) if '\uac00'<=c<='\ud7a3'})
 reserved={int.from_bytes(c.encode('cp932'),'big') for s in texts.values() for c in ICONS.sub('',s) if ord(c)>=128 and not '\uac00'<=c<='\ud7a3'}
 slots=[g for g in GLYPHS if g['code']>=0x8000 and g['w']==19 and g['h']==19 and g['code'] not in reserved]
 assert len(chars)<=len(slots),(len(chars),len(slots))
 cmap={c:g['code'] for c,g in zip(chars,slots)};writej('translation/hangul_map.json',cmap)
 font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-bRg.ttf'),64)
 pages={};pals={};originals={}
 for pg,idx in enumerate(PAGES):
  b=(ROOT/f'analysis/war/{idx}.raw').read_bytes();originals[pg]=b
  raw=b[1184:1184+65536];linear=gs.unswizzle8(raw,256,256)
  assert gs.swizzle8(linear,256,256)==raw,'swizzle roundtrip'
  pages[pg]=np.frombuffer(linear,np.uint8).reshape(256,256).copy()
  pal=np.frombuffer(b[144:1168],np.uint8).reshape(256,4);lk=np.arange(256);lk=(lk&~24)|((lk&8)<<1)|((lk&16)>>1);pals[pg]=pal[lk]
 for c,g in zip(chars,slots):
  im=Image.new('L',(72,72));d=ImageDraw.Draw(im);bb=d.textbbox((0,0),c,font=font);d.text(((72-bb[2]+bb[0])//2-bb[0],(72-bb[3]+bb[1])//2-bb[1]),c,font=font,fill=128)
  arr=np.array(im.resize((19,19),Image.Resampling.LANCZOS));pg=g['page'];pal=pals[pg]
  # Select existing white palette entries by nearest alpha; preserve CLUT and all other data.
  candidates=np.where(np.min(pal[:,:3],axis=1)>200)[0]
  assert len(candidates)>8
  idx=candidates[np.argmin(abs(arr[:,:,None].astype(int)-pal[candidates,3].astype(int)),axis=2)]
  pages[pg][g['y']:g['y']+19,g['x']:g['x']+19]=idx
 changed={}
 for pg,idx in enumerate(PAGES):
  b=bytearray(originals[pg]);b[1184:1184+65536]=gs.swizzle8(pages[pg].tobytes(),256,256);changed[idx]=bytes(b)
  ar=pals[pg][pages[pg]];Image.fromarray((ar[:,:,:3]*(ar[:,:,3:4]/128)).clip(0,255).astype('uint8')).save(ROOT/f'build/font_page_{pg}.png')
 return cmap,changed

def codec(cmap):
 def enc(s):
  out=bytearray();pos=0
  for m in ICONS.finditer(s):out.extend(plain(s[pos:m.start()]));out.extend(bytes.fromhex(m[1]));pos=m.end()
  out.extend(plain(s[pos:]));return bytes(out)
 def plain(s):
  out=bytearray()
  for c in s:
   if c in cmap:out.extend(cmap[c].to_bytes(2,'big'))
   elif ord(c)<128:out.append(ord(c))
   else:
    raw=c.encode('cp932');code=int.from_bytes(raw,'big');assert code not in cmap.values(),f'punctuation slot conflict {c}';out.extend(raw)
  return out
 return enc

def rebuild_locals(texts,enc):
 src=(ROOT/'analysis/candidates/1670_7ff9a638.bin').read_bytes();n=struct.unpack_from('<I',src,4)[0];out=bytearray(src[:(n+2)*4]);dedup={}
 for x in LOC:
  raw=enc(texts[x['source']]) if x['source'] in texts else bytes.fromhex(x['raw'])
  if raw not in dedup:dedup[raw]=len(out);out.extend(raw+b'\0')
  struct.pack_into('<I',out,12+x['id']*4,dedup[raw])
 for x in LOC:
  p=struct.unpack_from('<I',out,12+x['id']*4)[0];assert 0<p<len(out) and out.find(0,p)>=p
 return bytes(out)

def rebuild_mul(src,blocks,texts,enc):
 patches={x['block_offset']:x for x in blocks};out=bytearray(src[:0x800]);pos=0x800
 while pos+16<=len(src):
  typ,size=struct.unpack_from('<II',src,pos);end=pos+16+size
  if typ>3 or end>len(src):out.extend(src[pos:]);break
  if pos not in patches:out.extend(src[pos:end]);pos=end;continue
  x=patches[pos];payload=bytearray()
  for t in x['texts']:
   raw=enc(texts[t['source']]) if t['lang']==5 and t['source'] in texts else bytes.fromhex(t['raw'])
   payload.extend(str(t['lang']).encode()+b'\r'+raw+b'\r')
  st=x['text_offset']-4;block=bytearray(src[pos:st])+struct.pack('<I',len(payload))+payload
  block.extend(b'\0'*(-len(block)%16));struct.pack_into('<I',block,4,len(block)-16)
  if x['block']!=0:struct.pack_into('<I',block,16,len(block)-20)
  out.extend(block);pos=end
 return bytes(out)

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def main():
 source=ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso'
 assert digest(source)=='c045214d7863be1d1e40f445809ce9db9b4ecbc539ef2b6c69783f51bb8c7640','지원하지 않는 원본 ISO입니다.'
 texts=translations();cmap,changes=fontbuild(texts);enc=codec(cmap)
 import localize_controls
 changes.update(localize_controls.build())
 movie_rows=movie_subtitles.extract()
 changes.update(movie_subtitles.rebuild(movie_rows,texts,enc))
 changes.update(level_subtitles.rebuild(level_subtitles.extract(),texts,enc))
 elf,changes[783]=movie_subtitles.fontbuild(movie_rows,texts,cmap)
 for s in texts.values():enc(s)
 changes[1670]=changes[1671]=rebuild_locals(texts,enc)
 source=ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso';target=ROOT/'Tomb_Raider_Anniversary_SLPS25856_KO.iso'
 groups=collections.defaultdict(list)
 for x in SUB:groups[x['entry']].append(x)
 with source.open('rb') as f:
  for idx,blocks in groups.items():
   e=ES[idx];f.seek(BASE+e['offset']);src=f.read(e['size']);new=rebuild_mul(src,blocks,texts,enc)
   if new!=src:changes[idx]=new
 print('changes',len(changes),'hangul',len(cmap),flush=True)
 (ROOT/'build/locals_ko.bin').write_bytes(changes[1670])
 shutil.copyfile(source,target)
 archive_size=next(x['size'] for x in FILES if x['path']=='/BIGFILE.DAT;1');cursor=(archive_size+2047)//2048*2048
 positions=sorted(set(e['offset'] for e in ES));limits={v:(positions[i+1] if i+1<len(positions) else archive_size) for i,v in enumerate(positions)};written={};manifest=[]
 with target.open('r+b') as f:
  elf_file=next(x for x in FILES if x['path']=='/SLPS_258.56;1')
  assert len(elf)==elf_file['size'];f.seek(elf_file['lba']*2048);f.write(elf)
  for idx,data in changes.items():
   e=ES[idx];key=(e['offset'],hashlib.sha256(data).hexdigest())
   if key in written:newpos=written[key]
   else:
    newpos=e['offset']
    if len(data)>limits[newpos]-newpos:newpos=cursor;cursor+=(len(data)+2047)//2048*2048
    written[key]=newpos;f.seek(BASE+newpos);f.write(data)
   f.seek(BASE+4+4*len(ES)+16*idx);f.write(struct.pack('<II',len(data),newpos//2048))
   manifest.append(dict(index=idx,old_offset=e['offset'],new_offset=newpos,old_size=e['size'],new_size=len(data),sha256=key[1]))
  # BIGFILE is the last filesystem file. Update all ISO9660 directory copies found in metadata.
  new_archive=max(archive_size,cursor);f.seek(0);meta=bytearray(f.read(299*2048));hits=[]
  for m in re.finditer(b'BIGFILE.DAT;1',meta):
   record=m.start()-33
   if record>=0 and meta[record+32]==13 and struct.unpack_from('<I',meta,record+2)[0]==BASE//2048:
    struct.pack_into('<I',meta,record+10,new_archive);struct.pack_into('>I',meta,record+14,new_archive);hits.append(record)
  assert hits,'ISO directory entry not found'
  newsize=max(source.stat().st_size,BASE+new_archive);newsize=(newsize+2047)//2048*2048
  for sec in range(16,32):
   p=sec*2048
   if meta[p+1:p+6]==b'CD001' and meta[p] in (1,2):struct.pack_into('<I',meta,p+80,newsize//2048);struct.pack_into('>I',meta,p+84,newsize//2048)
  f.seek(0);f.write(meta);f.truncate(newsize)
 writej('build/manifest.json',dict(source=source.name,target=target.name,source_sha256=digest(source),target_sha256=digest(target),font='NanumSquareNeo-bRg.ttf',hangul_count=len(cmap),translated_unique=sum(k!=v for k,v in texts.items()),changes=manifest,iso_directory_records=hits,controls_texture_entries=[1160,1714,2626,3208],translation_method='직접 번역 및 기존 직접 번역 검토; 외부 기계 번역 미사용',status='정적 검증 및 신규 부팅 검증 필요'))
 print('built',target,flush=True)
if __name__=='__main__':main()
