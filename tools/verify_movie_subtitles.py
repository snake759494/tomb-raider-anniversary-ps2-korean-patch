"""영상 자막의 모든 시각, 언어 채널, 문자표, 픽셀과 ISO 반영을 독립 검사."""
import json,struct,hashlib,re
import numpy as np
import build_patch as bp
import movie_subtitles as ms
import gs
ROOT=bp.ROOT
texts=bp.translations();cmap=bp.readj('translation/hangul_map.json');enc=bp.codec(cmap)
src=ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso';dst=ROOT/'Tomb_Raider_Anniversary_SLPS25856_KO.iso'
rows=ms.extract();manifest=bp.readj('build/manifest.json');changes={m['index']:m for m in manifest['changes']}
report={'status':'통과','scanned_archive_entries':len(bp.ES),'movie_files':len(rows),'cues':[]}
with dst.open('rb') as f:
 for r in rows:
  m=changes[r['entry']];f.seek(bp.BASE+m['new_offset']);new=f.read(m['new_size']);old=bytes.fromhex(r['raw'])
  ol=list(ms.LINE.finditer(old));nl=list(ms.LINE.finditer(new));assert len(ol)==len(nl)
  assert ms.LINE.sub(b'',old)==ms.LINE.sub(b'',new)
  for x,y in zip(ol,nl):
   assert x[1]==y[1] and x[3]==y[3]
   if not x[1].startswith(b'lang_japanese '):assert x[0]==y[0];continue
   oc=list(ms.CUE.finditer(x[2]));nc=list(ms.CUE.finditer(y[2]));assert len(oc)==len(nc)==19
   for a,b in zip(oc,nc):
    source=a[2].decode('cp932');target=texts[source]
    assert a[1]==b[1] and b[2]==enc(target) and not bp.JP.search(target)
    report['cues'].append(dict(time=a[1].decode(),source=source,translation=target))
 elfinfo=next(x for x in bp.FILES if x['path']=='/SLPS_258.56;1');f.seek(elfinfo['lba']*2048);elf=f.read(elfinfo['size'])
 oldelf=(ROOT/'analysis/SLPS_258.56').read_bytes();assert elf[:0x29ac20]==oldelf[:0x29ac20] and elf[0x29b058:]==oldelf[0x29b058:]
 table=[struct.unpack_from('<H4B',elf,0x29ac20+i*6) for i in range(180)]
 assert all(a[0]<b[0] for a,b in zip(table,table[1:]));table={g[0]:g[1:] for g in table}
 m=changes[783];f.seek(bp.BASE+m['new_offset']);new=f.read(m['new_size']);old=(ROOT/'analysis/war/783.raw').read_bytes()
 assert old[:1184]==new[:1184] and old[66720:]==new[66720:]
 oa=np.frombuffer(gs.unswizzle8(old[1184:66720],256,256),np.uint8).reshape(256,256)
 na=np.frombuffer(gs.unswizzle8(new[1184:66720],256,256),np.uint8).reshape(256,256)
 used=np.zeros((256,256),bool);ascii_count=0
 oldtable={struct.unpack_from('<H',oldelf,0x29ac20+i*6)[0]:struct.unpack_from('<4B',oldelf,0x29ac22+i*6) for i in range(180)}
 for code,(x,y,w,h) in table.items():
  assert h==19 and x+w<=256 and y+h<=256 and not used[y:y+h,x:x+w].any();used[y:y+h,x:x+w]=True
  if code<128:
   ox,oy,ow,oh=oldtable[code];assert w==ow and np.array_equal(oa[oy:oy+oh,ox:ox+ow],na[y:y+h,x:x+w]);ascii_count+=1
 for cue in report['cues']:
  width=0
  for c in cue['translation']:
   code=cmap[c] if c in cmap else ord(c);assert code in table;width+=table[code][2]
  cue['glyph_width']=width
  assert width<=600,('화면 너비 초과',cue)
 report.update(glyphs=len(table),preserved_ascii_glyphs=ascii_count,korean_glyphs=len(table)-ascii_count,elf_change_range=['0x29ac20','0x29b058'],iso_sha256=manifest['target_sha256'])
bp.writej('build/movie_subtitle_verification.json',report)
print('영상 자막 19개, 시각, 글꼴 180자, 원본 영문 픽셀 보존 검증 통과')
