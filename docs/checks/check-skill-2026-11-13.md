# 로컬 검사기 결과 (uliya-skill-kit 0.7.7 규칙, 2026-11-13)

**공식 `check-skill.mjs`는 실행하지 못했다.** 아래는 키트 0.7.7의 `scripts/check-lib.mjs`를 소스로만 읽고 그 규칙을 옮긴 로컬 검사기 `scripts/check.py`의 결과다. 내려받은 `.mjs`는 실행하지 않았다. 공식 실행 결과가 아니므로 제출 문서에 "official checker passed"라고 쓰지 않는다.

- 실행일: 2026-11-13
- 대상: `fridge-door/` (SKILL.md + references 4종), 패키지 버전 1.0.0
- 명령: `.venv/bin/python scripts/check.py fridge-door --catalog <kit>/data/capability-catalog.json`
- 결과: `status: static-pass`, errors 0 · warnings 0 · info 0, checkFormatVersion 2.0.0, catalog checkedVersion 2.2.0, skillName `fridge-door`
- `--official`(키트 규칙만, plan 체크리스트 제외)도 `static-pass: 0 error, 0 warning`
- 카탈로그 검증: 키트 카탈로그를 `loadCatalogContract()`와 같은 계약(버전 2.2.0, 9개 CLI의 단일 agent 소유)으로 읽어 통과했고, SKILL.md의 근거 줄 6개(`ug-filesystem`, `ug-filemgr`, `file-workflow` → `file-agent`, `ug-photo` → `photo-agent`, `ug-knowledge` → `knowledge-agent`, `ug-document` → `document-agent`)를 그 카탈로그의 CLI→agent 값과 대조해 일치했다. 카탈로그 파일은 라이선스가 불명이라 저장소에 복사하지 않았다.

| 파일 | sha256 |
|---|---|
| SKILL.md | 897280ebb2df9a4f830226a55d38f3edc3da45714079345842bb8830b67aa7f1 |
| references/README.md | 98751eb2b40c57d14883548205fc7c92101713db929800255f9f20cb52e93998 |
| references/digest-format.md | b68c489f966a944e2e179da01d18ea3b5773017b606dcc3ae8b98aac639ede31 |
| references/disclosures.md | ae99027add36a7c7fce5521029cc06e5e7555f0ec0dcdcfcebab0762be092dca |
| references/test-plan.md | 36ab563cd42dfb280bc97afd4a7ba5745e9cca18560ec2f9f9f783ab77bb759e |

참고 해시(대조용, 저장소에 없는 파일):

| 파일 | sha256 |
|---|---|
| 키트 0.7.7 `scripts/check-lib.mjs` (소스로만 읽음) | b6b9e93167e9ab90aa571a3ad10b0bcb92d530e7054a4df7f8c8db5b94f85664 |
| 키트 0.7.7 `data/capability-catalog.json` | 397efb1a07b7e33d7395eea86f125592ccb155a95b692b1f9ca40fae0889041d |
| `dist/fridge-door.zip` (5개 파일, 27,577바이트, 압축 해제 내용이 위 원본과 동일) | c0c5bf07126bd18db69aaf172d1696831a200407b88d0989afd0421430654085 |

같은 날 함께 확인한 것: pytest 214 passed, 1 skipped(`FRIDGE_DOOR_KIT_CATALOG`를 키트 카탈로그로 지정하면 215 passed), ruff·mypy 통과.

3차(마무리) 수정(같은 날) 뒤 다시 실행한 결과다. 위 해시는 3차 수정본 기준이다. SKILL.md 본문 233줄(파일 238줄), delegate 20개(15단계에 17개, 작품 일지 절에 3개). 단계 번호는 그대로이고, 출력 폴더 확인 delegate가 Step 11에서 Step 9의 첫 위임으로 옮겨졌다. 2차 수정본 기록(SKILL.md 235줄, ZIP 25,749바이트, pytest 204 passed)은 이 해시로 대체된다. 검사기 자체도 바뀌었다: 키트 정규식의 `\s`를 JavaScript와 같은 유니코드 공백 클래스(NBSP, U+2000–U+200A, U+3000, BOM 등)로 옮겼고(`js_re`), `trim()`도 같은 집합으로 맞췄다.

정적 검사 통과는 업로드·설치·장비 실행을 증명하지 않는다. 패키지 파일을 고치면 해시가 바뀌므로 다시 실행한다. 공식 스크립트를 실행할 수 있게 되면 `node uliya-skill-kit/scripts/check-skill.mjs fridge-door` 결과를 이 표와 비교해 새 기록을 남긴다. 2026-10-27 기록(`check-skill-2026-10-27.md`, 키트 0.7.3·카탈로그 2.0.0)은 이전 패키지에 대한 것이다.
