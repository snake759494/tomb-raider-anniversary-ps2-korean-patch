"""지원 원본의 해시를 확인한 뒤 한글패치를 적용한다."""
from pathlib import Path
import argparse,hashlib,subprocess,json
ROOT=Path(__file__).resolve().parents[1]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
 m=json.loads((ROOT/'validation/manifest.json').read_text(encoding='utf8'))
 if args.output.exists():raise SystemExit('출력 파일이 이미 있습니다. 기존 파일은 덮어쓰지 않습니다.')
 if digest(args.source)!=m['source_sha256']:raise SystemExit('원본 해시가 일치하지 않습니다. 지원 일본판 원본을 사용하세요.')
 v=json.loads((ROOT/'validation/xdelta_verification.json').read_text(encoding='utf8'))
 p=ROOT/v['patch']
 if digest(p)!=v['patch_sha256']:raise SystemExit('패치 파일 해시가 일치하지 않습니다.')
 subprocess.run([str(ROOT/'xdelta.exe'),'-d','-s',str(args.source),str(p),str(args.output)],check=True)
 if digest(args.output)!=m['target_sha256']:raise SystemExit('복원 파일 해시가 일치하지 않습니다.')
 print('패치 적용 및 전체 파일 검증 완료:',args.output)
if __name__=='__main__':main()
