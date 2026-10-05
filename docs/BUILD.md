# 재빌드

Python 3.10 이상과 requirements.txt의 의존성을 준비하세요. 저장소 루트에 지원 원본 ISO(README의 이름과 해시), NanumSquareNeo-bRg.ttf, 별도로 확보한 xdelta.exe를 둡니다. 배포 파일에는 포함되지 않습니다.

```powershell
python -m pip install -r requirements.txt
python -X utf8 tools/prepare.py
python -X utf8 tools/build_patch.py
python -X utf8 tools/verify_patch.py
python -X utf8 tools/verify_font.py
python -X utf8 tools/verify_movie_subtitles.py
python -X utf8 tools/make_patch.py
```

원문은 원본 ISO에서 로컬로 추출됩니다. 공개 번역 파일은 원문 UTF-8 문자열의 SHA-256을 키로 사용하므로 원문 대사 데이터가 포함되지 않습니다. 추출 문자열의 해시를 한글 번역과 연결하며 누락·아이콘·서식 변수 검사를 수행합니다.

analysis/ 및 build/는 로컬 생성 폴더입니다. validation/은 공개 릴리즈 당시의 검증 기록입니다. 폰트 파일 또는 Pillow 버전에 따라 재생성 픽셀이 달라질 수 있으므로 공개 결과 해시와 비교하세요. 빌드는 원본을 변경하지 않으며 저장소 루트의 결과 ISO를 재생성합니다. 실행 중인 ISO를 닫고 빌드하세요.
