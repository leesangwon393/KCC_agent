# 에이전트 로컬 API (웹 연결용)

맥에서 도는 에이전트(`prototype/demo_v5.py`)가 여는 HTTP API입니다. 지금 화면(`demo_v5.html`)도 이 API만 씁니다. 웹(`web/`)이나 Django API는 이 API를 호출하거나, 같은 데이터를 받아 가면 됩니다.

- 주소: `http://127.0.0.1:<port>`. 맥 안에서만 열립니다. 외부에서 직접 접근할 수 없습니다.
- 인증: 없습니다. 같은 맥의 프로그램만 부를 수 있다는 것이 전제입니다.
- 브라우저에서 부르기: 다른 주소의 웹 페이지가 부르려면 `--allow-origin <origin>`으로 허용해야 합니다. 예: `--allow-origin http://localhost:3000`. 허용하지 않은 origin은 preflight가 403입니다.
- POST는 `Content-Type: application/json`만 받습니다. 다른 사이트가 폼 전송으로 파일 이동을 위조하지 못하게 하기 위해서입니다.

## 실행

```sh
python prototype/demo_v5.py --root <작업폴더> --projects <projects.json> --watch \
  --strict-auto-inbox ~/Downloads --strict-auto-inbox ~/Desktop \
  --auto-inbox "~/Library/Mobile Documents/com~apple~CloudDocs/KCC-inbox" \
  --source-rules <source_rules.json> --qwen <Qwen3-1.7B> --adapter <LoRA> \
  --digest-hours 5 --expire-installers-days 3 --port 8791 [--allow-origin <origin>]
```

`projects.json` 형식은 `{"<project_id>": {"name": "...", "folder": "~/Desktop/...", "desc": "한 줄 설명"}}`입니다. 폴더마다 `_project.md`(에이전트 지침)를 두면 검색에 함께 쓰입니다.

## 응답 형식

| 경우 | 응답 |
|---|---|
| POST 성공 | `200 {"ok": true, "result": ...}` |
| POST 실패 | `400 {"ok": false, "error": "ValueError: ..."}` |
| GET | 객체를 그대로 돌려줍니다 |

## 엔드포인트

| 메서드·경로 | 요청 | 하는 일 | `result` |
|---|---|---|---|
| `GET /api/state` | | 전체 상태 | 아래 [State](#state) |
| `GET /api/events` | | 새 파일 감지 등의 알림. 화면은 2초마다 부르고, `version`이 바뀌면 `state`를 다시 읽습니다 | `{version, events: [{path, text}], watch}` |
| `POST /api/analyze` | `{id}` | 파일을 다시 판단합니다 | Run |
| `POST /api/answer` | `{id, project_id}` | 질문에 답합니다. 페이지 규칙과 `_project.md` 메모를 배웁니다. **파일은 옮기지 않습니다** | 배운 메모 `{note, trace}` 또는 `null` |
| `POST /api/approve` | `{id, plan}` | 계획을 실행합니다(폴더로 이동). `plan`은 `state`에서 받은 그대로 보냅니다 | 실행 여부 |
| `POST /api/keep` | `{id}` | "여기 그대로 두기" | `null` |
| `POST /api/undo` | `{id}` | 이동을 되돌리고, 그 승인으로 배운 페이지 규칙을 지웁니다 | `null` |
| `POST /api/digest_now` | | 정리 안 된 파일을 번호 목록으로 모읍니다 | Digest 또는 `null` |
| `POST /api/digest_reply` | `{text}` | 자연어 답장을 해석해 미리보기를 만듭니다. Qwen이 필요하고 2~4분 걸립니다 | Digest(`proposal` 포함) |
| `POST /api/digest_apply` | | 미리보기대로 폴더를 만들고 옮깁니다 | `[{name, project, ...}]` |
| `POST /api/restore_trashed` | `{i}` | 휴지통으로 옮긴 설치 파일을 원래 자리로 되돌립니다 | `null` |
| `POST /api/reset` | | **데모 폴더 전용.** 데모가 만들지 않은 폴더에는 거부합니다 | |

답하고 바로 옮기려면 `answer` → `state`에서 새 `plan`을 받아서 → `approve` 순서로 부릅니다.

## State

```jsonc
{
  "controller": "규칙 → Qwen3 하이브리드 ...",
  "root": "<작업폴더>",
  "assets": [Asset],
  "journal": [{"asset", "src", "dst", "hash", "state": "prepared|done|rolled_back|undone"}],  // 최근 20개
  "catalog": [{"id", "name", "desc", "status"}],  // 프로젝트(폴더) 목록
  "digest": Digest | null,
  "pending": 3,            // 답을 기다리는 파일 수
  "trashed": [{"i", "path", "trash", "at"}]  // 휴지통으로 옮긴 설치 파일, 최근 10개 (at = unix 초)
}
```

### Asset

| 필드 | 뜻 |
|---|---|
| `id` | 파일 id. 모든 POST에 씁니다 |
| `original`, `path` | 처음 들어온 위치와 지금 위치. 둘이 다르면(`archived: true`) 이미 옮긴 파일입니다 |
| `project` | 정해진 프로젝트 id 또는 `null` |
| `keep` | "그대로 두기"를 눌렀는지 |
| `plan` | `{action, reason, target?}`. `action`은 `file`(폴더로 저장), `archive`, `keep`, `defer`(보류) 중 하나입니다 |
| `run` | 아래 Run |
| `why` | 판단 근거 문장 목록. 도구가 실제로 돌려준 사실로만 만듭니다 |

### Run

| 필드 | 뜻 |
|---|---|
| `status` | `planned`(정함), `waiting_user`(질문 중), `budget_exceeded`, `error: ...` |
| `decider` | 누가 정했나: `source`(다운로드 페이지 규칙), `rule`(규칙), `model`(Qwen) |
| `project`, `evidence` | 지정한 프로젝트와 근거. 근거는 원문을 그대로 인용한 것입니다 |
| `question`, `candidates` | 질문 중일 때의 질문 문장과 후보 프로젝트 id |
| `trace` | 도구 호출 기록 `[{tool, arguments, result}]` |
| `steps`, `errors`, `seconds` | 단계 수, 거부된 호출 수, 걸린 시간 |
| `trigger` | `watch`면 자동 감지로 시작된 판단입니다 |
| `answered`, `learned` | 사용자가 답한 프로젝트와, 그때 `_project.md`에 덧붙인 메모 |

### Digest

```jsonc
{
  "items": [{"n": 1, "aid", "name", "hint"}],  // hint: 첫 줄 내용 + 에이전트 후보
  "asked": 1793929676.0,
  "proposal": {                                  // digest_reply 뒤에 생깁니다
    "new_projects": {"NEW_1": {"name", "desc", "folder"}},
    "moves": [{"n", "aid", "name", "project_id"}],
    "leave": [{"n", "aid", "name"}]
  }
}
```

## 웹 연결 계약(`web/INTEGRATION.md`)과의 대응

| 웹 화면 | 에이전트 쪽 |
|---|---|
| 대시보드·모든 파일 | `state.assets`: 위치, 프로젝트, 계획, 근거. 해시는 `journal[].hash`에 있습니다 |
| 폴더·지침 | `state.catalog`과 폴더별 `_project.md`. 답변·승인 때마다 `## 학습된 자료 (승인 기록)` 아래에 한 줄씩 덧붙입니다(덧붙이기만 함, 최대 40줄) |
| 분류 대기 | `run.status == "waiting_user"`인 파일의 `question`, `candidates`, `why`. 답은 `answer`, 실행은 `approve` |
| 삭제 관리 | `state.trashed`와 `restore_trashed`. 지금 정책은 설치 파일(`.dmg`, `.pkg`, setup/install `.zip`·`.exe`)만, 처음 본 뒤 N일, 맥 시계 기준이고, 지우지 않고 휴지통으로 옮깁니다 |
| 처리 기록 | `state.journal`, `undo` |

## 아직 없는 것

- **요청 ID(중복 실행 방지):** 대신 `approve`는 받은 `plan`이 지금 다시 계산한 계획과 다르면 거부합니다(`stale plan`). 그리고 원본 해시가 바뀌었거나 대상에 같은 이름이 있으면 실행하지 않습니다. 같은 요청이 두 번 와도 두 번째는 실패합니다.
- **인증과 사용자 구분:** 이 API는 한 맥, 한 사용자만 다룹니다. 여러 사용자는 Django 쪽에서 나눠야 합니다.
- **Django로 보내기(push):** 에이전트가 Django API에 결과를 올리는 코드는 아직 없습니다. 연결 방식은 둘 중 하나입니다.
  - 맥의 작은 동기화 스크립트가 `/api/state`와 `/api/events`를 읽어 Django에 올리고, 사용자 결정을 받아 `answer`/`approve`로 넘깁니다.
  - 에이전트에 그 기능을 직접 넣습니다.
- **파일 미리보기:** 원본 파일 내용이나 이미지는 API로 내보내지 않습니다. 개인 파일이 맥 밖으로 나가지 않게 하려는 것입니다.
