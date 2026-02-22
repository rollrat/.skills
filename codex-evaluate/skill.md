---
name: codex-evaluate
description: 로컬 Codex CLI를 사용해 파일이나 텍스트의 품질을 평가합니다. /codex-evaluate <파일경로 또는 평가대상> [기준] 로 실행.
---

# Codex Evaluate - 로컬 Codex CLI 품질 평가기

## Overview

로컬에 설치된 `codex exec`를 사용하여 파일 또는 텍스트의 품질을 평가한다.
파일 경로를 넘기면 Codex가 직접 읽고 평가하며, 평가 기준은 자유롭게 지정할 수 있다.

핵심 커맨드:
```bash
codex exec \
  -c 'sandbox_permissions=["disk-full-read-access"]' \
  "평가 프롬프트..."
```

- `codex exec`: 비대화형 모드 (결과를 stdout으로 출력)
- `sandbox_permissions=["disk-full-read-access"]`: 로컬 파일 전체 읽기 허용
- 모델: 계정 기본값 사용 (`-m <model>` 옵션으로 오버라이드 가능)

## Usage

```
/codex-evaluate <파일경로_또는_평가대상> [평가기준]
```

### Examples
```
/codex-evaluate ~/Desktop/agents/content/youtube/영상요약.md
/codex-evaluate ~/Desktop/agents/content/youtube/영상요약.md "정확성, 가독성, 완전성 위주로"
/codex-evaluate ~/report.md --model gpt-4o
```

### Parameters
- `<파일경로>`: 평가할 파일의 절대/상대 경로. 여러 파일은 쉼표로 구분.
- `[평가기준]`: 선택적. 없으면 기본 5개 기준으로 평가.
- `--model <model>`: 선택적. 기본값은 Codex 계정 기본 모델.

### 기본 평가 기준 (별도 지정 없을 때)
1. **정확성** (0~10): 내용이 사실에 부합하고 오류가 없는가?
2. **완전성** (0~10): 핵심 내용이 빠짐없이 포함되었는가?
3. **가독성** (0~10): 문장이 자연스럽고 이해하기 쉬운가?
4. **구조** (0~10): 형식과 구성이 논리적이고 탐색하기 좋은가?
5. **키워드/태그** (0~10): 핵심 주제를 잘 대표하는가?

## Critical Rules

### 날짜 처리 (필수)
- 현재 날짜/시간은 반드시 Bash 커맨드로 얻는다. 절대 추론하거나 추정하지 않는다.
- 파일명, frontmatter 등 모든 곳에서 커맨드 출력값만 사용한다.
  - `date '+%Y-%m-%d'` → 2026-02-15

### 출력 언어
- 모든 평가 결과는 **한국어**로 출력한다.
- 평가 프롬프트에 `평가 결과를 한국어로 출력해달라`를 반드시 포함한다.

### Windows 호환
- 경로는 Unix 스타일(`/c/Users/rollrat/...`) 사용.
- codex exec 출력은 UTF-8이므로 별도 디코딩 불필요.

### codex 모델 주의
- `-m o4-mini`는 ChatGPT 계정에서 지원되지 않을 수 있음 → 모델 오류 시 `-m` 옵션 제거하고 재시도.
- 계정 기본 모델은 `gpt-5.3-codex` 등 자동 선택됨.

## Workflow

### 1. 입력 파싱

- 파일 경로 추출 (여러 개면 쉼표 구분)
- 평가 기준 추출 (없으면 기본 5개 기준 사용)
- `--model` 옵션 파싱

인자 없이 실행된 경우 → 사용법 안내 출력 후 종료.

### 2. codex 설치 확인

```bash
which codex || where codex
```

없으면:
```bash
npm install -g @openai/codex
```

### 3. 평가 프롬프트 구성

```
아래 파일(들)을 읽고 품질을 평가해달라.

평가 대상 파일:
{파일경로1}
{파일경로2}  (여러 개일 경우)

평가 기준:
{사용자 지정 기준 또는 기본 5개 기준}

각 항목별로 점수(0~10)와 이유를 설명하고,
종합 점수와 개선 제안을 제시해달라.

평가 결과를 한국어로 출력해달라.
```

### 4. codex exec 실행

모델 옵션 없이 (기본 모델):
```bash
codex exec \
  -c 'sandbox_permissions=["disk-full-read-access"]' \
  "{평가 프롬프트}"
```

모델 지정 시:
```bash
codex exec \
  -m {model} \
  -c 'sandbox_permissions=["disk-full-read-access"]' \
  "{평가 프롬프트}"
```

### 5. 결과 출력

codex exec의 stdout을 그대로 사용자에게 출력한다.

실패 시:
- `ERROR: The '...' model is not supported` → 모델 옵션 제거 후 재시도
- exit code != 0 → 에러 메시지 출력 후 종료

## 인자 없이 실행 시 동작

**`/codex-evaluate`를 인자 없이 실행하면 아래 안내를 출력하고 즉시 종료한다.**

```
🔍 Codex Evaluate - 로컬 Codex CLI 품질 평가기

사용법:
  /codex-evaluate <파일경로>
  /codex-evaluate <파일경로> "정확성, 완전성 위주로 평가"
  /codex-evaluate <파일1>,<파일2> --model gpt-4o

예시:
  /codex-evaluate ~/Desktop/agents/content/youtube/영상요약.md
  /codex-evaluate ~/report.md "논리 구조와 근거의 타당성 중심으로"

기본 평가 기준 (기준 미지정 시):
  1. 정확성  (0~10)
  2. 완전성  (0~10)
  3. 가독성  (0~10)
  4. 구조    (0~10)
  5. 키워드  (0~10)

핵심 동작:
  codex exec -c 'sandbox_permissions=["disk-full-read-access"]' "프롬프트"
```

## Error Handling

- **codex 미설치**: `npm install -g @openai/codex` 안내 후 중단.
- **파일 없음**: 경로 확인 안내 출력. Codex가 스스로 파일 찾는 시도를 하지만, 사전 존재 확인 권장.
- **모델 미지원 에러**: `-m` 옵션 제거 후 재시도.
- **API 인증 오류**: `codex login` 실행 안내.
- **타임아웃**: 파일이 매우 크거나 기준이 복잡하면 처리 시간이 길어질 수 있음 — 기준을 단순화하거나 파일을 줄여서 재시도.
