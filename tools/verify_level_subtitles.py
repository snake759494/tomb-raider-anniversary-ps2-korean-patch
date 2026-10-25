"""레벨 내장 자막: 일본어 채널만 같은 길이로 바뀌었는지 독립 검사."""
import build_patch as bp
import level_subtitles as ls
ROOT=bp.ROOT
texts=bp.translations();cmap=bp.readj('translation/hangul_map.json');enc=bp.codec(cmap)
rows=ls.extract();changes={m['index']:m for m in bp.readj('build/manifest.json')['changes']}
src=ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso';dst=ROOT/'Tomb_Raider_Anniversary_SLPS25856_KO.iso'
report={'status':'통과','entries':ls.ENTRIES,'lines':[]}
with src.open('rb') as a,dst.open('rb') as b:
 for idx in ls.ENTRIES:
  e=bp.ES[idx];m=changes[idx];assert m['new_offset']==e['offset'] and m['new_size']==e['size']
  a.seek(bp.BASE+e['offset']);old=a.read(e['size']);b.seek(bp.BASE+m['new_offset']);new=b.read(m['new_size'])
  mask=bytearray(old);mine=[x for x in rows if x['entry']==idx]
  for x in mine:
   p,n=x['offset'],x['length'];t=texts[x['source']];raw=enc(t)
   assert new[p:p+n]==raw+b' '*(n-len(raw)) and not bp.JP.search(t)
   mask[p:p+n]=new[p:p+n];report['lines'].append(dict(entry=idx,bytes=n,used=len(raw),translation=t))
  assert bytes(mask)==new,('일본어 채널 밖 변경',idx)
bp.writej('build/level_subtitle_verification.json',report)
print('레벨 내장 자막',len(report['lines']),'개 검증 통과')
