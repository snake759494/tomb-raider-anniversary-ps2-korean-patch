"""xdelta 생성 후 파일을 추가로 남기지 않고 전체 복원 스트림을 검증한다."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 m=json.loads((ROOT/'build/manifest.json').read_text(encoding='utf8'));src=ROOT/m['source'];dst=ROOT/m['target'];patch=ROOT/'build/Tomb_Raider_Anniversary_SLPS25856_KO.xdelta';exe=str(ROOT/'xdelta.exe')
 assert digest(src)==m['source_sha256'];assert digest(dst)==m['target_sha256']
 subprocess.run([exe,'-e','-f','-9','-B','67108864','-s',str(src),str(dst),str(patch)],check=True)
 h=hashlib.sha256();size=0
 with subprocess.Popen([exe,'-d','-c','-s',str(src),str(patch)],stdout=subprocess.PIPE,stderr=subprocess.PIPE) as p:
  for b in iter(lambda:p.stdout.read(8<<20),b''):h.update(b);size+=len(b)
  err=p.stderr.read();assert p.wait()==0,err
 assert size==dst.stat().st_size and h.hexdigest()==m['target_sha256']
 report=dict(status='통과',patch=patch.name,patch_size=patch.stat().st_size,patch_sha256=digest(patch),reconstructed_size=size,reconstructed_sha256=h.hexdigest(),source_sha256=m['source_sha256'],temporary_iso_created=False)
 (ROOT/'build/xdelta_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
