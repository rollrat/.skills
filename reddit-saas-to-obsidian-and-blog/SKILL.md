---
name: reddit-saas-to-obsidian-and-blog
description: Reddit SaaS 게시판 글을 Chrome DevTools MCP로 읽고, 요약해서 Obsidian 볼트에 저장한 후 블로그 content/에도 복사하고 git push까지 자동 배포합니다. /reddit-saas-to-obsidian-and-blog <url_or_subreddit> 로 실행.
---

# Reddit SaaS → Obsidian + Blog 자동 배포

## Overview

`reddit-saas-to-obsidian` 스킬의 모든 동작을 포함하며, Obsidian 저장 이후 **블로그 배포 단계가 추가**된다:
1. Chrome DevTools MCP로 Reddit SaaS 데이터 수집 & 비판적 분석
2. **Obsidian 볼트** `reddit-saas/{YYYY-MM-DD_HHmm}/{subreddit}.md` 저장
3. **블로그** `C:/Users/rollrat/Desktop/agents/content/reddit-saas/{YYYY-MM-DD_HHmm}/{subreddit}.md` 복사
4. `git add → commit → push` 자동 배포 → GitHub Actions가 사이트 자동 빌드

## Usage

```
/reddit-saas-to-obsidian-and-blog <reddit_url_or_subreddit> [options]
```

### Options
- `<url>`: 특정 Reddit 게시물 URL (단일 글 요약)
- `<subreddit>`: 서브레딧 이름 (예: SaaS, microsaas)
- `--top <n>`: 수집할 게시물 수 (기본: 10)
- `--sort <type>`: 정렬 방식 - hot, new, top (기본: hot)
- `--no-push`: git commit만 하고 push는 생략

## Critical Rules

### Chrome MCP 에러 처리
**Chrome DevTools MCP 접근이 실패하면 즉시 사용자에게 에러 메시지를 출력하고 중단한다.** WebFetch 등 다른 도구로 우회하지 않는다.

### 날짜 처리 (필수)
**가장 먼저 Bash로 `date "+%Y-%m-%d_%H%M"` 명령을 실행하여 실제 현재 시간을 확인한다.** 절대 추론하거나 추정하지 않는다.

### 문서 생성 규칙
- **글마다 개별 문서를 만들지 않는다**
- **모든 글을 하나의 총 요약 문서로 합쳐서 생성한다**
- 파일명은 **날짜+시간** 형식: `{YYYY-MM-DD_HHmm}/{subreddit}.md`

## Workflow

### 0. 현재 시간 확인 (필수)

Bash로 `date "+%Y-%m-%d_%H%M"` 실행. 이 값을 모든 경로에 사용.

### 1. Chrome DevTools MCP 연결 확인

`list_pages`를 호출하여 Chrome MCP 연결 상태를 확인. 실패 시 에러 출력 후 즉시 중단.

### 2. Chrome DevTools MCP로 Reddit 데이터 수집

Reddit JSON API를 Chrome DevTools MCP를 통해 접근:
- 서브레딧 모드: `https://www.reddit.com/r/{subreddit}/hot.json?limit=10`
- 특정 글 모드: `https://www.reddit.com/r/{subreddit}/comments/{id}.json`

1. `navigate_page`로 JSON URL 이동
2. `evaluate_script`로 JSON 파싱하여 게시물 목록 추출
3. 각 게시물의 댓글 JSON URL로 이동하여 상위 댓글 추출

### 3. 데이터 추출 대상

각 게시물에서:
- **제목** (title) - 영어 원문 그대로
- **원문 URL** (permalink)
- **작성자** (author)
- **작성일** (created_utc)
- **업보트 수** (score)
- **본문 내용** (selftext) - 최대 1500자. 링크 포스트면 URL도 포함
- **댓글 수** (num_comments)
- **상위 댓글 10개**: 작성자, 내용(최대 300자), 점수
- **게시물 flair/태그**
- 링크/제품 URL, WHOIS/SimilarWeb 등 사기 적발 증거

### 4. 총 요약 문서 생성

추출한 모든 게시물 데이터를 분석하여 **하나의 요약 문서**로 생성.

#### 마크다운 템플릿

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

---

## 2. {이모지} {다음 게시물}...

(모든 게시물 반복. 점수 높은 순서대로 정렬)

---

## 🔍 메타 분석: r/{서브레딧} 커뮤니티 현재 트렌드

### 1. {트렌드 제목}
{전체 게시물을 관통하는 패턴/합의/갈등. 2-3문장.}

---

## 🔗 언급된 도구 & 서비스
- [{도구명}]({URL}) - {간단 설명}
```

#### 작성 가이드라인

- **링크와 표 사이에 반드시 빈 줄을 넣는다** (Obsidian 마크다운 파서 요구사항)
- 헤더 이모지: 🚀 런칭, 💀 사기적발, ⚠️ 경고, 💼 전략, 🔧 기술, ⚙️ 도구비교, 📢 교훈, 💰 매출
- 프로모션 의도 명시적으로 지적
- AI 생성 콘텐츠 의심 시 언급
- 사기/가짜 글 적발 증거 상세 기록
- 실패 경험, 구체적 숫자, 반직관적 조언이 있는 댓글 우선 포함

### 5. Obsidian에 저장

Obsidian MCP의 `write_note` 도구로 볼트에 저장:
- **경로**: `reddit-saas/{YYYY-MM-DD_HHmm}/{subreddit}.md`

### 6. 블로그 content/ 폴더 저장

Obsidian에 저장한 것과 **동일한 내용**을 블로그 content 폴더에도 저장:

```python
import os

blog_dir = 'C:/Users/rollrat/Desktop/agents/content/reddit-saas/{YYYY-MM-DD_HHmm}'
os.makedirs(blog_dir, exist_ok=True)
blog_path = f'{blog_dir}/{subreddit}.md'

with open(blog_path, 'w', encoding='utf-8') as f:
    f.write(full_content)  # frontmatter + 요약 본문 동일 내용
```

멀티 채널 수집 시 `summary.md`도 동일하게 복사한다.

### 7. Git commit + push

```bash
cd /c/Users/rollrat/Desktop/agents

git add "content/reddit-saas/{YYYY-MM-DD_HHmm}/"

git commit -m "content: r/{subreddit} SaaS 분석 추가 ({YYYY-MM-DD_HHmm})

출처: https://www.reddit.com/r/{subreddit}
수집: {posts_count}개 게시물"

# --no-push 옵션이 없을 때만 push
git push origin main
```

### 8. 정리 및 완료 보고

```
✅ 완료

📡 r/{subreddit} SaaS 분석
📁 Obsidian: reddit-saas/{YYYY-MM-DD_HHmm}/{subreddit}.md
📁 블로그:   content/reddit-saas/{YYYY-MM-DD_HHmm}/{subreddit}.md
🚀 GitHub Actions 배포 시작됨
```

## 인자 없이 실행 시 동작

```
📡 Reddit SaaS 수집 가능한 기본 채널:

  SaaS          — SaaS 전반 (런칭, MRR 공유, 전략)
  microsaas     — 1인/소규모 SaaS, 사이드프로젝트 수익화
  indiehackers  — 인디 개발자, 온라인 비즈니스 전반
  buildinpublic — 공개 빌딩 과정, 진행 상황 공유
  IMadeThis     — 직접 만든 프로젝트 쇼케이스
  selfhosted    — 셀프호스팅, SaaS 대안 비교
  logistics     — 물류 업계 소프트웨어, 운송, 3PL, TMS
  supplychain   — 공급망 관리, 디맨드 플래닝, ERP, 재고

사용법:
  /reddit-saas-to-obsidian-and-blog SaaS              — r/SaaS 인기글 10개 수집 + 블로그 배포
  /reddit-saas-to-obsidian-and-blog microsaas --top 5 — r/microsaas 5개 수집 + 블로그 배포
  /reddit-saas-to-obsidian-and-blog <Reddit URL>      — 특정 게시물 하나 수집 + 블로그 배포
  /reddit-saas-to-obsidian-and-blog SaaS --no-push    — push 생략
```

## 멀티 채널 수집 후 종합 요약 (summary.md)

2개 이상의 서브레딧을 수집한 경우, 모든 개별 채널 문서 저장 완료 후 Task 도구로 `general-purpose` 서브에이전트를 실행하여 `summary.md`를 생성한다.

서브에이전트 완료 후 `summary.md`도 블로그 content 폴더에 복사하고, 전체 폴더를 한 번에 git commit + push한다.

## Error Handling

- **Chrome MCP 연결 실패**: 에러 메시지 출력 후 **즉시 중단**. 다른 도구로 우회하지 않음.
- **Reddit 접근 불가**: 로그인 필요 시 안내, rate limit 시 안내 후 중단
- **content/ 폴더 없음**: `os.makedirs`로 자동 생성
- **git push 실패**: 에러 출력 후 "Obsidian/content 저장은 완료됨, 수동 push 필요" 안내
