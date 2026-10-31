**2** 추천 2순위 · UGREEN Hackathon 2026 on AI NAS

## fridge-door (냉장고 문 비서) — 폰 백업 속 가정통신문·아이 그림을 NAS 안에서 읽어 주간 할 일과 아이별 작품 앨범으로

- **Round 1 마감(KST)**: 11/16(월) 16:45 D-22 · PST 11/15 23:45

- **Round 2 (파이널 30팀)**: 11/30 23:45 PT = 12/1 16:45 KST

- **상금**: $46,000 Grand $20k · Silver $10k · Bronze $6k · Creative $5k×2

- **타겟 상**: Grand Prize 안전망 Most Creative

- **등록자**: 241명 개인·최대 3인, 한국 허용

- **트랙**: Bring Memories to Life

- **필수 요건**: UGOS Skill Creation Tool + Uliya Skill Development Standard, 등록 expert agent 경유 CLI만

- **제출물**: R1: 제안서 PDF(≤1MB, 10항목, 영어 ≤500단어) + Pre-test Skill ZIP · R2: Final ZIP + 3분 YouTube

출처: [Devpost 공식(S4)](https://ugreenhackathon.devpost.com/) [Hackathon Starter Kit(S1)](https://ai.ugreen.com/pages/hackathon-starter-kit) [uliya-skill-kit-0.7.3-en.zip(S2)](https://cdn.shopify.com/s/files/1/0630/9416/1602/files/uliya-skill-kit-0.7.3-en.zip?v=1790578898) [SkillHub 게시 기준(S3)](https://api.ugnas.com/api/system/v1/ua/agreement/page?agreementCode=skillhub-publish-audit-spec&acceptLanguage=en-US) [UGREEN Photos 문서(S5)](https://support.ugnas.com/detail/article/en-US/222) [Custom Learning(S6)](https://support.ugnas.com/detail/article/en-US/322) [TechRadar 리뷰(S7)](https://www.techradar.com/computing/ugreen-nasync-idx6011-pro-nas-review) [NASCompares(S7)](https://nascompares.com/2026/01/21/ugreen-idx6011-pro-ai-nas-review/) [Notebookcheck(S7)](https://www.notebookcheck.net/Ugreen-iDX6011-Pro-review-NAS-power-with-desktop-hardware-and-AI-features.1253511.0.html) [techtest.org(S7)](https://techtest.org/ugreen-ugos-pro-2026-im-update-check-verschluesselung-ki-und-neue-funktionen-im-ueberblick/) [Blop77/UGREEN 참고작(S8)](https://github.com/Blop77/UGREEN)

01

### 전제 정리 · Uliya Skill이 할 수 있는 것 / 없는 것
1차 자료 직접 확인

#### Skill의 정체 S1 · S2-a · S2-b · S4

- **Markdown 지시문 패키지**. 루트에 `SKILL.md`(필수) + `references/*.md`(선택, SKILL.md에서 직접 링크)만 허용. 그 외(README.md 포함·심볼릭 링크·스크립트·매니페스트)는 `RESOURCE_UNSUPPORTED` error → README는 `references/README.md`로 넣는다(S8도 동일).
- 실행 주체는 NAS 안의 Uliya 메인 에이전트(로컬 LLM). 본문은 `delegate --target {agent} --instruction '{task}'` 한 줄 명령만. 부모가 `cli.invoke` 직접 호출 시 `RUNTIME_DIRECT_CLI_INVOKE` error.
- 자식 expert agent가 실제 CLI/Action을 고르고 실행. 부모는 사적 파라미터(파일 ID 등)를 미리 수집하지 않는다.
- 위임 결과 5상태 `completed / failed / cancelled / waiting_user / waiting_approval` 모두 다뤄야 함(누락 시 `DELEGATION_RESULT_HANDLING_MISSING`).
- 제한: ZIP ≤10 MB, 파일당 ≤1 MB, ≤100 파일, SKILL.md 500행 초과 시 warning.
- Round 1: 실기기 불필요, 설치 가능하지 않아도 됨. Round 2: 배정된 iDX6011 Pro(64 GB)에서 **실제 동작** + 영상에 실행 장면 필수.

#### Skill이 할 수 없는 것 카탈로그 부재 = 미지원

- 외부 네트워크 호출, 이메일·푸시·메신저 발송, 공유 링크 생성, Docker·백업·사용자/권한·시스템 설정·저장소 상태 조회(용량은 `find --min-size`·`stat`로 간접 계산만).
- 스크립트·바이너리·런타임 코드 블록(bash/python/js 펜스 → `SECURITY_SCRIPT_EXECUTION_UNSUPPORTED`).
- 스케줄 실행·상주 불가(S3 5.4) → "매주 자동"이 아니라 "매주 한 번 말해 달라"로 설계.
- 영상 파일 전사: `audio-transcription`이 비디오를 받는지 **확인 필요**.
- 앨범 캡션 쓰기 없음 → 캡션은 `save-text` 문서로. 사진 EXIF 쓰기 없음(`chtimes`만).
- 인물(`figure-name`) 검색은 얼굴 인덱싱·이름 지정 선행 필요 → Round 2 당일 업로드분은 지연 가능, **경로 기반(`find`·`vision-ocr --path`)이 안전**.
- 감시 카메라: 테스트 NAS에 카메라가 없을 가능성 큼 → 검증 불가 리스크.

   `````````````````````````````````````` `````````````````````````````` `````````````` ````````````````**``**`` ```````````` ``````````````````````**````**`````````````` ```````````` ```````` ``````````````````

| agent (delegate target 6개뿐) | CLI | 주요 Action (effect / approval) |
|---|---|---|
| file-agent | ug-filesystem | ls, find(path·pattern·type=image/video/audio/documents·min/max-size·date-type·start/end-timestamp·max-depth·limit), stat, getfattr, cat, category, md5sum, sha256sum (read/none) · mkdir, touch, echo(overwrite/append/patch), rename, cpmv(move/copy), del, restore(휴지통 복원), chtimes, share-mkdir (state-change/gateway) |
| file-agent | ug-filemgr | mediainfo, scan-dedupe(path+, scope), tag-list, tag-get, tag-get-by-name, tag-get-file, tag-list-file, tag-filter(tag-id+, path+, recursive) (read/none) · tag-add, tag-set, tag-delete(gateway) · tag-add-file, tag-delete-file(conditional) |
| file-agent | file-workflow | get-user-dir(사용자 홈 실제 경로) · start(kind=organize/deduplication, by=type/btime/mtime/size/image_resolution, keep-by) → run(id) (workflow) · batch-move(renameBy=date-prefix 등) · batch-del (workflow) |
| document-agent | ug-document | page-count, metadata, qa(intent=qa/summary/outline/comparison/period/extraction/locate_content, answer-mode=table/list), extract(schema=invoice/contract/expense/receipt/medical-report/purchase_order/mixed_reconciliation, max-files≤500), reconcile (read/none) · translate(file 또는 --content 문자열, target-lang) · writing(task=outline/polish/rewrite/expand/compress/draft/minutes) (mixed/gateway) |
| knowledge-agent | ug-knowledge | answer-official(UGREEN 공식 문서 QA), audio-transcription(path+, language, speak-count → transcriptText·segments·quality·warnings), collect-evidence(query, path+, extension+) (read/none) · save-text(path, content 또는 content-ref, filename-hint → verified·outputFile) (workflow) |
| photo-agent | ug-photo | albums, album-detail, figure-albums, object-albums, search-picture(figure/pet·album·dir·location·ai-object·ocr-contains·file-name-contains·start/end-time·camera/lens/focal/iso·file-type), search-screen, search-classify, search-hint, meta(EXIF), vision-ocr(path), vision-vlm(path, prompt, max-tokens), health (read/none) · create-album(album-name, add-item+, query), create-album-condition, create-album-anniversary, create-album-baby, create-album-custom, timeline (workflow) |
| media-agent | ug-video | search(query/actor/style/favorites/recent/watch-status), control(pause/continue/next/previous), subtitle-search · subtitle-download(gateway) |
| media-agent | ug-music | search(song/singer/album/genre/year/songlist/random, start/end-year, play) · control(volume/seek/speed/playback-mode/stop-timer) |
| security-monitor-agent | ug-surveillance | cameras, event-timeline(Human/HumanFace/Vehicle/Pet/Package, known/stranger, 기간), identity-resolve, event-evidence, faces, face-detail, vehicle-plates (모두 read/none) |

카탈로그(catalogVersion 2.0.0, 2026-09-01, 9 CLI · 6 agent · 약 80 action)의 permissions / prerequisites / errorCodes / stability는 전부 `"unknown"` → 반환 필드·에러 코드 미공개. Skill 본문은 특정 JSON 필드명 대신 "실제 반환 결과"로 서술한다.

정적 검사기(check-lib.mjs)가 실제로 잡는 것 — 작성 함정 17개

    ```````` ```` ```` `````` ``````    ```` ```````` `` ```` `````````````` ````````````  ``````````

| 규칙 | 심각도 | 실무 함정 |
|---|---|---|
| 루트에 SKILL.md, references/ 외 항목 | error | README.md를 루트에 두면 탈락급 |
| frontmatter는 name, description 한 줄씩만 | error | version:, author: 넣지 말 것 |
| name = ^[a-z0-9]+(?:-[a-z0-9]+)*$, 디렉터리명과 동일 | error | ZIP 안 폴더명 = name |
| description ≤1,024자; when/use when 없으면, 명령형·실행 세부면 | warning | "… Use when a parent says …" 형태 |
| # Generation-time capability evidence 아래 - `ug-xxx` → `agent` | error | ASCII -> 인식 안 됨. agent 매핑 불일치도 error |
| delegate: 한 줄, --target --instruction 각 1회, 작은따옴표, 파이프/리다이렉트 금지 | error | 안쪽 작은따옴표는 '\'' |
| delegate target 6개 외 | error |  |
| 본문에 5개 상태 토큰 전부 | error |  |
| 조회형인데 "no results / empty result" 없음 | warning | 빈 결과 처리 문장 필수 |
| <…> 꺾쇠 자리표시자, "that folder" 식 지칭 | warning | {value} 중괄호 표기 사용 |
| /nas, /mnt, /volume1, /share(s)가 delegate 줄 밖에 | error | 예시 경로는 "Photos/PhoneBackup" 상대 표기 |
| /home/{실제사용자} 하드코딩 | warning |  |
| 단어 curl, wget | error | 본문·references 전부 |
| cat , cp , mv , rm , open(, fs., readFile | error | "a cat sat"도 걸림 → 반려동물 예시는 dog로 |
| request-id, expert-id, correlation-id, ug-ai, HERMES, Host CLI | error | 내부 식별자 언급 금지 |
| "bypass/skip/ignore … approval/permission/audit" | error | "승인을 기다린다"로만 |
| TODO, TBD, replace-with- · references 미링크(warning) · password = "…", PEM 키(error) | error | [..](references/x.md) 직접 링크 |

1차 자료 목록 (S1–S8)

   [](https://ai.ugreen.com/pages/hackathon-starter-kit) [](https://cdn.shopify.com/s/files/1/0630/9416/1602/files/uliya-skill-kit-0.7.3-en.zip?v=1790578898) `` ```` `` `` [](https://api.ugnas.com/api/system/v1/ua/agreement/page?agreementCode=skillhub-publish-audit-spec&acceptLanguage=en-US) [](https://ugreenhackathon.devpost.com/) [](https://support.ugnas.com/detail/article/en-US/222) [](https://support.ugnas.com/detail/article/en-US/322)  [](https://github.com/Blop77/UGREEN)

| # | 자료 | 비고 |
|---|---|---|
| S1 | Hackathon Starter Kit | curl/WebFetch 429 → Chrome으로 본문 확보 |
| S2 | uliya-skill-kit-0.7.3-en.zip (37,575 B) | 스크립트는 실행하지 않고 읽기만 |
| S2-a | docs/skill-development-standard.md | 4단계 워크플로, "catalog에 없는 능력은 미지원" |
| S2-b | references/skill-format.md, SKILL.template.md | SKILL.md 필수 섹션 |
| S2-c | data/capability-catalog.json | 9 CLI · 6 agent · 약 80 action |
| S2-d | scripts/check-lib.mjs | 진단 코드·정규식으로 "실제로 막는 것" 확정 |
| S3 | SkillHub Content Submission and Publication Standards | 사칭·과장·상주 금지 |
| S4 | Devpost 공식·규정 | 제출물·심사 기준 |
| S5 | UGREEN Photos 지원 문서 | 얼굴/중복/장면/반려동물/문자 인식, 모바일 백업 (UGOS Pro 1.6.1) |
| S6 | Custom Learning | 오프라인 자가 학습 분류 |
| S7 | iDX6011 Pro 리뷰 4건(헤더 출처 참조) | Uliya = 로컬 Qwen3 계열, 32k 컨텍스트 |
| S8 | Blop77/UGREEN "lecture-revision-kit" | 형식 관례 확인용, 내용 재사용 금지 |

02

### 선정안

Selected · Skill name

fridge-door 냉장고 문 비서

Fridge Door turns the school notices and kids' drawings piling up in your phone backup into a weekly parent to-do list and per-child artwork albums — read, sorted and saved entirely on your UGREEN NAS.

폰 백업 폴더에 쌓인 가정통신문·아이 그림 사진을 NAS 안에서 읽어, 이번 주 부모 할 일 목록과 아이별 작품 앨범으로 바꿔 준다.

**해결 문제** — 종이 통신문·알림장·안내문은 "찍어 두고 잊는" 데이터다. 마감(회신서, 현장학습비, 준비물)이 사진 더미 속에 묻히고, 아이 그림은 수백 장이 되면 누구 것인지·언제 것인지 찾을 수 없다. 기존 해법(Artkive, Keepy, 구글 포토)은 클라우드 업로드·구독이 필요하고, 통신문→할 일 변환은 아무도 안 한다.

**이름 결정** — 대안 `fridge-door-keeper`(의미 명확), `school-paper-keeper`(직설적). 결론은 `fridge-door`: 짧고, "냉장고 문에 붙이던 것들"이라는 은유가 설명 없이 전달되며 241명 중 눈에 띈다. 소문자-하이픈·디렉터리명 동일 규칙 충족.

- **타겟 유저**: 유치원·초등 자녀 1~3명 가정. (1) 통신문을 사진으로 찍어 두는 맞벌이 부모 (2) 현지어 통신문을 읽기 어려운 다문화·주재원 가정 (3) UGREEN Photos 모바일 자동 백업 사용자
- **핵심 가치**: 폴더+기간 → 마감 정렬 체크리스트 1파일 + 앨범 N개. 원본 무변경, 데이터는 NAS 밖으로 안 나감
- **트랙**: Bring Memories to Life(주). Automate Your Workflow도 가능하나 경쟁작(중복 정리·계약서류)과 거리를 둔다
- **노리는 상**: Grand Prize $20,000 Most Creative $5,000
- **사용 agent**: file-agent · photo-agent · document-agent · knowledge-agent (4개 오케스트레이션)
- **쓰기 작업**: 앨범 생성 · 다이제스트 1파일 저장 · `fridge-door-done` 태그 — 모두 확인 후

03

### 승리 근거 · 심사 기준 대응
4개 기준 동일 가중 · R1 상위 30 → R2 점수로 최종

User Value동일 가중

명확한 입력(폴더+기간) → 명확한 출력(마감 정렬 체크리스트 1개 파일 + 앨범 N개) → 측정 가능("이번 주 마감 5건, 지난 것 1건"). 매주 반복 사용, 태그로 처리 완료 추적.

Innovation & Differentiation동일 가중

(1) 사진을 "할 일"로 변환하는 워크플로(앨범 정리가 아니라 행동 산출물) (2) 그림 속 아이 이름 OCR로 아이별 자동 분류 (3) 외국인 부모용 통신문 번역 `translate --content` (4) 실행 이력을 NAS 태그(`tag-add-file`)로 남겨 재실행 시 신규분만 처리 — 스타터 예시 5종 어디에도 없는 조합.

Technical Quality동일 가중

photo/file/document/knowledge 4개 expert 오케스트레이션, 5개 상태·빈 결과·부분 결과·승인 대기 명시, 원본 무변경(이동·삭제 없음), 쓰기는 앨범 생성·문서 저장 두 가지뿐이고 모두 확인 후. 폴백(경로 기반 ↔ 인물 기반) 설계.

AI NAS Fit & Validation동일 가중

폰 자동 백업으로 **이미 NAS에 있는** 사진이 입력. OCR·VLM·번역이 전부 NAS 로컬 모델에서 수행(아이 얼굴·학교명·주소가 외부로 안 나감). 결과물도 NAS 앨범·파일로 남아 Photos 앱에서 바로 보임 — "NAS여야만 하는 이유".

04

### 아이디어 회의 기록
22개 발산 → 3개 심층 → 1개 선정

#### #1 fridge-door 선정 · 34/35

통신문 → 부모 할 일 다이제스트 + 아이별 작품 앨범

**타깃** 초등·유치원 부모(+다문화·주재원). **능력** `find` → `vision-ocr`/`vision-vlm`(path) → `create-album` → `save-text`, `translate --content`, 태그. **모두 인덱싱 불필요장점** 매주 반복되는 실제 마감 관리("놓친 회신서 0"), 아이 그림·체크리스트의 감정 호소력, 문제·해결·NAS 이유가 한 문단. 유사물(Artkive 등)은 클라우드·유료

**리스크** 낮음 사진 폴더 업로드 즉시 OCR 가능

#### #19 trip-report 28/35

여행 사진 앨범+이야기 + 영수증 지출 표 "여행 보고서"

**능력** `search-picture --location/time`(위치 인덱싱 필요), `extract receipt`, `create-album`, `save-text`

**장점** 풍경 사진으로 영상이 화려

**치명적 리스크** 중 인덱싱 지연 시 앨범 조건 실패. 사용 빈도 연 2~3회, "왜 NAS여야 하나" 약함, 스타터 예시 "여행 앨범" 확장판

→ 선정안 Stretch "학기 말 작품 연감"으로 흡수

#### #17 screenshot-inbox-zero 27/35

스크린샷 OCR 분류·태그·이동, 실행 항목 추출

**능력** `search-screen --category screen`(분류 인덱싱 필요; 폴백 `find --pattern "Screenshot*"`), `vision-ocr`, tag/`cpmv`

**장점** 스마트폰 헤비유저 전원이 대상

**치명적 리스크** 중 폰 갤러리(삼성·iOS)가 이미 자동 분류, 영상이 지루함

→ 탈락

전체 발산 목록 (22개)

   ```````````` ```````` `````````` ```` ```````` ```````` `````` `````` `````````` `````` ```` ```` `````` ```` `` `````` ```````` `````` `````````` `````` ```` ````````

| # | 아이디어 | 한 줄 | 사용 agent / Action | 메모 |
|---|---|---|---|---|
| 1 | fridge-door 냉장고 문 비서 | 가정통신문·아이 그림 사진을 OCR/VLM으로 읽어 부모 할 일 다이제스트와 아이별 작품 앨범으로 | photo vision-ocr·vision-vlm·create-album; file find·tag; document translate --content; knowledge save-text | 가정·육아·다문화. 인덱싱 불필요(경로 기반) |
| 2 | baby-month-book 월령 성장책 | 아기 사진 월별 묶음 + VLM 캡션 "이달의 순간" | photo search-picture·create-album-baby·vision-vlm; knowledge save-text | Baby 앨범 기본 기능과 겹침 |
| 3 | receipt-ledger 영수증 가계부 | 영수증 OCR/extract로 월별 지출 장부, 원본 태깅·아카이브 | photo vision-ocr; document extract receipt/expense; file tag-add-file·cpmv; knowledge save-text | 소호. 스타터 예시와 인접 |
| 4 | contract-expiry-radar | 계약서 기간 추출, 60일 내 만기 목록·태그 | document extract contract; file find·tag | 스타터 예시와 거의 동일 |
| 5 | storage-diet 저장공간 다이어트 | 대용량·중복·저화질 영상 후보 "비워도 되는 N GB", 확인 후 일괄 삭제 | file find --min-size·scan-dedupe·mediainfo·batch-del | 보편 니즈. 자체 중복 정리와 겹침 |
| 6 | shoot-cull 촬영 선별 | EXIF+VLM으로 1차 셀렉, "Selects" 앨범 | photo search-picture --camera-model·meta·vision-vlm·create-album | 로컬 VLM 품질 신뢰 리스크 |
| 7 | paper-finder 서류 찾기 집사 | "작년 전세계약서 어디 있지?" 문서·사진 OCR 횡단 검색 | knowledge collect-evidence; photo search-picture --ocr-contains; document qa | Universal Search와 겹침 |
| 8 | meeting-actions | 녹음 → 화자 분리 전사 → 액션아이템 표 | knowledge audio-transcription·save-text; document writing minutes | 스타터 예시 그대로 |
| 9 | warranty-vault 보증서 금고 | 영수증·명판·설명서에서 보증 만료일 → 가전 대장 | photo vision-ocr·create-album; document extract·qa; knowledge save-text | 참신. 테스트 데이터 부담 |
| 10 | subtitle-sweep | 자막 없는 영상 찾아 검색·다운로드 | media search·subtitle-search·subtitle-download | 스타터 예시. 인터넷·인덱싱 의존 |
| 11 | memory-playlist | 여행 사진 연도·장소로 그 시절 음악 재생 | photo search-picture; music search --start-year | 재미 위주, 효용 낮음 |
| 12 | porch-digest 현관 이벤트 일지 | 택배·방문자 이벤트·스냅샷 하루 일지 | security-monitor event-timeline --topic Package·event-evidence | 테스트 NAS 카메라 부재 → 검증 불가 |
| 13 | pet-diary | 반려동물 사진 VLM 캡션 + 월간 일기 | photo search-picture --pet-name·vision-vlm; knowledge save-text | 효용 약함. 단어 'cat' 검사기 함정 |
| 14 | notice-translator | 폴더 서류를 지정 언어로 번역 저장 | document translate; file find | 단일 능력. #1에 흡수 |
| 15 | downloads-triage | 다운로드 폴더 유형별 정리+중복 제거 | file-workflow start/run | 스타터 예시 그대로 |
| 16 | backup-integrity-audit | 원본·백업 해시 비교 누락·손상 리포트 | file find·sha256sum·stat | AI 요소 약함, 영상 임팩트 낮음 |
| 17 | screenshot-inbox-zero | 스크린샷 OCR 분류·태그·이동, 실행 항목 추출 | photo search-screen·vision-ocr; file tag·cpmv; knowledge save-text | 폰 갤러리 기본 기능과 겹침 |
| 18 | digital-legacy-index | 노년층·가족용 중요 서류 색인 | document metadata·qa; knowledge save-text | 민감 데이터, 범위 모호 |
| 19 | trip-report 여행 결산 | 여행 앨범+이야기, 영수증 지출 표 | photo search-picture --location/time·vision-vlm·create-album; document extract receipt; knowledge save-text | 데모 화려. 여행 앨범 예시+α |
| 20 | recipe-digitizer | 손글씨 레시피 OCR → 구조화 문서 | photo vision-ocr; document writing; knowledge save-text | 니치 |
| 21 | invoice-bank-reconcile | 프리랜서 송장과 입금내역 대사 | document extract mixed_reconciliation·reconcile | 스타터 예시 인접 |
| 22 | best-shot-keeper | 중복 사진 중 최선 1장만 남김 | file scan-dedupe; photo meta·vision-vlm; file-workflow batch-del | 삭제 중심 → 승인·리스크 큼 |

평가 매트릭스 (1~5점, 합계 /35)

기준: (a) Uliya 표준·제약 안에서 실제 동작 가능 [×2] · (b) 심사 4기준 적합도 · (c) 1인·21일·실기기 없이 설계 현실성 · (d) 차별화(UGREEN 기본·스타터 예시와 거리) · (e) 500단어 제안서 설득력 · (f) Round 2 3분 영상 임팩트

   

| # | 아이디어 | a(×2) | b | c | d | e | f | 합계 |
|---|---|---|---|---|---|---|---|---|
| 1 | fridge-door | 5 (10) | 5 | 4 | 5 | 5 | 5 | 34 |
| 19 | trip-report | 4 (8) | 4 | 4 | 3 | 4 | 5 | 28 |
| 17 | screenshot-inbox-zero | 4 (8) | 4 | 4 | 3 | 4 | 4 | 27 |
| 9 | warranty-vault | 4 (8) | 4 | 3 | 4 | 4 | 3 | 26 |
| 16 | backup-integrity-audit | 5 (10) | 3 | 5 | 4 | 3 | 1 | 26 |
| 6 | shoot-cull | 3 (6) | 4 | 3 | 4 | 4 | 4 | 25 |
| 5 | storage-diet | 5 (10) | 3 | 4 | 2 | 3 | 2 | 24 |
| 3 | receipt-ledger | 4 (8) | 3 | 4 | 2 | 3 | 3 | 23 |
| 14 | notice-translator | 5 (10) | 2 | 5 | 2 | 2 | 2 | 23 |
| 8 | meeting-actions | 5 (10) | 3 | 4 | 1 | 2 | 2 | 22 |
| 4 | contract-expiry-radar | 5 (10) | 3 | 4 | 1 | 2 | 2 | 22 |
| 20 | recipe-digitizer | 4 (8) | 2 | 4 | 3 | 2 | 3 | 22 |
| 2 | baby-month-book | 3 (6) | 3 | 3 | 2 | 3 | 4 | 21 |
| 13 | pet-diary | 3 (6) | 3 | 4 | 2 | 3 | 3 | 21 |
| 15 | downloads-triage | 5 (10) | 2 | 5 | 1 | 1 | 1 | 20 |
| 11 | memory-playlist | 3 (6) | 2 | 3 | 3 | 2 | 3 | 19 |
| 7 | paper-finder | 4 (8) | 2 | 3 | 1 | 2 | 2 | 18 |
| 21 | invoice-bank-reconcile | 4 (8) | 3 | 3 | 1 | 2 | 1 | 18 |
| 22 | best-shot-keeper | 3 (6) | 2 | 3 | 2 | 2 | 3 | 18 |
| 10 | subtitle-sweep | 3 (6) | 2 | 4 | 1 | 2 | 2 | 17 |
| 12 | porch-digest | 1 (2) | 3 | 2 | 3 | 3 | 3 | 16 |
| 18 | digital-legacy-index | 3 (6) | 2 | 2 | 3 | 2 | 1 | 16 |

- (a) 1점: #12는 테스트 NAS에 카메라가 없을 가능성. 3점: 인물 인식·VLM 품질·미디어 인덱싱 의존(#2, #6, #10, #13, #22). 5점: 경로 기반 `find` + `vision-ocr/vlm`(path 직접 지정)처럼 **인덱싱 선행 없이** 도는 안.
- (d) 1점: Starter Kit §5 다섯 예시(중복 정리, 여행 앨범, 회의록, 계약·송장, 차고 이벤트)와 사실상 동일. UGREEN Photos는 Baby/Pet/Face/중복 앨범을 이미 제공(S5).

상위 3개 심층 비교표

          

| 항목 | #1 fridge-door | #19 trip-report | #17 screenshot-inbox-zero |
|---|---|---|---|
| 타깃 | 초등·유치원 자녀 둔 부모(+다문화·주재원) | 여행 다녀온 가족·커플 | 스마트폰 헤비유저 전원 |
| 핵심 문제 | 통신문·알림장은 사진으로만 쌓이고 마감(회신서·준비물·현장학습비)을 놓침; 아이 그림은 버리지도 찾지도 못함 | 사진은 흩어지고 지출은 기억 안 남 | 스크린샷 수천 장이 갤러리를 덮음 |
| Round 2 당일 리스크 | 낮음 | 중(위치·시간 인덱싱 지연) | 중(분류 인덱싱 지연 → 파일명 폴백) |
| 차별화 | 통신문→할 일 + 이름 OCR 작품 분류 + 번역 | 여행 앨범 예시 확장판 | 폰 갤러리가 이미 자동 분류 |
| User Value | 매주 반복, 측정 가능("놓친 회신서 0") | 가끔(연 2~3회) | 중간 |
| 영상 임팩트 | 아이 그림·통신문→체크리스트, 감정 호소력 | 풍경 사진으로 화려 | 지루함 |
| 500단어 설득력 | 문제·해결·NAS 이유(아이 데이터는 로컬에)가 한 문단 | "왜 NAS여야 하나" 약함 | 보통 |
| 결론 | 선정 | Stretch "학기 말 작품 연감"으로 흡수 | 탈락 |

05

### 기능 리스트
태그 = 호출 agent·CLI · LLM 판단 · 난도

#### MVP R1에 완전 기술 · R2 당일 검증 · 10개

- **M1 입력 수집**`{source_folder}`(폰 백업 폴더), `{period}`(기본 최근 7일), `{children}`(선택), `{parent_language}`(선택), `{output_folder}`(기본 `{source_folder}/Fridge Door`)LLM: 기본값 제안, 누락 시 질문(`waiting_user`)
—난도 하

- **M2 사진 인벤토리**기간 내 이미지 목록(경로·크기·수정시각), 최대 12장LLM: 12장 초과 시 기간 축소 요청
file-agentug-filesystem find --type image --start/end-timestamp --max-depth 2 --limit난도 하

- **M3 처리 이력 제외**태그 `fridge-door-done` 붙은 파일 제외LLM: 신규분만 남김, 전부 처리됨이면 "새 항목 없음" 종료
file-agentug-filemgr tag-get-by-name → tag-filter난도 중

- **M4 OCR**각 사진의 글자 읽기LLM: 통신문 후보 / 글자 거의 없음(그림 후보) / 무관(영수증 등) 1차 분류
photo-agentug-photo vision-ocr --path난도 하

- **M5 통신문 구조화**제목·기관(학교·반)·날짜·마감·할 일 유형(회신서·준비물·납부·행사)·금액·대상 아이LLM: 원문 날짜 인용 + 해석값, 불확실하면 "확인 필요", 오늘 이전 마감은 "지남"
LLM 자체 추론document-agent ug-document writing --task compress (긴 텍스트)난도 중

- **M6 작품 판별·캡션**글자 없는 사진을 VLM으로 확인: `--prompt 'Is this a child'\''s drawing or craft? Answer YES or NO, then one sentence describing subject and colours.'`LLM: NO면 "무관". 그림 속 이름(OCR)과 `{children}` 매칭
photo-agentug-photo vision-vlm --path --prompt난도 중

- **M7 앨범 생성(확인 후)**"School notices {YYYY-MM}" 1개, "Artwork – {child} {YYYY}" 아이별LLM: 동명 앨범 존재 시 추가 여부 질문(`albums --keyword` 선조회)
photo-agentug-photo create-album --album-name --add-itemwaiting_approval난도 중

- **M8 다이제스트 저장(확인 후)**`Fridge Door – {period}.md`LLM: 섹션 순서 고정(목업 S3)
knowledge-agentug-knowledge save-text --path --filename-hint --content난도 하

- **M9 처리 완료 태그(확인 후)**저장·앨범이 `completed`인 파일에만
file-agentug-filemgr tag-add → tag-add-file (conditional)난도 중

- **M10 결과 보고·상태 처리**5개 상태, 빈 결과, 부분 결과, 읽을 수 없는 사진 목록LLM: "저장했다"는 `completed` 반환 후에만
—난도 하

#### Should R1 기술 · R2 여유 시 검증 · 4개

- **S1 통신문 번역**`{parent_language}`가 원문과 다르면 각 요약을 번역해 병기LLM: 요약문만 번역(원문 전체는 토큰 낭비)
document-agentug-document translate --content --target-langgateway난도 중

- **S2 지난 통신문 아카이브**마감 지난 사진을 `{source_folder}/Fridge Door/Archive {YYYY-MM}`로 이동(확인 후)LLM: 기본 OFF, 명시적으로 원할 때만
file-agentug-filesystem mkdir → cpmv --type movegateway난도 중

- **S3 아이 식별 폴백**이름 OCR 실패 시 인물 앨범으로 보강LLM: 인덱싱 미완이면 선택 질문
photo-agentfigure-albums --show-name named → search-picture --figure-name난도 중

- **S4 주간 비교**이전 다이제스트를 읽어 "지난주 미완료 이월"LLM: `[x]` 항목은 완료로 간주
file-agentfind --pattern "Fridge Door*" → cat난도 상

#### Stretch 영상 마지막 15초·로드맵 · 3개

- **X1 학기 말 "작품 연감"**아이별 작품 앨범 + VLM 캡션 모음 문서 + 기념일 앨범
photo create-album-anniversaryknowledge save-text난도 중

- **X2 통신문 Q&A**"이번 달 현장학습비 얼마였지?" → 저장된 다이제스트에 질의
knowledge collect-evidence --pathdocument qa --intent period난도 중

- **X3 음성 알림장**선생님 음성 메시지 파일도 입력에 포함
knowledge audio-transcription난도 중

06

### 유저 플로우
사용자 발화 → Skill 처리 → 결과

플로우 A · 주간 다이제스트(코어) — KO "냉장고 문, 이번 주 학교 통신문 정리해 줘." / EN "Fridge Door, sort out this week's school papers."

1. **입력 확인**트리거 "school notices / kids' drawings / fridge door". "폴더 `Photos/PhoneBackup`, 최근 7일(10/19~10/25), 아이 Mina·Jun, 저장 `…/Fridge Door`로 진행할까요?" → "응"→ waiting_user
1. **file-agent find**기간 내 이미지 목록 → 9장ug-filesystem
1. **file-agent tag-filter**`fridge-door-done` 2장 제외 → 7장ug-filemgr
1. **photo-agent vision-ocr ×7**글자 많음 4(통신문) · 거의 없음 2 · 조금 1(영수증)ug-photo
1. **LLM 구조화**마감 3(11/01 회신서, 10/31 현장학습비 12,000원, 11/04 준비물 '줄넘기') + 행사 1(11/07 학예회 14:00). 영수증 → 무관
1. **photo-agent vision-vlm ×2**"YES. A crayon drawing of a yellow school bus under a rainbow." / "YES. A paper-cup robot craft, silver and red." OCR '김민아' → Mina
1. **미리보기 확인**"앨범 2개 만들고 파일 1개 저장할까요?" → "응"→ 화면 S1 · waiting_user
1. **create-album ×2**"School notices 2026-10"(4) · "Artwork – Mina 2026"(2), 플랫폼 승인 → completed, UUIDwaiting_approval → 화면 S4
1. **knowledge-agent save-text**completed, 저장 경로 반환→ 화면 S3
1. **file-agent tag-add-file ×6**영수증 제외 6장 태그 → completed
1. **결과 보고**"마감 3건(가장 빠른 것 10/31 현장학습비), 행사 1건, 작품 2점(Mina). 영수증 1장은 건드리지 않았어요."→ 화면 S2

플로우 B · 외국인 부모 번역(Should S1) — EN "Fridge Door, read the notices from my daughter's school this week and tell me in English what I need to do." / KO "딸 학교에서 온 이번 주 통신문 읽고 내가 뭘 해야 하는지 영어로 알려 줘."

1. **입력 확인**기간·폴더 확인, `{parent_language}=English` 자동(요청 언어)
1. **find → tag-filter → vision-ocr**국문 통신문 3장
1. **구조화 + translate ×3**국문 원문 인용 유지 → `translate --content '{notice_summary}' --target-lang en`document-agent · waiting_approval 가능
1. **미리보기**통신문마다 [원문 핵심 1줄 / English summary / Due / Action]
1. **저장·앨범(A와 동일) → 보고**"3 notices. 2 require action: return the consent form by Nov 1 (Mina, Class 2-3); pay KRW 12,000 field-trip fee by Oct 31. 1 is information only (school festival Nov 7, 2 pm)."

플로우 C · 빈 결과·엣지 — KO "냉장고 문, 지난 주말 사진 정리해 줘."

1. **find 결과 0**"10/18~10/19 사이에 `Photos/PhoneBackup`에서 사진을 찾지 못했어요(no results). 다른 폴더나 기간을 알려 주세요." 비슷한 폴더로 임의 확장 안 함completed · 생성 0
1. **OCR·VLM 모두 실패(흐림)**"2장은 읽을 수 없었어요(IMG_4412.jpg, IMG_4413.jpg). '확인 필요' 섹션에 파일명만 남깁니다."확인 후 종료 또는 cancelled
1. **앨범 승인 거부**앨범 단계 cancelled, 다이제스트 저장만 진행할지 질문부분 성공

플로우 A 다이어그램 노드·엣지

**노드**: U(사용자) · P(Uliya 부모) · F(file-agent) · PH(photo-agent) · D(document-agent) · K(knowledge-agent) · OUT1(앨범) · OUT2(다이제스트 파일)

**엣지**: U→P 요청 / P→U 입력 확인 / P→F find(기간·이미지) / F→P 목록 9 / P→F tag-filter / F→P 제외 2 / P→PH vision-ocr ×7 / PH→P 텍스트 / P→PH vision-vlm ×2 / PH→P 캡션 / P→D (선택) translate/compress / P→U 미리보기·확인 / U→P 승인 / P→PH create-album ×2 / PH→OUT1 / P→K save-text / K→OUT2 / P→F tag-add-file ×6 / P→U 결과 보고

[07 화면 목업: 아티팩트 참조]

08

### 실행 계획

#### 아키텍처 (플로우 A)
 flowchart LR U[사용자] -->|요청| P[Uliya 부모] P -->|입력 확인| U P -->|find · tag-filter · tag-add-file| F[file-agent] P -->|vision-ocr ×7 · vision-vlm ×2 · create-album ×2| PH[photo-agent] P -.->|선택: translate / compress| D[document-agent] P -->|save-text| K[knowledge-agent] PH --> OUT1[(앨범)] K --> OUT2[(다이제스트 .md)]

부모는 `delegate`만 쓰고, 각 단계는 직전 단계의 실제 결과(upstream)만 사용. 원본은 읽기 전용.

#### 일정 (2026-10-26 → 11-16 16:45 KST, 하루 3~5시간)

10/26(일)**환경**Devpost 등록, uliya-skill-kit을 ~/.claude/skills/에 설치, "What capabilities are currently supported?" 등 확인 질문, 카탈로그 재독(ug-photo 반환 요약)

10/27**범위 확정**S1 §4 "Do not generate any files yet…" 타당성 대화, 이름 확정 → 범위 메모

10/28–10/30**SKILL.md v0.1→v0.5**매일 check-skill.mjs, 자체 {value} lint → 0 error

10/31–11/1**references 4종**digest-format 예시 완성 → 패키지 v0.7

11/2–11/4**테스트 이미지 14장**통신문 8(국문 5·영문 3, 인쇄 후 촬영, 1장 지난 날짜), 그림 6(2장 이름, 1장 흐림), 영수증 1, 스크린샷 1. expert 응답 모사 드라이런

11/5–11/7**제안서**10항목 영어 → 500단어 이하 → HTML→PDF(≤1 MB), 다이어그램 SVG

11/8–11/9**사용자 관점 리뷰**지인 1명에게 README만 주고 흐름 설명 가능한지 → v0.9

11/10–11/11**Devpost 페이지**스토리·썸네일 1200×800·갤러리 2장, 라이선스/AI 도구 공개문

11/12–11/13**최종 검사**0 error 0 warning, ZIP 용량·파일 수, 단어 수 재확인

11/14(토)**제출 (마감 2일 전)**제출 후 수정 금지 항목 점검

11/15–11/16**버퍼**Round 2 테스트 계획·영상 스토리보드, OBS 설치·녹음 테스트

~11/30 23:45 PT**Round 2**테스트 당일(아래 타임박스) → 영상 업로드 → 12/1 16:45 KST 전 제출

#### 3분 영상 시나리오

0:00–0:12냉장고 문 실사진 → 폰 갤러리 스크롤 · "These used to live on the fridge door. Now they live in a phone backup — and get forgotten."

0:12–0:25UGOS 데스크톱, Uliya 창 · "Fridge Door is a Uliya Skill for UGREEN AI NAS."

0:25–0:50입력 확인 → 미리보기 카드(S1) · "I ask once a week. It finds this week's photos, reads them on the NAS, and shows me what it found before touching anything."

0:50–1:20OCR 결과 ↔ 원본 사진, 마감 pill · "Four school notices became three deadlines and one event. Every item names its source photo."

1:20–1:45그림 2장 + VLM, '김민아' 하이라이트 · "Two drawings. It read my daughter's name on one of them and filed it under her album."

1:45–2:10승인 → Photos 앨범(S4) → md 파일(S3) · "After I approve: two albums in UGREEN Photos and a one-page digest file. Nothing moved, nothing deleted."

2:10–2:30영어 번역(플로우 B) · "Parents who don't read the local language get the same list in theirs — translated on the NAS."

2:30–2:48재실행 "2 already done", 앨범 2→5 · "Next week it skips what it already handled."

2:48–3:00엔드카드: 이름·트랙·"All on your NAS"

- 당일 모든 실행 OBS 1080p 녹화(시스템 오디오 포함), 실패 장면도 보관
- 영어 더빙 + 영어 자막 동시. 가짜 결과 합성 금지, 타임랩스는 OCR 대기만
- YouTube 공개/미등록, 제목 "fridge-door — Uliya Skill for UGREEN AI NAS (Hackathon 2026)"

#### 리스크와 완화

**R1 표준·검사기 위반** (루트 README, ASCII 화살표, 꺾쇠, `/volume1`, 'cat'·`curl`, 상태 토큰 누락) → 자동 스크리닝 탈락
완화: §01 함정 목록을 체크리스트로, 매 수정마다 `node uliya-skill-kit/scripts/check-skill.mjs fridge-door`(0 error·0 warning 목표), 자체 `{value}` lint, references까지 동일 규칙

**R2 실기기 없음** → `vision-ocr`/`vision-vlm`/`create-album --add-item` 반환 형태·승인 UX·성능 미확인
완화: 필드명 대신 "실제 반환 결과"로 서술, 단계별 폴백(`find`→`search-picture --dir`; add-item 불가 시 `create-album --query` 또는 `create-album-condition --dir --start-time`), 1회 12장 상한(32k 컨텍스트), 테스트 데이터 사전 검수, 당일 타임박스

**R3 로컬 OCR/VLM의 한국어·손글씨 품질** (S7: 클라우드보다 느리고 덜 정확)
완화: 인쇄물 위주 시연(영문+국문), 손글씨는 "읽을 수 없음"으로 정직하게 분리, 날짜·금액에 원본 파일명 병기, 이름 OCR 실패 시 `waiting_user`로 아이 선택

**R4 Photos 인덱싱 지연** → 인물·장면 검색 불가
완화: MVP는 인덱싱 불필요 경로만, 인물 기반은 Stretch

#### Round 2 테스트 당일 타임박스 PT 00:00~23:59 = KST 17:00~익일 17:00

 ``

| 17:00 | 접속, Skill 설치, 테스트킷 업로드(Photos/PhoneBackup 구조 재현), 수정시각이 기간 안인지 확인 |
|---|---|
| 18:00 | 코어 1(통신문 8장) — 실패 시 폴백 표(find→search-picture --dir, add-item→create-album --query) |
| 20:00 | 코어 2(그림 6장, 아이별 앨범, 재실행 스킵) |
| 22:00 | 엣지(흐림·영수증), 승인 거부 경로, 빈 기간 |
| 23:00 | 문구 수정 → check-skill.mjs → 재설치 → 실패 케이스 재실행 |
| 익일 01:00 | 촬영(S6) |
| 03:00~ | 재촬영·증거 백업(로그·녹화·결과 파일). 당일 종료 후 데이터 복구 불가 |

#### 제출 체크리스트 · Round 1 전

- 폴더명 = `name` = `fridge-door`; frontmatter에 `name`, `description`만
- description ≤1,024자, "Use when" 포함, 명령형 아님
- `# Generation-time capability evidence` + `- `ug-x` → `agent`` 5줄(유니코드 →)
- 모든 `delegate` 한 줄·작은따옴표·target 6개 중 하나; 파이프/리다이렉트 없음
- 5개 상태 토큰 전부 본문에 존재; "no results" 문구; "real result"/"upstream" 문구
- 금지어 검색 `grep -nE "curl|wget|cat |cp |mv |rm |/nas|/volume|/mnt|/share|request-id|TODO|TBD|<[^>]{1,80}>"` 결과 0건(SKILL.md·references 전부)
- 코드 펜스에 bash/python/js 언어 태그 없음
- references 파일 전부 SKILL.md에서 `[..](references/x.md)` 직접 링크
- 루트에 README.md·.DS_Store·스크립트 없음(`zip -X`, macOS는 `__MACOSX` 제거)
- `node uliya-skill-kit/scripts/check-skill.mjs fridge-door` → 0 error(목표 0 warning)
- ZIP ≤10 MB, 파일 ≤100, 파일당 ≤1 MB
- 제안서 PDF ≤1 MB, 10항목 실질 답변 ≤500단어(자동 카운트), 제3자 구성요소·AI 도구 명시, 서명·날짜
- 개인정보 없음: 테스트 이미지의 학교명·아이 이름·전화번호는 가상
- Devpost 폼: 트랙 선택, 영어, 제출 후 Round 1 자료 삭제 금지
- S3 준수: 이름·설명이 기능과 일치, UGREEN 공식 사칭 요소 없음, 과장어("best") 없음

#### 제출 체크리스트 · Round 2 전

- 테스트킷 최종본(14장) + 기대 결과표
- OBS·마이크 점검, 영어 내레이션 대본
- 폴백 결정표 인쇄
- 영상 ≤3:00, 영어 자막, 실제 NAS 화면만, YouTube 링크 제출

09

### 제출 패키지 초안
SKILL.md · 파일 구조 · 제안서 10항목

SKILL.md 초안 (영어, 검사기 규칙 반영)

초안이다. 제출 전 반드시 `check-skill.mjs`로 0 error 확인. 본문에서 `cat`, `curl`, `/volume1`, `<…>`, `request-id` 단어를 쓰지 않았다.
 --- name: fridge-door description: A weekly parent to-do digest and per-child artwork albums built from the school notices, newsletters, permission slips and children's drawings that sit as photos in a phone backup folder on the NAS, read entirely on the device. Use when a parent says things like "sort out this week's school papers", "what do I need to send back to school", "file the kids' drawings", or "fridge door". --- # Goal Turn the photos a parent takes of school paperwork and children's artwork into two results, without moving or deleting any original photo: - One **digest file** for the chosen period: deadlines in date order, events, a short summary of each notice (optionally translated into the parent's language), captions for the artwork, and a list of photos that could not be read. - **Albums** in UGREEN Photos: one "School notices {year-month}" album and one "Artwork – {child} {year}" album per child. Supported scope: one source folder per run, up to 12 photos per run, images only. Photos that are neither school paperwork nor artwork (for example receipts) are listed and left untouched. On later runs, photos already handled are skipped. For the user guide, read [references/README.md](references/README.md). For the digest layout, read [references/digest-format.md](references/digest-format.md). For dependencies and AI tool disclosures, read [references/disclosures.md](references/disclosures.md). # Required input Collect these values before the first delegation. Use the user's exact words; do not guess. 1. `{source_folder}`: the NAS folder where the phone backs up photos. If the user does not name one, ask once and offer to list the user's top-level folders first. 2. `{period}`: a date range. Default: the last 7 days, stated back to the user as explicit dates. 3. `{children}`: child names as the parent writes them, in any language, or none. 4. `{parent_language}`: the language for summaries. Default: the language the user is speaking. 5. `{output_folder}`: where the digest is saved. Default: a subfolder named Fridge Door inside `{source_folder}`. Confirm before saving. Values filled during the run (always from real results of earlier steps): `{photo_list}`, `{new_photos}`, `{photo_path}`, `{ocr_text}`, `{caption}`, `{notice_items}`, `{artwork_items}`, `{unrelated_items}`, `{notice_summary}`, `{translated_summary}`, `{digest_text}`, `{album_name}`, `{album_paths}`, `{saved_path}`, `{tag_id}`. Before each delegation, replace every `{name}` with the real value. If a value is missing, stop the dependent step and say which value is missing. # Generation-time capability evidence - `ug-filesystem` → `file-agent` - `ug-filemgr` → `file-agent` - `ug-photo` → `photo-agent` - `ug-document` → `document-agent` - `ug-knowledge` → `knowledge-agent` # Workflow Run the steps in order. Each step uses only the real result returned by the steps before it (upstream results only). ## Step 1: List this period's photos `delegate --target file-agent --instruction 'In the folder {source_folder} and its subfolders up to depth 2, list image files whose modification time falls inside {period}. Return each file with its full path, size and modification time, newest first, at most 12 files. Only read; do not create, move, rename or delete anything. If nothing matches, say so and return an empty list.'` - Empty list (no results): tell the user no photos were found in `{source_folder}` for `{period}` and stop. Do not search other folders or widen the period on your own. - If the folder has more than 12 matching photos, say so and ask the user to narrow `{period}`. ## Step 2: Skip photos handled on earlier runs `delegate --target file-agent --instruction 'Look up the file tag named fridge-door-done. If it exists, return which of the following files carry it: {photo_list}. If the tag does not exist, say so and return an empty list. Only read; do not create or change tags.'` - Remove tagged files from the list; the rest is `{new_photos}`. If `{new_photos}` is empty, tell the user everything in this period was already handled and finish as `completed` with nothing created. ## Step 3: Read the text on each photo For each path in `{new_photos}`, one at a time: `delegate --target photo-agent --instruction 'Run OCR on the image {photo_path} and return the recognised text exactly as read, in reading order, with unclear parts marked. Do not describe the picture, do not add text that is not in the image, and do not change the photo or any album. If no text is recognised, return an empty result and say so.'` Sort by the real OCR result: - Clearly a school notice, newsletter, permission slip, fee notice or class message: add to `{notice_items}` with its `{ocr_text}`. - Little or no text: candidate artwork, go to Step 4. - Text that is clearly something else (receipt, screenshot, menu): add to `{unrelated_items}` and do nothing further with it. ## Step 4: Check candidate artwork For each candidate: `delegate --target photo-agent --instruction 'Look at the image {photo_path} and answer in two parts. First, YES if it shows a child'\''s drawing, painting or craft, otherwise NO. Second, one sentence naming the main subject and colours. Do not guess the child'\''s name or age. Do not change the photo or any album.'` - YES: add to `{artwork_items}` with the `{caption}`. If the OCR text from Step 3 contains one of `{children}`, assign that child; otherwise mark the child as unknown and ask the parent once (`waiting_user`) when showing the preview. - NO: add to `{unrelated_items}`. ## Step 5: Structure the notices From each `{ocr_text}`, build one entry: title, sender (school or class), every date with its role (due, event, payment), the action the parent must take, amount if any, and the child it concerns (match against `{children}`; otherwise all). Quote the original date text next to the interpreted date. Mark a date as needing a check when the text is unclear. Flag a due date earlier than today as past. When a notice text is longer than about 400 words, condense it first: `delegate --target document-agent --instruction 'Condense this school notice for a parent. Keep every date, deadline, amount, place, item to bring and action required, word for word. Remove greetings and boilerplate. Return plain text in the result and do not save any file. Text: {ocr_text}.'` If `{parent_language}` differs from the notice language, translate the short summary of each entry: `delegate --target document-agent --instruction 'Translate the following school notice summary into {parent_language}. Keep dates, amounts and names unchanged. Return the translation as text in the result and do not save any file. Text: {notice_summary}.'` Keep the real translation as `{translated_summary}`. If translation fails for an entry, keep the original summary and say so in the digest. ## Step 6: Preview and confirm Show one preview: notices with due dates in date order, events, artwork with captions and assigned child, unrelated photos that will be left alone, and exactly what will be created: album names with photo counts and the digest file name inside `{output_folder}`. State that nothing will be moved or deleted. Ask the user to confirm or correct. This is a `waiting_user` point. If the user declines, show the digest text in the conversation instead and finish as `cancelled` with nothing created. ## Step 7: Create albums (after confirmation) For each album to create, with `{album_name}` set to "School notices {year-month}" or "Artwork – {child} {year}": `delegate --target photo-agent --instruction 'Create an album named {album_name} containing exactly these photos: {album_paths}. If an album with this name already exists, add the photos to it instead of creating a second one, and say which happened. Do not move, copy or delete any file. Return the real album identifier and the number of photos it now holds.'` The platform may ask the user to approve. Wait for it (`waiting_approval`). If approval is denied, treat that album as `cancelled` and continue with the next step. ## Step 8: Save the digest (after confirmation) Compose `{digest_text}` following [references/digest-format.md](references/digest-format.md), using only real results, and save it: `delegate --target knowledge-agent --instruction 'Save the following Markdown text as a new file in the folder {output_folder}, creating that folder if it does not exist, using the file name hint Fridge Door – {period}. Do not overwrite an existing file; if the name is taken, add a number. Return the real saved path and whether the save was verified. Text: {digest_text}.'` Wait for approval if asked (`waiting_approval`). Report the saved path only after the expert returns `completed`. ## Step 9: Mark handled photos Only for photos that ended in a `completed` album or in the saved digest: `delegate --target file-agent --instruction 'Make sure a file tag named fridge-door-done exists, creating it if needed, then add that tag to these files: {album_paths}. Do not remove any other tag and do not change the files. Return which files were tagged.'` If tagging fails, say so; the run is still complete, but the next run may show these photos again. ## Step 10: Report Report only real results: the next due item, counts of deadlines, events and artwork per child, each album with its real identifier and photo count, the saved digest path, photos skipped as unrelated or already handled, and photos that could not be read. # Completion and failure - `completed`: use the real result in the next step. Never say an album exists or a file was saved unless the responsible expert returned `completed` with a real identifier or path. - `failed`: name the step and the file, with the expert's reason. For Steps 3 to 5, continue with the remaining photos and list the failed ones under "Needs your check". If Step 1 fails, stop. If Step 8 fails, show the digest text in the conversation so nothing is lost. - `cancelled`: stop the workflow, report what was already created, and state that nothing more will be created. - `waiting_user`: show the expert's question to the user exactly, wait, then resume the same step. - `waiting_approval`: tell the user what will change (an album, one new file, tags) and resume only after the platform reports approval. Denied approval counts as `cancelled` for that item only. Empty and partial results: an empty list from Step 1 or Step 2 ends the run honestly. If only some photos could be read, create albums and the digest from those and list the rest. Never invent dates, amounts, school names or captions; every item in the digest names its source photo file. Safety: original photos are read only and never moved, renamed or deleted. The only writes are new albums, one new digest file in the confirmed `{output_folder}`, and the fridge-door-done tag, each after the user confirms. No data leaves the NAS. The Skill never runs `cli.invoke` itself; all NAS work goes through the delegate commands above.

검사기 관점 자체 점검: frontmatter 2키 · description 약 420자, "Use when" 포함, 명령형 아님 · 증거 섹션 제목·화살표 형식 일치 · 모든 delegate 한 줄·작은따옴표·target 6개 내 · 5개 상태 토큰 · "no results"/"empty list" · "real result"/"upstream" · `cli.invoke`는 "never runs" 부정문 안에만 · 절대 경로 없음 · references 3개 직접 링크. 남는 **확인 필요**: `{...}` 중괄호를 Uliya 런타임이 치환 규칙대로 따르는지(S8도 같은 방식).

#### 패키지 파일 구조
 fridge-door/ ← 디렉터리명 = name ├── SKILL.md (위 초안, 본문 ≤ 300행 목표) └── references/ ├── README.md 사용자 가이드: 대상, 설치(Skills Hub/업로드), │ 권한(읽기: 소스 폴더 / 쓰기: 출력 폴더·앨범·태그), │ 예시 발화 6개(EN/KO), 반복 사용법, 제거 방법, 버전 이력 0.9.0 ├── digest-format.md 다이제스트 섹션 7개 고정 양식 + 예시 1부(S3 콘텐츠) ├── disclosures.md 패키지 내용, 의존 CLI/agent 표, 제3자 구성요소 "None", │ 해커톤 중 신규 개발 범위, AI 도구(Claude Code, uliya-skill-kit 0.7.3) └── test-plan.md Round 2 당일 타임박스, 코어 2·엣지 1 체크리스트, 폴백 결정표(R2)

ZIP은 `fridge-door/` 폴더 하나만, 예상 < 60 KB. 제안서 HTML/PDF·테스트 이미지·Devpost 썸네일 1200×800은 별도 폴더, ZIP 제외.

#### 제안서 10개 항목 초안 영어 · 실질 답변 ≈ 470단어

1. **What does your Skill do?** Fridge Door reads the school notices and children's drawings that sit as photos on the NAS and turns them into a weekly parent to-do digest and per-child artwork albums, entirely on the device.
1. **Target user and problem** Parents of kindergarten and primary-school children who photograph paper notices and artwork. The photos land in a phone backup folder and are forgotten: reply slips and fees are missed, and hundreds of drawings become impossible to attribute or find. Parents who do not read the local language are hit hardest.
1. **Solution** Once a week the parent asks Uliya. The Skill lists the period's photos, reads each one with on-device OCR, structures every notice into deadline, action, amount and child, checks picture-only photos with the on-device vision model and captions the artwork, then, after one confirmation, creates albums in UGREEN Photos and saves a one-page digest. Handled photos are tagged so later runs process only new ones.
1. **Main user flow** "Sort out this week's school papers" → confirm folder, period, children → inventory → OCR and vision per photo → preview of deadlines, events, artwork and what will be created → approve → albums, digest file, tags → report with the next due item and every source file name.
1. **Differentiation** Album tools organize pictures; Fridge Door turns pictures into actions with dates. It attributes artwork by reading the child's name written on it, translates notice summaries for non-native parents, and uses NAS file tags as run memory. Cloud services for kids' artwork require uploads and subscriptions; here nothing leaves the NAS.
1. **NAS features used** Step 1 `ug-filesystem find` (file-agent); Step 2 and 9 `ug-filemgr` tag lookup and tag-add-file (file-agent); Steps 3–4 `ug-photo vision-ocr`, `vision-vlm` (photo-agent); Step 5 `ug-document writing` condense and `translate --content` (document-agent); Step 7 `ug-photo create-album` (photo-agent); Step 8 `ug-knowledge save-text` (knowledge-agent).
1. **Technical approach** A Markdown orchestration Skill: the parent issues only `delegate` commands to four registered experts in fixed order and passes only real upstream results. Inputs: source folder, period, child names, language, output folder. Originals are read-only; the only writes are albums, one digest file and a tag, each after confirmation and platform approval. Models: built-in NAS OCR, vision and document models; no external services or keys. All five delegation states, empty and partial results are handled; runs are capped at 12 photos.
1. **Progress** Built: complete Skill package (SKILL.md, user guide, digest format, disclosures, test plan) passing the official static checker with zero errors; a 16-photo test kit specification with planted cases. Not built: device-tuned wording for approval prompts. Needs NAS testing: OCR quality on Korean and English print, vision answers on drawings, album creation from file paths, save-text naming.
1. **Finalist test plan** Core 1: eight notices yield a digest with six deadlines in date order, one flagged as past, plus two events, each citing its photo. Core 2: six drawings become two per-child albums, one child assigned from the name read on the drawing, and a second run skips all thirteen handled photos. Edge: a blurred photo and a receipt in the same folder are reported as unreadable and unrelated, nothing is invented, nothing is created before confirmation.
1. **Limits, risks, dependencies** Images only; handwritten notices and poor light reduce OCR quality and are reported, not guessed. Twelve photos per run. Child attribution needs the name on the artwork or the parent's answer. Depends entirely on built-in NAS experts; translation quality follows the on-device model.

(단어 수 제외) Team: individual. Third-party components: none. AI tools: Claude Code for drafting and static checks; UGOS Skill Creation Tool 0.7.3 for capability checks.

## 다이제스트 레이아웃 결정 (2026-10-31)

기획 아티팩트의 다이제스트 목업과 달리 `references/digest-format.md`는 맨 위에 "At a glance"(다음 마감, 건수, 처리 범위)를 추가하고, 아티팩트의 별도 "Not processed" 섹션을 "Left untouched and run details"에 합쳤다. 이유: 부모가 파일을 열자마자 10초 안에 다음 할 일을 보게 하고, 관련 없음·읽기 실패·이미 처리됨·실행 정보를 한 곳에 모아 섹션 수를 줄이기 위해서다. 아티팩트 S3 목업은 구성만 근사이며 실제 파일은 digest-format.md를 따른다.
