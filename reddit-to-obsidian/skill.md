---
name: reddit-to-obsidian
description: Reddit SaaS 게시판 글을 Chrome DevTools MCP로 읽고, 요약해서 Obsidian 볼트에 저장합니다. /reddit-to-obsidian <url_or_subreddit> 로 실행.
---

# Reddit to Obsidian - SaaS 게시물 수집 & 요약

## Overview

Chrome DevTools MCP를 사용하여 Reddit SaaS 관련 게시글과 댓글을 읽고, **하나의 총 요약 문서**로 만들어 Obsidian 볼트의 `reddit/` 폴더에 저장합니다.

## Usage

```
/reddit-to-obsidian <reddit_url_or_subreddit> [options]
```

### Options
- `<url>`: 특정 Reddit 게시물 URL (단일 글 요약)
- `<subreddit>`: 서브레딧 이름 (예: SaaS, microsaas) - 상위 인기글 수집
- `--top <n>`: 수집할 게시물 수 (기본: 10)
- `--sort <type>`: 정렬 방식 - hot, new, top (기본: hot)
- `--folder <name>`: Obsidian 저장 폴더 (기본: reddit)

## Critical Rules

### Chrome MCP 에러 처리
**Chrome DevTools MCP 접근이 실패하면 즉시 사용자에게 에러 메시지를 출력하고 중단한다.** WebFetch 등 다른 도구로 우회하지 않는다.

예시 출력:
```
Chrome DevTools MCP 연결 실패: {에러 메시지}
Chrome이 디버그 모드로 실행 중인지 확인해주세요.
```

### 문서 생성 규칙
- **글마다 개별 문서를 만들지 않는다**
- **모든 글을 하나의 총 요약 문서로 합쳐서 생성한다**
- 파일명은 **날짜+시간** 형식: `reddit/{YYYY-MM-DD_HHmm}/{subreddit}.md`
  - 예: `reddit/2026-02-14_1530/SaaS.md`

## Workflow

### 0. 현재 시간 확인 (필수)

**가장 먼저 Bash로 `date "+%Y-%m-%d_%H%M"` 명령을 실행하여 실제 현재 시간을 확인한다.**
이 값을 파일 저장 경로의 `{YYYY-MM-DD_HHmm}` 부분에 사용한다.
절대로 시간을 추측하거나 임의로 넣지 않는다.

### 1. Chrome DevTools MCP 연결 확인

**`list_pages`를 호출하여 Chrome MCP 연결 상태를 확인한다.**
- 실패 시: 에러 출력 후 즉시 중단
- 성공 시: 다음 단계 진행

### 2. Chrome DevTools MCP로 Reddit 데이터 수집

Reddit JSON API를 Chrome DevTools MCP를 통해 접근:
- 서브레딧 모드: `https://www.reddit.com/r/{subreddit}/hot.json?limit=10`
- 특정 글 모드: `https://www.reddit.com/r/{subreddit}/comments/{id}.json`

1. `navigate_page`로 JSON URL 이동
2. `evaluate_script`로 JSON 파싱하여 게시물 목록 추출
3. 각 게시물의 댓글 JSON URL로 이동하여 상위 댓글 추출

### 3. 데이터 추출 대상

각 게시물에서 다음 정보를 추출:

- **제목** (title) - 영어 원문 그대로
- **원문 URL** (permalink)
- **작성자** (author)
- **작성일** (created_utc)
- **업보트 수** (score)
- **본문 내용** (selftext) - 최대 1500자. 링크 포스트면 URL도 포함
- **댓글 수** (num_comments)
- **상위 댓글 10개**: 작성자, 내용(최대 300자), 점수
- **게시물 flair/태그**

**본문 추출 시 주의:**
- selftext가 500자 이상이면 1500자까지 가져와야 핵심 내용을 놓치지 않음
- 링크/제품 URL이 포함되어 있으면 반드시 추출 (프로모션 판별에 필요)
- 댓글에서 WHOIS, SimilarWeb, 사이트 결함 등 사기 적발 증거도 중요 데이터

### 4. 총 요약 문서 생성

추출한 모든 게시물 데이터를 분석하여 **하나의 요약 문서**로 생성한다.

Obsidian 볼트 경로: `C:\Users\rollrat\Documents\Obsidian Vault`

파일 경로: `reddit/{YYYY-MM-DD_HHmm}/{subreddit}.md`

#### 마크다운 템플릿

**중요: 아래 형식을 정확히 따른다. 단순 요약이 아니라 비판적 분석을 포함해야 한다.**

```markdown
---
title: "r/{서브레딧} 정리 - {날짜 시간}"
subreddit: "{서브레딧}"
date_saved: "{YYYY-MM-DD HH:mm}"
posts_count: {수집 게시물 수}
tags:
  - reddit
  - saas
  - digest
---

# r/{서브레딧} 정리 - {YYYY-MM-DD HH:mm}

## 1. {이모지} {한국어 요약 제목} (⬆{점수}, 💬{댓글수})
[{영어 원문 제목}]({Reddit permalink})

| 항목 | 내용 |
|------|------|
| {핵심 속성1} | {값1} |
| {핵심 속성2} | {값2} |
| {핵심 속성3} | {값3} |

댓글 핵심:
- {핵심 댓글 인용 또는 요약} (⬆{점수}) — {부연 설명}
- {찬반이 갈리면 양쪽 모두 인용}
- {프로모션/사기 의심 시 적극 지적}

---

## 2. {이모지} {다음 게시물}...

(모든 게시물 반복. 점수 높은 순서대로 정렬)

---

## 🔍 메타 분석: r/{서브레딧} 커뮤니티 현재 트렌드

### 1. {트렌드 제목}
{전체 게시물에서 반복되는 패턴/합의/갈등을 분석. 2-3문장.}

### 2. {트렌드 제목}
{구체적 예시와 함께 설명}

### 3. {트렌드 제목}
...

(3-5개 트렌드 도출)

---

## 🔗 언급된 도구 & 서비스
- [{도구명}]({URL}) - {간단 설명}
- ...
```

#### 작성 가이드라인

**게시물별 작성 규칙:**
- **링크와 표 사이에 반드시 빈 줄을 넣는다.** Obsidian 마크다운 파서는 이전 블록과 표 사이에 빈 줄이 없으면 표를 렌더링하지 않는다. `[제목](URL)` 바로 다음 줄에 `| 항목 |`이 오면 안 되고, 반드시 한 줄 띄어야 한다.
- 헤더에 게시물 성격을 나타내는 이모지 포함 (🚀런칭, 💀사기적발, ⚠️경고, 💼전략, 🔧기술, 🇩🇪국가, ⚙️도구비교, 📢교훈, 💰매출 등)
- `항목/내용` 테이블로 핵심 정보를 구조화 (제품, 상황, 주장, 전략, 핵심 논리, 결과 등 게시물 성격에 맞는 항목 선택)
- 댓글은 점수(⬆) 포함하여 인용. 찬반이 갈리면 양쪽 모두 포함
- 프로모션 의도가 보이면 명시적으로 지적 (예: "OP가 본인 제품 홍보 의도 있음")
- 사기/가짜 글이 적발되면 댓글의 증거를 상세히 기록 (WHOIS, SimilarWeb, 사이트 결함 등)
- AI 생성 콘텐츠 의심 시 언급 (예: "Thanks ChatGPT" 댓글, 글 자체의 AI 슬롭 여부)

**댓글 분석 규칙:**
- 단순 긍정 댓글은 생략하고, 실질적 인사이트/반론/증거가 있는 댓글만 포함
- 점수가 높은 댓글일수록 상세히 인용
- 댓글 간 논쟁이 있으면 흐름을 보여줌 (예: "배관공 1000곳에 이메일 → 수익=£0" → "배관공은 이메일 안 읽음. WhatsApp이나 현장 방문")
- 실패 경험, 구체적 숫자, 반직관적 조언이 있는 댓글을 우선 포함

**메타 분석 규칙:**
- 개별 글 요약이 아니라, 전체 게시물을 관통하는 **커뮤니티 수준의 패턴**을 도출
- 합의가 형성되고 있는 주제, 찬반이 갈리는 주제, 새로 떠오르는 키워드를 구분
- 커뮤니티의 프로모션/AI슬롭 감지 능력, 모더레이션 상태도 관찰
- 구체적 게시물을 예시로 인용하며 근거 제시

## Examples

```bash
# 특정 게시물 하나 요약
/reddit-to-obsidian https://www.reddit.com/r/SaaS/comments/abc123/my_saas_hit_10k_mrr/

# r/SaaS 인기글 10개 수집 (기본)
/reddit-to-obsidian SaaS

# r/microsaas 최신글 15개 수집
/reddit-to-obsidian microsaas --top 15 --sort new
```

## Implementation Notes

Claude가 이 skill을 실행할 때:

1. **Chrome DevTools MCP 연결 확인**: `list_pages` 호출. 실패 시 에러 출력 후 중단.
2. **Chrome DevTools MCP로 Reddit JSON API 접근**: `navigate_page`로 JSON URL 이동, `evaluate_script`로 데이터 추출.
3. **비판적 분석 요약 생성**: 추출된 데이터를 분석하여 한국어로 요약. 단순 정리가 아닌 **비판적 시각** 포함:
   - 프로모션/셀프프로모 의도 감지 및 명시
   - AI 생성 콘텐츠 의심 여부 판별
   - 사기/가짜 스토리 적발 증거 기록
   - 댓글 간 논쟁 구조 보존
   - 커뮤니티 전체 트렌드 메타 분석
4. **게시물 정렬**: 점수(score) 높은 순서대로 정렬하여 문서 작성.
5. **Obsidian에 저장**: Obsidian MCP의 `write_note` 도구를 사용하여 볼트에 저장. **파일명의 날짜+시간은 반드시 Bash `date "+%Y-%m-%d_%H%M"` 명령으로 실제 현재 시간을 확인한 후 사용한다.** 추측이나 임의 시간을 넣지 않는다.

### Reddit JSON API 활용

Reddit URL 뒤에 `.json`을 붙이면 JSON 데이터를 얻을 수 있습니다:
- 게시물: `https://www.reddit.com/r/SaaS/hot.json?limit=10`
- 특정 글: `https://www.reddit.com/r/SaaS/comments/{id}.json`

Chrome DevTools로 이 JSON URL에 접근하여 `evaluate_script`로 파싱합니다.

## Error Handling

- **Chrome MCP 연결 실패**: 에러 메시지 출력 후 **즉시 중단**. 다른 도구로 우회하지 않음.
- **Reddit 접근 불가**: 로그인 필요 시 안내, rate limit 시 안내 후 중단
- **Obsidian 볼트 없음**: 볼트 경로 확인 안내
