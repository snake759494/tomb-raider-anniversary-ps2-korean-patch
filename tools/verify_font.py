from pathlib import Path
import json,numpy as np
import build_patch as bp,gs
def main():
 m=bp.readj('build/manifest.json');changes={x['index']:x for x in m['changes']};cmap=bp.readj('translation/hangul_map.json');codes=set(cmap.values());glyphs=[g for g in bp.GLYPHS if g['code'] in codes];assert len(glyphs)==len(cmap)==m['hangul_count']
 report=[]
 with (bp.ROOT/m['target']).open('rb') as f:
  for page,entry in enumerate(bp.PAGES):
   old=(bp.ROOT/f'analysis/war/{entry}.raw').read_bytes();e=changes[entry];f.seek(bp.BASE+e['new_offset']);new=f.read(e['new_size']);assert len(new)==len(old)
   assert old[:1184]==new[:1184] and old[1184+65536:]==new[1184+65536:]
   a=np.frombuffer(gs.unswizzle8(old[1184:1184+65536],256,256),np.uint8).reshape(256,256);b=np.frombuffer(gs.unswizzle8(new[1184:1184+65536],256,256),np.uint8).reshape(256,256);mask=np.zeros((256,256),bool)
   for g in glyphs:
    if g['page']!=page:continue
    x,y=g['x'],g['y'];assert x+19<=256 and y+19<=256;assert not mask[y:y+19,x:x+19].any();mask[y:y+19,x:x+19]=True
   assert np.array_equal(a[~mask],b[~mask]);report.append(dict(page=page,entry=entry,unchanged_outside_hangul_slots=True,header_and_palette_unchanged=True))
 bp.writej('build/font_verification.json',dict(status='통과',glyph_count=len(glyphs),pages=report));print(f'한글 {len(glyphs)}자 및 폰트 7개 페이지의 비수정 영역 보존 확인')
if __name__=='__main__':main()
