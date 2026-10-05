import pathlib,json,struct,re,collections
es=json.loads(pathlib.Path('analysis/bigfile_index.json').read_text());out=[];base=662598*2048
with pathlib.Path('Lara Croft Tomb Raider - Anniversary (Japan).iso').open('rb') as f:
 for e in es:
  if e['size']<2064:continue
  f.seek(base+e['offset']);h=f.read(128)
  if h[:4]==b'!WAR' or struct.unpack_from('<I',h)[0]==14 or struct.unpack_from('<I',h,4)[0]!=0xffffffff:continue
  f.seek(base+e['offset']);b=f.read(e['size']);pos=0x800;block=0
  while pos+16<=len(b):
   typ,size=struct.unpack_from('<II',b,pos)
   if typ>3 or size>len(b)-pos-16:break
   if typ==1 and size>16:
    ar=b[pos+16:pos+16+size];end=len(ar.rstrip(b'\0'))-1
    if end>=0 and ar[end]==13:
     for st in range(end-end%4-4,0,-4):
      if struct.unpack_from('<I',ar,st)[0]==end-st-3:
       raw=ar[st+4:end+1];parts=raw.split(b'\r')
       if len(parts)%2==1 and all(p.isdigit() for p in parts[:-1:2]):
        out.append(dict(entry=e['index'],block=block,block_offset=pos,text_offset=pos+16+st+4,length=end-st-3,texts=[dict(lang=int(parts[j]),raw=parts[j+1].hex(),source=parts[j+1].decode('cp932','replace')) for j in range(0,len(parts)-1,2)]))
       break
   if typ==1:block+=1
   pos+=16+size
pathlib.Path('analysis/subtitles.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('blocks',len(out),'langs',collections.Counter(t['lang'] for x in out for t in x['texts']));print(str(out[:2])[:1500])
