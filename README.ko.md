# Boring Backend Skill

[English](README.md)

Boring Backend는 API와 서비스의 신뢰성 작업을 설계, 구현, 리뷰하는 AI 코딩 에이전트를 위한 compact skill입니다.

## 설계 방향

Boring Backend는 AI 코딩 에이전트가 흔히 보이는 문제를 줄이기 위해 만들었습니다. 과하게 설계하거나, 중요한 예외 케이스를 놓치거나, 검증하지 않은 상태에서 확신을 크게 말하는 문제를 줄이는 데 초점을 둡니다.

이 스킬은 다음 관점을 함께 사용합니다.

- 테스트를 의식한 문제 정의: happy path보다 실패 모드에서 시작합니다. 가능한 경우 모든 guard는 실행 가능한 증거로 끝나야 합니다. 정적 리뷰와 체크리스트도 도움이 되지만, 테스트나 smoke run이 없으면 신뢰도는 낮게 봅니다.
- 에이전트 작업 위생: 변경은 작게 유지하고, 가정은 명시하며, 가장 작은 작동 경로를 선택합니다. 성공 기준은 에이전트가 실제로 실행할 수 있는 명령으로 정의합니다.
- SOLID와 YAGNI의 균형: 라우팅, 도메인 규칙, 영속성, DTO, 에러 매핑처럼 현재 계약에 필요한 책임은 분리합니다. 반대로 미래 확장을 위한 인터페이스, 팩토리, 전략 패턴, 플러그인 계층은 현재 필요하지 않으면 만들지 않습니다.

의도한 장점은 트리거를 하나로 유지하면서도 내부 모드로 설계, 구현, 리뷰를 나누는 것입니다. 이렇게 하면 발견과 호출은 단순하게 유지하면서도 정확성, 보안, 데이터 무결성, 상태 코드, 성능, 운영 guardrail을 함께 확인할 수 있습니다.

## Skill

- `boring-backend`: 인증, 데이터 무결성, 멱등성, 동시성, 성능, 분산 환경 동작, 운영 리스크가 얽힌 API/service 작업을 설계, 구현, 리뷰할 때 사용합니다.

이 스킬은 하나의 트리거 아래에서 세 가지 모드로 동작합니다.

- Design: 구현 전에 API 계약, 불변식, guard 전략, 트레이드오프, 필요한 증거 수준을 정리합니다.
- Implementation: 범위를 통제하면서 API/service 코드를 구현하고, 테스트와 guard evidence를 남깁니다.
- Review: 신뢰성, 보안, 데이터 무결성, 성능, 호환성, 운영 리스크를 영향도 순으로 보고합니다.

환경별 운영 증거를 명시적으로 요청한 경우에는 침습적 작업 전에 조건부 안전 reference를 읽습니다.

## 구조

- `skills/boring-backend/`: 원본 skill 패키지입니다.
- `.agents/skills/boring-backend/`: Codex/Antigravity 스타일의 프로젝트 로컬 미러입니다.
- `.claude/skills/boring-backend/`: Claude Code용 프로젝트 로컬 미러입니다.
- `validation/`: 레포 유지보수용 behavior, trigger, fairness 평가 입력입니다. 설치되는 runtime skill 밖에 둡니다.
- `scripts/verify_all.py`: 미러와 레포 검증을 한 번에 실행합니다.
- `scripts/verify_boring_backend_skill_mirrors.py`: 원본 skill과 미러 패키지가 동기화되어 있는지 검증합니다.

## 설치

Codex `skill-installer`를 사용할 때는 runtime skill 폴더만 설치합니다.

```text
--repo dd3ok/boring-backend --ref v1.1.1 --path skills/boring-backend
```

설치 대상에는 완전한 runtime 패키지만 들어 있습니다.

```text
boring-backend/
|-- SKILL.md
|-- LICENSE
|-- agents/openai.yaml
`-- references/*.md
```

이 파일들만으로 스킬 전체 기능이 동작합니다. `SKILL.md`가 필요한 reference만 조건부로 읽으며, 저장소의 테스트, 평가 입력, 검증 스크립트는 runtime 의존성이 아닙니다.

수동 설치할 때는 `skills/boring-backend` 폴더 전체를 아래 위치로 복사합니다. 연결된 reference도 동작의 일부이므로 `SKILL.md`만 따로 복사하지 마세요.

동일한 폴더를 설치하는 대표 위치는 다음과 같습니다.

| Runtime | 프로젝트 범위 | 사용자 범위 |
|---|---|---|
| Codex / Agents | `.agents/skills/boring-backend` | `$HOME/.agents/skills/boring-backend` |
| Claude Code | `.claude/skills/boring-backend` | `~/.claude/skills/boring-backend` |
| Antigravity | `.agents/skills/boring-backend` | 제품/버전별로 다름; 프로젝트 범위 권장 |

저장소 루트 전체를 설치하지 마세요. `.agents/`, `.claude/`, `.github/`, `validation/`, `tests/`, `scripts/`, `requirements-dev.txt`는 저장소 유지보수 파일이며 runtime skill에 포함되지 않습니다.

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

GitHub Actions에서는 같은 진입점을 Ubuntu, macOS, Windows의 CPython 3.14에서 실행하고, Ubuntu의 CPython 3.11, 3.12, 3.13에서도 실행합니다.

## 평가

Runtime 지침이나 기대 출력이 바뀌면 외부 provider별 runner로 behavior case를 실행하고, discovery metadata나 activation 경계가 바뀌면 trigger case를 실행합니다. 이 저장소에는 평가 입력과 격리 규칙만 두며 runner와 생성 결과는 포함하지 않습니다.

- `validation/trigger-eval-cases.json`: 스킬을 직접 언급하지 않은 요청에서 activation 경계를 점검합니다.
- `validation/behavior-eval-cases.json`: 스킬을 명시적으로 선택한 뒤 사용하는 prompt, 입력, grader 기대값의 machine-readable 정본입니다.
- `validation/experiment-fairness.md`: 격리, 채점, no-skill 또는 이전 버전과의 비교 규칙입니다.

## 라이선스

MIT 라이선스를 적용합니다. `LICENSE`를 확인하세요. 설치 가능한 runtime subtree에도 같은 전문을 `skills/boring-backend/LICENSE`로 포함합니다.
