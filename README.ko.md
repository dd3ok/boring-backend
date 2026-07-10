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
- `scripts/verify_all.py`: 미러와 레포 검증을 한 번에 실행합니다.
- `scripts/verify_boring_backend_skill_mirrors.py`: 원본 skill과 미러 패키지가 동기화되어 있는지 검증합니다.
- `reports/`: 생성된 평가 출력을 두는 ignore 대상 작업 디렉터리입니다. 빈 로컬 경로만 유지합니다.

## 설치

Codex `skill-installer`를 사용할 때는 runtime skill 폴더만 설치합니다.

```text
--repo dd3ok/boring-backend --path skills/boring-backend
```

수동 설치도 경로 기준으로만 하면 됩니다. `skills/boring-backend` 폴더를 사용하는 런타임의 skills 디렉터리에 복사합니다.

자주 쓰는 설치 위치는 다음과 같습니다.

| Runtime | 프로젝트 범위 | 사용자 범위 |
|---|---|---|
| Codex / Agents | `.agents/skills/boring-backend` | `$HOME/.agents/skills/boring-backend` |
| Claude Code | `.claude/skills/boring-backend` | `~/.claude/skills/boring-backend` |
| Antigravity | `.agents/skills/boring-backend` | `~/.gemini/config/skills/boring-backend` |

`.agents/`, `.claude/`, `validation/`, `reports/`, `scripts/` 전체를 runtime skill로 설치하지 마세요. 이들은 개발용 미러, 평가 자산, 생성 출력, 검증 유틸리티입니다.

## 검증

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

GitHub Actions에서도 같은 진입점을 Ubuntu, macOS, Windows에서 실행합니다.

## 라이선스

MIT 라이선스를 적용합니다. 자세한 내용은 `LICENSE`를 확인하세요.
