# Round 1 제출 체크리스트 (2026-10-31 기준)

마감 2026-11-16(월) 16:45 KST, 제출 계획 11/14(토). 상태: **완료** / **남음-Claude** / **남음-사용자 계정 필요**.

## 패키지 (ZIP) — #23, #31

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 폴더명 = name = `fridge-door`, frontmatter는 name·description만 | 완료 | 로컬 검사기 통과 |
| description ≤1,024자, "Use when" 포함, 명령형 아님 | 완료 | 로컬 검사기 통과 |
| Generation-time capability evidence 5줄 | 완료 | SKILL.md 상단 |
| delegate 규칙(한 줄·작은따옴표·target 6개 이내·파이프/리다이렉트 없음) | 완료 | 로컬 검사기 + 123개 테스트 |
| 5개 상태 토큰, "no results", "real result"/"upstream" 문구 | 완료 | 로컬 검사기 |
| 금지어 grep 0건, 코드 펜스 언어 태그 없음, 과장어 없음 | 완료 | 2026-10-31 직접 grep 확인 |
| references 전부 SKILL.md에서 직접 링크 | 완료 | 4개 파일 링크됨 |
| 루트에 README·.DS_Store·스크립트 없음, `__MACOSX` 없음 | 완료 | ZIP 5개 파일, 해당 항목 0건 |
| 로컬 검사 `scripts/check.py fridge-door --summary` | 완료 | 0 error, 0 warning (2026-10-31) |
| ZIP ≤10 MB, 파일 ≤100, 파일당 ≤1 MB | 완료 | 15,854바이트, 5개 파일, 최대 20,074바이트(SKILL.md) |
| ZIP 빌드 (`dist/fridge-door.zip`) | 완료 | `python3 -m scripts.build_zip`. 최종 제출 직전(11/13) 재빌드 필요 |
| 공식 `check-skill.mjs` 0 error | 남음-Claude | 공식 키트가 이 환경에 없음. 2026-10-27 공식 실행 기록(docs/checks)이 있으나 이후 `references/test-plan.md`가 바뀌어(해시 불일치) 기록이 낡음. 2026-11-01 키트 0.7.3(37,575 B)는 다시 받았으나 내려받은 스크립트 실행이 권한 시스템에서 거부되어 실행 못 함. 사용자가 `node uliya-skill-kit/scripts/check-skill.mjs fridge-door`를 실행하거나 실행을 허용하면 결과·해시로 docs/checks를 갱신하고 ZIP을 다시 빌드. 그 전까지 문서는 "local port"로만 표기 |
| v0.9.0 문구 점검(README만 보고 흐름 설명 가능한지 지인 1명 확인) | 남음-사용자 계정 필요 | 지인 확인은 사용자가 해야 함. 반영은 Claude |
| 11/12–11/13 최종 재검사(검사·빌드·테스트 재실행) | 남음-Claude | #31 |

## 제안서 — #23

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 제안서 PDF 생성 (`docs/proposal/proposal.pdf`) | 완료 | 90,908바이트 (≤1 MB) |
| 제안서 전체 페이지(항목 제목·SVG·푸터·서명줄 포함) ≤500단어 | 완료 | `scripts/count_proposal_words.py`: 전체 484단어, 답변 10개만 400단어. 공식 규정 원문은 "영어 ≤500단어"뿐이라 가장 넓은 기준(전체 페이지)으로 맞춤 |
| 제3자 구성요소·AI 도구 명시 | 완료 | 제안서 하단 |
| 제안서 문구 "local port of the official checker rules" | 완료 | 공식 키트 미설치라 "official checker 통과" 대신 로컬 포트로 표기(사실과 일치). 공식 재실행은 키트 확보 시 선택 |
| 이름·서명·날짜(`Date: 2026-11-__`) | 남음-사용자 계정 필요 | 사용자 본인 서명·날짜. 기입 후 PDF 재생성은 Claude 가능 |
| 개인정보 없음(학교·아이 이름·전화번호 가상) | 완료 | 테스트 자료는 가상 데이터(`02-000-0000`) |
| 16장 테스트킷 실물 이미지 | 남음-Claude | 명세만 있고 이미지는 Round 2 전 준비(#28). Round 1 제출물 아님 |

## Devpost 페이지 — #30

| 항목 | 상태 | 근거·메모 |
|---|---|---|
| 영어 스토리(항목별 붙여넣기용) | 완료 | `docs/submission/devpost.md` |
| 썸네일 1200×800 | 완료 | `docs/submission/gallery/thumbnail.png` |
| 갤러리 2장 이상 | 완료 | 5장(`00-chat`~`04-privacy`, 1500×1000). `00-chat`·`02-digest`는 제목 옆에 "Simulated dry run, not a device screenshot" 표기, 카드 날짜는 2026-11-23~12-12 샘플 |
| 라이선스(MIT)·AI 도구(Claude Code, UGOS Skill Creation Tool 0.7.3)·제3자 none 공개문 | 완료 | devpost.md 하단 |
| 저장소 공개 여부 결정 | 남음-사용자 계정 필요 | `sh0sub/fridge-door`가 현재 비공개. 공개하거나 devpost.md "Try it out"의 저장소 줄 삭제 |
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
