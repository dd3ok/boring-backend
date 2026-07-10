# Boring Backend Skill

[English](README.md)

Boring Backend는 API와 서비스의 신뢰성 작업을 설계, 구현, 리뷰하는 AI 코딩 에이전트를 위한 compact skill입니다.

## 설계 방향

Boring Backend는 AI 코딩 에이전트가 흔히 보이는 문제를 줄이기 위해 만들었습니다. 과하게 설계하거나, 중요한 예외 케이스를 놓치거나, 검증하지 않은 상태에서 확신을 크게 말하는 문제를 줄이는 데 초점을 둡니다.

이 스킬은 다음 관점을 함께 사용합니다.

- 테스트를 의식한 문제 정의: happy path보다 실패 모드에서 시작합니다. 가능한 경우 모든 guard는 실행 가능한 증거로 끝나야 합니다. 정적 리뷰와 체크리스트도 도움이 되지만, 테스트나 smoke run이 없으면 신뢰도는 낮게 봅니다.
- 에이전트 작업 위생: 변경은 작게 유지하고, 가정은 명시하며, 가장 작은 작동 경로를 선택합니다. 성공 기준은 에이전트가 실제로 실행할 수 있는 명령으로 정의합니다.
- SOLID와 YAGNI의 균형: 라우팅, 도메인 규칙, 영속성, DTO, 에러 매핑처럼 현재 계약에 필요한 책임은 분리합니다. 반대로 미래 확장을 위한 인터페이스, 팩토리, 전략 패턴, 플러그인 계층은 현재 필요하지 않으면 만들지 않습니다.

의도한 장점은 트리거를 하나로 유지하면서도 내부 모드로 설계, 구현, 리뷰, 운영 증거 점검을 나누는 것입니다. 이렇게 하면 발견과 호출은 단순하게 유지하면서도 정확성, 보안, 데이터 무결성, 상태 코드, 성능, 운영 guardrail을 함께 확인할 수 있습니다.

## Skill

- `boring-backend`: 인증, 데이터 무결성, 멱등성, 동시성, 성능, 분산 환경 동작, 운영 리스크가 얽힌 API/service 작업을 설계, 구현, 리뷰할 때 사용합니다.

이 스킬은 하나의 트리거 아래에서 네 가지 모드로 동작합니다.

- Design: 구현 전에 API 계약, 불변식, guard 전략, 트레이드오프, 필요한 증거 수준을 정리합니다.
- Implementation: 범위를 통제하면서 API/service 코드를 구현하고, 테스트와 guard evidence를 남깁니다.
- Review: P0-P4 기준으로 신뢰성, 보안, 데이터 무결성, 성능, 호환성, 운영 리스크를 점검합니다.
- Production evidence: 로컬 테스트 증거와 load test, query plan, p95/p99 latency, saturation, rollout/rollback, observability 증거를 구분합니다.

## 구조

- `skills/boring-backend/`: 원본 skill 패키지입니다.
- `.agents/skills/boring-backend/`: Codex/Antigravity 스타일의 프로젝트 로컬 미러입니다.
- `.claude/skills/boring-backend/`: Claude Code용 프로젝트 로컬 미러입니다.
- `validation/`: 레포 유지보수용 behavior, trigger, fairness 평가 입력입니다. 설치되는 runtime skill 밖에 둡니다.
- `scripts/run_skill_eval.py`: 선택적으로 provider adapter를 trigger suite에 실행하고 크기가 제한된 프로토콜 출력을 `reports/` 아래에 기록합니다.
- `scripts/verify_all.py`: 미러와 레포 검증을 한 번에 실행합니다.
- `scripts/verify_boring_backend_skill_mirrors.py`: 원본 skill과 미러 패키지가 동기화되어 있는지 검증합니다.
- `reports/`: 생성된 평가 출력을 두는 ignore 대상 작업 디렉터리입니다. 빈 로컬 경로만 유지합니다.

## 설치

Codex `skill-installer`를 사용할 때는 runtime skill 폴더만 설치합니다.

```text
--repo dd3ok/boring-backend --ref v1.0.0 --path skills/boring-backend
```

아직 릴리스하지 않은 변경을 의도적으로 시험할 때만 `--ref main`을 사용하세요.

수동 설치도 경로 기준으로만 하면 됩니다. `skills/boring-backend` 폴더를 사용하는 런타임의 skills 디렉터리에 복사합니다.

자주 쓰는 설치 위치는 다음과 같습니다.

| Runtime | 프로젝트 범위 | 사용자 범위 |
|---|---|---|
| Codex / Agents | `.agents/skills/boring-backend` | `$HOME/.agents/skills/boring-backend` |
| Claude Code | `.claude/skills/boring-backend` | `~/.claude/skills/boring-backend` |
| Antigravity | `.agents/skills/boring-backend` | `~/.gemini/config/skills/boring-backend` |

`.agents/`, `.claude/`, `validation/`, `reports/`, `scripts/` 전체를 runtime skill로 설치하지 마세요. 이들은 개발용 미러, 평가 자산, 생성 출력, 검증 유틸리티입니다.

## 검증

검증은 CPython 3.11부터 3.14까지 지원합니다. 더 최신 CPython 버전은 검증되지 않았습니다.

프로젝트 로컬 Python 3 가상환경에 개발 의존성을 설치합니다.

```text
python -m pip install -r requirements-dev.txt
```

그다음 레포 루트에서 활성화된 가상환경이나 운영체제의 Python 3 실행기로 검증 진입점을 실행합니다.

```text
python scripts/verify_all.py
python3 scripts/verify_all.py  # macOS/Linux
py -3 scripts/verify_all.py    # Windows
```

GitHub Actions에서는 같은 진입점을 Ubuntu, macOS, Windows의 CPython 3.14에서 실행하고, Ubuntu의 CPython 3.11에서도 실행합니다.

## 평가

실제 에이전트 평가는 선택적으로 실행하며 CI에는 넣지 않습니다. Adapter는 신뢰하는 로컬 프로그램이며, harness는 프로토콜을 검증할 뿐 sandbox가 아닙니다. Adapter는 background descendant를 만들거나 request의 run directory 밖에 쓰면 안 됩니다. Timeout 시 adapter process tree 정리는 최선 노력(best effort)으로 수행합니다.

보고서 `--output`은 `reports/` 아래에 둘 수 있지만 실제 실행은 그 안에서 하지 않습니다. Harness는 기본적으로 저장소 밖의 시스템 임시 경로에 실행용 work root를 만들고 실행 후 정리합니다. 디버깅을 위해 `--work-root`를 직접 지정하면 그 경로를 보존합니다. 이 경로는 새 경로이거나 비어 있어야 하고, 보고서 경로와 분리되어야 하며, 저장소 밖에 있어야 하고, 상위 경로에 같은 이름의 `.agents/skills/`, `.claude/skills/`, `.codex/skills/`, `.gemini/config/skills/`가 없어야 합니다. 이 조건으로 work path에서 발견 가능한 프로젝트·사용자 스킬 복사본이 no-skill baseline에 섞이는 문제를 막습니다.

Harness는 각 adapter를 해당 run의 작업 디렉터리에서 시작합니다. 저장소 루트 기준으로 존재하는 runner command 파일 인자는 실행 전에 절대 경로로 바꿉니다. Adapter는 `--request`, `--response` JSON 경로를 받고 평가 대상 agent를 request의 `paths.workspace`에서 실행해야 하며, agent에는 request 최상위의 `query`만 전달해야 합니다. 또한 request의 `isolation` 계약에 따라 `allowed_skill_path` 밖에 있는 같은 이름의 사용자·관리자·managed·기설치 스킬을 비활성화하고, 필수 응답 확인에 격리 방법을 반환해야 합니다. 평가 suite, label, case id, rationale, 예상 결과를 들여다보면 안 됩니다. 이 규칙을 어긴 adapter의 metric은 신뢰할 수 없습니다. Activation, catalog read, usage는 벤더 trace나 API가 제공할 때만 기록하고, 알 수 없는 값은 `null`로 남겨야 합니다.

Case/trial block과 block 안의 variant 순서는 `--seed`로 결정론적으로 무작위화하며, 한 block의 모든 variant에는 동일한 paired seed를 전달합니다. 응답 객체는 `activation` (`bool|null`), `catalogs` (`string[]|null`), `usage` (`object|null`), 실행 디렉터리 기준 `artifacts`, adapter `metadata`, 필수 `isolation` 확인을 받습니다. 격리 확인은 `verified`를 `true`로 설정하고, 비어 있지 않은 `method`와 빈 `unexpected_same_name_skills` 배열을 제공해야 합니다. 이 조건을 만족하지 않으면 run이 실패합니다. Usage 값은 `null` 또는 0 이상 9,007,199,254,740,991 이하의 정수여야 합니다. Harness는 stdout을 버리고 stderr를 동시에 비우면서 최대 2 KiB excerpt만 보관합니다. JSON nesting은 100으로 제한하고, 응답은 최대 64 KiB에 1 byte를 더 읽어 상한 초과를 감지하며, 선언 artifact는 최대 32개 파일, 합계 16 MiB까지 허용합니다.

각 보고서에는 보관된 request/response 파일, 제한된 stderr excerpt, 선언된 artifact, JSONL 결과, summary, manifest가 포함됩니다. 선언하지 않은 workspace 파일과 run별 runtime 복사본은 격리된 work root의 수명 동안만 존재하고 보고서로 복사하지 않습니다. Manifest에는 work-root 정책, Git commit과 dirty 상태, dirty일 때 worktree/diff digest, harness hash, skill hash, 파일로 해석되는 runner command 인자의 hash를 기록합니다.

```text
python scripts/run_skill_eval.py --output reports/eval/run-001 --trials 3 --seed 17 --variant current=skills/boring-backend --variant baseline --runner-exe python --runner-arg path/to/vendor_adapter.py --runner-meta vendor=example --runner-meta model=example
```

저장소에 포함된 것은 프로토콜 검사용 결정론적 fixture뿐이며 실제 벤더 adapter가 아닙니다. Fixture 실행은 harness 동작만 증명하며 스킬 품질이나 토큰 절감 효과를 증명하지 않습니다. `forward-test-prompts.md`는 사람이 평가하거나 별도 grader가 사용하는 behavior rubric으로 유지합니다.

## 라이선스

MIT 라이선스를 적용합니다. 자세한 내용은 `LICENSE`를 확인하세요.
