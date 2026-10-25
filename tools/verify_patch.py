from pathlib import Path
import json,struct,hashlib,collections,sys
sys.path.insert(0,str(Path(__file__).parent));import build_patch as bp
root=bp.ROOT;src=root/'Lara Croft Tomb Raider - Anniversary (Japan).iso';dst=root/'Tomb_Raider_Anniversary_SLPS25856_KO.iso'
manifest=bp.readj('build/manifest.json');changes={x['index']:x for x in manifest['changes']};texts=bp.translations();cmap=bp.readj('translation/hangul_map.json');enc=bp.codec(cmap)
rev={v:k for k,v in cmap.items()}
assert all(t['source'] in texts for x in bp.SUB for t in x['texts'] if t['lang']==5), 'Untranslated Japanese-language subtitle channel'
def decode(b):
 out='';i=0
 while i<len(b):
  if b[i:i+2]==b'\xe1\xa0' and i+2<len(b):out+='{ICON:'+b[i:i+3].hex()+'}';i+=3
  elif b[i]<128:out+=chr(b[i]);i+=1
  else:
   code=int.from_bytes(b[i:i+2],'big')
   if code in rev:out+=rev[code];i+=2
   else:
    n=2 if b[i]>=0xe0 or 0x81<=b[i]<=0x9f else 1;out+=b[i:i+n].decode('cp932');i+=n
 return out
for t in texts.values():assert decode(enc(t))==t
byentry=collections.defaultdict(list)
for x in bp.SUB:byentry[x['entry']].append(x)
def blocks(b):
 p=0x800;out=[]
 while p+16<=len(b):
  ty,sz=struct.unpack_from('<II',b,p)
  if ty>3 or p+16+sz>len(b):break
  out.append((p,ty,b[p:p+16+sz]));p+=16+sz
 return out,b[p:]
count=collections.Counter();ranges=[]
with src.open('rb') as a,dst.open('rb') as b:
 b.seek(bp.BASE);head=b.read(4+len(bp.ES)*20);assert struct.unpack_from('<I',head)[0]==len(bp.ES)
 a.seek(bp.BASE);assert a.read(4+len(bp.ES)*4)==head[:4+len(bp.ES)*4]
 for e in bp.ES:
  idx=e['index'];sz,sector,mask,comp=struct.unpack_from('<4I',head,4+len(bp.ES)*4+idx*16);off=sector*2048
  assert mask==int(e['mask'],16) and comp==e['compressed'];assert bp.BASE+off+sz<=dst.stat().st_size
  a.seek(bp.BASE+e['offset']);old=a.read(e['size']);b.seek(bp.BASE+off);new=b.read(sz);ranges.append((off,off+sz,idx))
  if idx not in changes:assert old==new,('unexpected change',idx);count['unchanged_archive_entries']+=1;continue
  m=changes[idx];assert off==m['new_offset'] and sz==m['new_size'];assert hashlib.sha256(new).hexdigest()==m['sha256'];count['changed_archive_entries']+=1
  if idx in (1670,1671):
   n=struct.unpack_from('<I',old,4)[0];assert old[:12]==new[:12]
   expected={x['id']:x for x in bp.LOC}
   for i in range(n-1):
    op=struct.unpack_from('<I',old,12+i*4)[0];np=struct.unpack_from('<I',new,12+i*4)[0]
    if not op:assert not np;continue
    x=expected[i];want=enc(texts[x['source']]) if x['source'] in texts else bytes.fromhex(x['raw']);assert 0<np<len(new);actual=new[np:new.index(0,np)];assert actual==want
    count['locals_records_verified']+=1
  elif idx in byentry:
   assert new[:0x800]==old[:0x800];ob,ot=blocks(old);nb,nt=blocks(new);assert len(ob)==len(nb) and ot==nt
   patches={x['block_offset']:x for x in byentry[idx]}
   for (op,ty,ov),(np,nty,nv) in zip(ob,nb):
    assert ty==nty
    if op not in patches:assert ov==nv;count['unchanged_mul_blocks']+=1;continue
    x=patches[op];st=x['text_offset']-4-op;prefix=bytearray(ov[:st]);struct.pack_into('<I',prefix,4,len(nv)-16)
    if x['block']!=0:struct.pack_into('<I',prefix,16,len(nv)-20)
    assert nv[:st]==prefix
    length=struct.unpack_from('<I',nv,st)[0];parts=nv[st+4:st+4+length].split(b'\r');assert parts[-1]==b'';assert len(parts)==2*len(x['texts'])+1
    for j,t in enumerate(x['texts']):
     assert int(parts[j*2])==t['lang'];want=enc(texts[t['source']]) if t['lang']==5 and t['source'] in texts else bytes.fromhex(t['raw']);assert parts[j*2+1]==want
     count['translated_subtitle_instances' if t['lang']==5 and t['source'] in texts else 'preserved_subtitle_instances']+=1
    assert not any(nv[st+4+length:]);count['subtitle_blocks_verified']+=1
 # Compare every ISO file other than archive, in chunks.
 for f in bp.FILES:
  if f['path']=='/BIGFILE.DAT;1':continue
  if f['path']=='/SLPS_258.56;1':
   a.seek(f['lba']*2048);b.seek(f['lba']*2048);oe=a.read(f['size']);ne=b.read(f['size'])
   assert oe[:0x29ac20]==ne[:0x29ac20] and oe[0x29b058:]==ne[0x29b058:]
   count['movie_glyph_table_modified']+=1
   continue
  a.seek(f['lba']*2048);b.seek(f['lba']*2048);left=f['size']
  while left:
   n=min(left,8<<20);assert a.read(n)==b.read(n),f['path'];left-=n
  count['unchanged_iso_files']+=1
ranges.sort()
for x,y in zip(ranges,ranges[1:]):
 if x[0]!=y[0]:assert x[1]<=y[0],('overlap',x,y)
import pycdlib
iso=pycdlib.PyCdlib();iso.open(str(dst))
for f in bp.FILES:
 rec=iso.get_record(iso_path=f['path']);assert rec.extent_location()==f['lba']
 if f['path']!='/BIGFILE.DAT;1':assert rec.data_length==f['size']
iso.close()
report=dict(status='통과: 바이너리 무결성과 문자열 왕복',counts=dict(count),unique_sources=len(texts),unique_direct_translations=sum(k!=v for k,v in texts.items()),hangul_glyphs=len(cmap),source_sha256=bp.digest(src),target_sha256=bp.digest(dst),limitations=['실행 검증은 별도 보고서 참조.','전체 플레이 미확인.'])
bp.writej('build/verification.json',report);print(json.dumps(report,ensure_ascii=True,indent=2))

