"""보스전 등 14형식 레벨 파일에 내장된 길이 접두 자막을 추출/재구성한다.
뒤따르는 데이터 위치를 보존하기 위해 일본어 채널을 같은 바이트 길이로 교체한다."""
import json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ENTRIES=[179,298,2207,2638,2910]
TEXT=re.compile(rb'(?s)(....)(0\r[^\r]*\r5\r)([^\r]*)\r')

def extract():
 es=json.loads((ROOT/'analysis/bigfile_index.json').read_text());out=[]
 with (ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso').open('rb') as f:
  for idx in ENTRIES:
   e=es[idx];f.seek(662598*2048+e['offset']);b=f.read(e['size']);assert struct.unpack_from('<I',b)[0]==14
   for m in TEXT.finditer(b):
    assert struct.unpack('<I',m[1])[0]==len(m[0])-4,(idx,m.start())
    out.append(dict(entry=idx,offset=m.start(3),length=len(m[3]),source=m[3].decode('cp932')))
 assert len(out)==15,len(out)
 (ROOT/'analysis/level_subtitles.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 return out

def rebuild(rows,texts,enc):
 es=json.loads((ROOT/'analysis/bigfile_index.json').read_text());result={}
 with (ROOT/'Lara Croft Tomb Raider - Anniversary (Japan).iso').open('rb') as f:
  for idx in ENTRIES:
   e=es[idx];f.seek(662598*2048+e['offset']);result[idx]=bytearray(f.read(e['size']))
 for x in rows:
  b=result[x['entry']];p=x['offset'];assert b[p:p+x['length']]==x['source'].encode('cp932')
  raw=enc(texts[x['source']]);assert len(raw)<=x['length'],('자막 길이 초과',x,texts[x['source']])
  b[p:p+x['length']]=raw+b' '*(x['length']-len(raw))
 return {k:bytes(v) for k,v in result.items()}

if __name__=='__main__':
 rows=extract();print('레벨 자막',len(rows))
