# Round 1 제출 체크리스트 (2026-10-31 기준, 패키지 항목은 2026-11-13 갱신)

마감 2026-11-16(월) 16:45 KST, 제출 계획 11/14(토). 규정: 제안서 답변 10개 합계 500단어 이하(선언·이름·서명·제3자 라이선스 정보 제외). 상태: **완료** / **남음-Claude** / **남음-사용자 계정 필요**.

## 패키지 (ZIP) — #23, #31

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 폴더명 = name = `fridge-door`, frontmatter는 name·description만 | 완료 | 로컬 검사기 통과 |
| description ≤1,024자, "Use when" 포함, 명령형 아님 | 완료 | 로컬 검사기 통과 |
| Generation-time capability evidence 6줄 | 완료 | SKILL.md 상단. 2026-11-13 `file-workflow` → `file-agent` 추가(그림 복사). 키트 0.7.7 카탈로그의 CLI→agent 값과 로컬 검사기로 대조 일치 |
| delegate 규칙(한 줄·작은따옴표·`'"'"'` 이스케이프만·파이프/리다이렉트 없음) | 완료 | 로컬 검사기 + 214개 테스트(2026-11-13, 3차 수정 반영). 지시문에 CLI·Action·파라미터 이름 없음(테스트로 확인) |
| 5개 상태 토큰, "no results", "real result"/"upstream" 문구 | 완료 | 로컬 검사기 |
| 금지어 grep 0건, 코드 펜스 언어 태그 없음, 과장어 없음 | 완료 | 로컬 검사기 plan 레이어로 2026-11-13 재확인. "Nothing leaves the NAS" 류 절대 단정 문구 없음(테스트) |
| references 전부 SKILL.md에서 직접 링크 | 완료 | 4개 파일 링크됨 |
| 루트에 README·.DS_Store·스크립트 없음, `__MACOSX` 없음 | 완료 | ZIP 5개 파일, 해당 항목 0건 |
| 로컬 검사 `scripts/check.py fridge-door --summary --catalog <키트>/data/capability-catalog.json` | 완료 | 0 error, 0 warning, catalog 2.2.0 (2026-11-13). 기록: docs/checks/check-skill-2026-11-13.md |
| ZIP ≤10 MB, 파일 ≤100, 파일당 ≤1 MB | 완료 | 27,577바이트, 5개 파일 (2026-11-13, 3차 수정 뒤 재빌드) |
| ZIP 빌드 (`dist/fridge-door.zip`) | 완료 | `python3 -m scripts.build_zip`, 2026-11-13 3차 수정 뒤 v1.0.0으로 재빌드(27,577바이트). 압축 해제 내용이 `fridge-door/` 원본과 동일. 패키지를 다시 고치면 재빌드 |
| 공식 `check-skill.mjs` 0 error | 남음-사용자 확인 필요 | 2026-11-13 키트 0.7.7의 `check-lib.mjs`를 소스로만 읽고 규칙(카탈로그 2.2.0 포함)을 로컬 검사기에 옮김. 내려받은 스크립트는 실행하지 않음. 로컬 결과 0/0과 파일 해시는 docs/checks/check-skill-2026-11-13.md. 2026-10-27 공식 기록은 이전 패키지(0.7.0)용이라 지금 파일과 해시가 다름. 사용자가 `node uliya-skill-kit/scripts/check-skill.mjs fridge-door`를 실행하면 해시와 결과를 대조해 기록 추가. 그 전까지 문서는 "local port"로만 표기 |
| v1.0.0 문구 점검(README만 보고 흐름 설명 가능한지 지인 1명 확인) | 남음-사용자 계정 필요 | 지인 확인은 사용자가 해야 함. 반영은 Claude |
| 11/12–11/13 최종 재검사(검사·빌드·테스트 재실행) | 완료 | 2026-11-13: 로컬 검사 0/0(카탈로그 포함), pytest 214 passed·1 skipped, ruff·mypy 통과, ZIP 재빌드. Devpost 문구·갤러리는 3차 수정 패키지(15단계 번호 유지, 출력 폴더 확인을 Step 9 복사 앞으로, 완료 카드 문구 변경)와 맞춤(2026-11-13, 아래 Devpost 절 참고). 제안서는 다른 작업자가 수정 중 |

## 제안서 — #23

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 제안서 PDF 생성 (`docs/proposal/proposal.pdf`) | 남음-Claude | 현재 PDF(90,908바이트, 2026-11-01 생성)는 2026-11-13에 다시 쓴 `proposal.html`보다 오래됨. 제출 전에 HTML에서 PDF를 다시 만들고 크기(≤1 MB)를 기록. 서명 기입 후에도 재생성 |
| 제안서 답변 10개 합계 ≤500단어 (선언·이름·서명·제3자 라이선스 정보 제외) | 완료 | 규정이 바뀜. `python3 scripts/count_proposal_words.py` 출력(2026-11-13): answers: 10  total words: 487 (limit 500); whole page (headings, SVG, footer, signature line), for information: 707; figure labels: 12  answers + figure labels: 499 (limit 500) |
| 제3자 구성요소·AI 도구 명시 | 완료 | 제안서 하단 |
| 제안서 문구 "local port of the official checker rules" | 완료 | 공식 키트 미설치라 "official checker 통과" 대신 로컬 포트로 표기(사실과 일치). 공식 재실행은 키트 확보 시 선택 |
| 이름·서명·날짜(`Date: 2026-11-__`) | 남음-사용자 계정 필요 | 사용자 본인 서명·날짜. 기입 후 PDF 재생성은 Claude 가능 |
| 개인정보 없음(학교·아이 이름·전화번호 가상) | 완료 | 테스트 자료는 가상 데이터(`02-000-0000`) |
| 16장 테스트킷 실물 이미지 | 남음-Claude | 명세만 있고 이미지는 Round 2 전 준비(#28). Round 1 제출물 아님 |

## Devpost 페이지 — #30

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 영어 스토리(항목별 붙여넣기용) | 완료 | `docs/submission/devpost.md`, 2026-11-13에 2차 수정 패키지에 맞춰 다시 씀(키트 0.7.7, 카탈로그 2.2.0, 테스트 214개, ZIP 5개 파일 27,577바이트, test-plan 미확인 가정 19개(3차 수정 반영), 공식 check-skill.mjs 미실행·장비 미실행 명시). 새 기능(아이의 말, 작품 일지)과 "지난 다이제스트가 멈춘 곳에서 시작" 반영. Inspiration 현장 이야기는 비워 둠(사용자가 제공 예정) |
| 썸네일 1200×800 | 완료 | `docs/submission/gallery/thumbnail.png` (2026-11-13 재생성, 다이제스트 카드와 앨범 타일 추가) |
| 갤러리 2장 이상 | 완료 | 5장(`00-chat`~`04-privacy`, 1500×1000), 2026-11-13에 2차 수정 패키지 기준으로 다시 만듦(15단계 번호, Step 8 미리보기·Step 15 완료 카드 형식, 아이의 말, 태그 7장). 3차 수정 뒤 `00-chat`(완료 카드 문구·저장 파일 이름), `02-digest`(메타 줄), `03-delegation`(Step 9 출력 폴더 확인)만 고쳐 같은 크기로 재생성. `00-chat`·`02-digest`는 제목 옆에 "Simulated dry run, not a device screenshot" 표기, 카드 날짜는 2026-11-23 주간 샘플. 이후 패키지 예시(IMG_0107은 부모 답 뒤 Mina, Mina 폴더 복사 2건, 앨범 Artwork - Mina 1개·2장)에 맞춰 `00-chat`·`02-digest`·`04-privacy`를 고쳐 재생성 |
| 라이선스(MIT)·AI 도구(Claude Code, UGOS Skill Creation Tool 0.7.7)·제3자 none 공개문 | 완료 | devpost.md 하단 |
| 저장소 공개 여부 결정 | 완료 (2026-11-01 공개) | `sh0sub/fridge-door` 공개 확인 |
| 트랙 선택(Bring Memories to Life) | 남음-사용자 계정 필요 | Devpost 폼 |
| 폼에 텍스트·이미지·ZIP·PDF 입력 후 제출 | 남음-사용자 계정 필요 | Devpost 로그인 필요 |
| 제출 후 Round 1 자료 삭제 금지 | 남음-사용자 계정 필요 | 제출 후 수정·삭제하지 않기 |

## 제출 — #32

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 제출 후 수정 금지 항목 점검 | 남음-Claude | 11/14 직전 목록 정리 |
| 제안서 PDF + Skill ZIP 제출 | 남음-사용자 계정 필요 | 11/14(토) 권장, 마감 11/16 16:45 KST |

## S3 준수 — #23

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 이름·설명이 기능과 일치, 과장어 없음 | 완료 | 직접 확인 |
| UGREEN 공식 사칭 요소 없음 | 완료 | README·갤러리에 "independent community Skill, not an official UGREEN product" 명시 |
