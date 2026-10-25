# 툼 레이더: 애니버서리 PS2 한글패치

PS2 일본판 **Lara Croft Tomb Raider: Anniversary (SLPS-25856)** 비공식 한글패치 **v1.0.1**입니다.

[패치 다운로드](https://github.com/snake759494/tomb-raider-anniversary-ps2-korean-patch/releases/tag/v1.0.1)

## 적용 범위

- 메뉴·설정·저장 안내·일지·탐색 힌트·유물 설명·인물 소개·음악 목록
- 본편 대사 및 개발자 해설의 일본어 자막 채널
- 영상용 SCH 대사 19개 전체 및 영상 전용 글꼴
- 보스전 등 레벨 파일에 내장된 대사 15개
- 조작 그림 4종, 일반 한글 852자, 직접 번역·검토한 고유 문자열 2,360종

외부 기계 번역 서비스는 사용하지 않았습니다. 작업 폴더의 9종 글꼴을 비교해 원본에 가장 가까운 **나눔스퀘어 네오 Regular**를 사용했습니다. 음성은 원본 그대로입니다. 영상에 구워진 영문 지명·제작진·권리 고지·로고와 배경 장식 문자는 유지합니다.

## 패치 적용 방법

1. 해시가 아래와 일치하는 일본판 원본 ISO를 준비합니다. 다른 지역판이나 이미 패치된 ISO에는 적용하지 않습니다.
2. 릴리즈에서 `TombRaiderAnniversary_PS2_KO_v1.0.1.xdelta`를 받습니다. 첨부 파일은 xdelta 하나입니다.
3. xdeltaUI에서 Apply Patch를 선택하고 Patch에 xdelta, Source File에 원본 ISO, Output File에 별도의 새 ISO 경로를 지정합니다.
4. 완성 ISO를 새로 부팅합니다. 이전 에뮬레이터 상태 저장은 불러오지 마세요. 자막 표시를 켜세요.

명령줄 적용:

```powershell
xdelta3 -d -s "Lara Croft Tomb Raider - Anniversary (Japan).iso" "TombRaiderAnniversary_PS2_KO_v1.0.1.xdelta" "Tomb_Raider_Anniversary_SLPS25856_KO.iso"
```

Python 해시 검증 적용 도구도 제공합니다. 저장소 루트에 패치와 별도로 확보한 `xdelta.exe`를 놓은 뒤 실행합니다. 기존 출력 파일과 잘못된 원본을 거부하고 결과 해시를 확인합니다.

```powershell
python -X utf8 tools/apply_patch.py "Lara Croft Tomb Raider - Anniversary (Japan).iso" "별도_한글판.iso"
```

## 파일 식별

| 항목 | 값 |
| --- | --- |
| 게임 번호 | SLPS-25856 |
| 원본/결과 ISO 크기 | 4,201,054,208 바이트 |
| 원본 SHA-256 | `c045214d7863be1d1e40f445809ce9db9b4ecbc539ef2b6c69783f51bb8c7640` |
| 결과 SHA-256 | `b6511042d9b1b26fa61fad4b6216d615b915ab3031420e63e6bbfefe13f32d15` |
| 패치 크기 | 305,763 바이트 |
| 패치 SHA-256 | `999cbbf8eaeea4ae29f252e9e5138becdae5b228b9ebc7d41bd5101ec3af7497` |


## 검증 범위

전체 아카이브 및 일반 ISO 파일 검사, 문자열 왕복·제어 바이트·자막 시각·영문 채널 보존 검사, xdelta 전체 복원 SHA-256 일치를 확인했습니다. 수정본 새 부팅·타이틀·설정·초반 일반 자막을 확인했으며, 제보한 영상 자막이 한글로 표시됨을 사용자가 직접 확인했습니다.

전체 스테이지 완주, 모든 화면의 줄바꿈·잘림, 저장/불러오기 왕복, PS2 실기는 미검증입니다. 정식 릴리즈 표시는 이러한 미검증 범위의 보증을 뜻하지 않습니다. 실행 파일 CRC는 `95FB1C26`이며 원본 CRC용 에뮬레이터 치트/패치가 자동으로 적용되지 않을 수 있습니다.

[재빌드](docs/BUILD.md) · [기술 설명](docs/TECHNICAL.md) · [검증 기록](validation/) · [권리 안내](RIGHTS.md)
