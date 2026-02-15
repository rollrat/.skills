---
name: skill-creator
description: 새로운 Claude Code 스킬을 생성하는 메타 스킬. 사용자의 공통 규칙(한국어 출력, 날짜 커맨드 필수 등)을 자동 적용합니다. /skill-creator <skill-name> <description> 로 실행.
---

# Skill Creator - 스킬 생성 메타 스킬

## Overview

새로운 Claude Code 커스텀 스킬을 생성합니다. 사용자의 공통 규칙과 환경 설정을 자동으로 반영하여 일관된 스킬을 만들어줍니다.

## Usage

```
/skill-creator <skill-name> "<description>"
```

### Examples
```
/skill-creator news-to-obsidian "네이버 뉴스 기사를 크롤링해서 옵시디언에 요약 저장"
/skill-creator podcast-summary "팟캐스트 RSS에서 에피소드 요약 생성"
```

인자 없이 실행하면 사용법 안내만 출력하고 종료한다.

## Critical Rules - 모든 스킬에 공통 적용

아래 규칙은 이 스킬로 생성하는 **모든 스킬**에 반드시 포함되어야 한다.

### 1. 출력 언어: 무조건 한국어
- 스킬이 처리하는 소스 데이터가 어떤 언어이든, **최종 요약/출력은 항상 한국어**로 작성한다.
- 스킬 정의 파일(skill.md) 자체도 한국어로 작성한다.
- 에이전트 프롬프트에 반드시 `한국어로 작성하라` 지시를 포함한다.

### 2. 날짜/시간: 반드시 커맨드로 직접 획득
- **절대 날짜를 추론하거나 추정하지 않는다.**
- 현재 날짜/시간이 필요한 모든 곳에서 Bash 커맨드를 실행하여 얻는다.
- 스킬 정의에 아래 내용을 Critical Rules 섹션에 명시한다:

```
### 날짜 처리 (필수)
- 현재 날짜/시간은 반드시 Bash 커맨드로 얻는다. 절대 추론하거나 추정하지 않는다.
- 파일명, frontmatter, 본문 등 모든 곳에서 커맨드 출력값만 사용한다.
- 예시:
  - `date '+%Y-%m-%d'` → 2026-02-15
  - `date '+%y.%m.%d_%H%M'` → 26.02.15_2130
  - `date '+%Y-%m-%dT%H:%M:%S'` → ISO 형식
```

### 3. Windows 환경 호환
- 스킬은 Windows 11 + Git Bash 환경에서 동작해야 한다.
- 외부 프로세스 출력은 cp949 인코딩일 수 있으므로 `.decode('cp949', errors='replace')` 처리를 기본으로 한다.
- 경로는 Unix 스타일(`/c/Users/rollrat/...`) 사용.

### 4. Obsidian 연동 시 공통 규칙
- Obsidian MCP의 `write_note` 도구를 사용한다.
- 파일명에 특수문자 사용하지 않는다 (`:`, `?`, `*`, `"`, `<`, `>`, `|` 금지).
- 문서 간 내부 링크는 `[[파일명]]` 형식을 사용한다.

### 5. 에이전트 사용 시 공통 규칙
- 병렬 실행 가능한 에이전트는 `run_in_background: true`로 동시 실행한다.
- 한 번에 최대 10개 배치, 초과 시 배치 분리.
- 에이전트 프롬프트에 항상 포함: `한국어로 작성하라`
- 기본 모델: `sonnet`. 비용 절감이 필요하면 `haiku`.

## Workflow

### 1. 입력 파싱

사용자로부터 스킬 이름과 설명을 받는다.
- 스킬 이름은 kebab-case (`my-skill-name`)
- 설명이 없으면 사용자에게 질문한다.

### 2. 스킬 설계 대화

사용자와 대화하며 스킬의 핵심 사항을 정한다:
- **입력**: 어떤 인자를 받는가?
- **처리**: 어떤 도구/API/에이전트를 사용하는가?
- **출력**: 결과를 어디에 어떤 형식으로 저장하는가?
- **옵션**: 어떤 선택적 파라미터가 있는가?

### 3. 스킬 파일 생성

`~/.claude/skills/{skill-name}/skill.md` 파일을 생성한다.

#### 필수 섹션 구조:

```markdown
---
name: {skill-name}
description: {한국어 설명}. /{skill-name} <args> 로 실행.
---

# {스킬 제목} - {한줄 설명}

## Overview
{스킬이 하는 일 설명}

## Usage
{호출 형식과 옵션}

## Critical Rules

### 날짜 처리 (필수)
- 현재 날짜/시간은 반드시 Bash 커맨드로 얻는다. 절대 추론하거나 추정하지 않는다.
- 파일명, frontmatter, 본문 등 모든 곳에서 커맨드 출력값만 사용한다.

### 출력 언어
- 모든 출력은 한국어로 작성한다.

### Windows 호환
- 외부 프로세스 출력 cp949 디코딩 처리.

{스킬 고유 규칙들}

## Workflow
{단계별 실행 흐름}

## 인자 없이 실행 시 동작
{사용법 안내 출력 후 종료}

## Error Handling
{에러 처리 방법}
```

### 4. 검증

생성된 스킬 파일이 아래를 충족하는지 확인:
- [ ] frontmatter에 name, description 있음
- [ ] Critical Rules에 날짜 커맨드 규칙 있음
- [ ] Critical Rules에 한국어 출력 규칙 있음
- [ ] Workflow에 구체적 코드/커맨드 예시 있음
- [ ] 인자 없이 실행 시 안내 출력 섹션 있음
- [ ] Error Handling 섹션 있음

### 5. 완료 보고

생성된 스킬 정보를 출력:
```
✅ 스킬 생성 완료

이름: {skill-name}
경로: ~/.claude/skills/{skill-name}/skill.md
호출: /{skill-name} <args>
설명: {description}
```

## 인자 없이 실행 시 동작

**`/skill-creator`를 인자 없이 실행하면 아래 안내를 출력하고 즉시 종료한다.**

```
🛠️ Skill Creator - Claude Code 커스텀 스킬 생성기

사용법:
  /skill-creator my-skill "스킬 설명"
  /skill-creator news-crawler "네이버 뉴스 크롤링 후 옵시디언 저장"

자동 적용되는 공통 규칙:
  • 출력 언어: 항상 한국어
  • 날짜/시간: Bash 커맨드로 직접 획득 (추론 금지)
  • Windows 환경 호환 (cp949 인코딩 처리)
  • Obsidian 연동 시 write_note 사용
  • 에이전트 병렬 실행, 기본 모델 sonnet

스킬은 ~/.claude/skills/{name}/skill.md 에 생성됩니다.
```

**이 안내만 출력하고 종료한다.**

## Error Handling

- **동일 이름 스킬 존재**: 덮어쓸지 사용자에게 확인 후 진행.
- **스킬 이름 부적절**: kebab-case가 아니면 자동 변환 후 확인.
- **설명 누락**: 사용자에게 어떤 스킬을 만들고 싶은지 질문.
