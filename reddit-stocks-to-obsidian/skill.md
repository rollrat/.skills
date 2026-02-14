---
name: reddit-stocks-to-obsidian
description: Reddit 금융/주식 커뮤니티 글을 Chrome DevTools MCP로 읽고, 분석해서 Obsidian 볼트에 저장합니다. /reddit-stocks-to-obsidian <url_or_subreddit> 로 실행.
---

# Reddit to Obsidian - 금융/주식 커뮤니티 분석 & 요약

## Overview

Chrome DevTools MCP를 사용하여 Reddit 금융/주식 관련 게시글과 댓글을 읽고, **하나의 총 요약 문서**로 만들어 Obsidian 볼트의 `reddit-stocks/` 폴더에 저장합니다.

## Usage

```
/reddit-stocks-to-obsidian <reddit_url_or_subreddit> [options]
```

### Options
- `<url>`: 특정 Reddit 게시물 URL (단일 글 분석)
- `<subreddit>`: 서브레딧 이름 (예: wallstreetbets, stocks) - 상위 인기글 수집
- `--top <n>`: 수집할 게시물 수 (기본: 10)
- `--sort <type>`: 정렬 방식 - hot, new, top (기본: hot)
- `--folder <name>`: Obsidian 저장 폴더 (기본: reddit-stocks)

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
- 파일명은 **날짜+시간** 형식: `reddit-stocks/{YYYY-MM-DD_HHmm}/{subreddit}.md`
  - 예: `reddit-stocks/2026-02-14_1530/wallstreetbets.md`

### 투자 조언 면책
**생성되는 문서는 정보 정리 목적이며, 투자 조언이 아니다.** 문서 하단에 면책 문구를 반드시 포함한다.

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
- **본문 내용** (selftext) - 최대 2000자. DD(Due Diligence) 글은 길이가 길므로 SaaS보다 더 많이 가져옴
- **댓글 수** (num_comments)
- **상위 댓글 10개**: 작성자, 내용(최대 400자), 점수
- **게시물 flair/태그** — DD, YOLO, Gain, Loss, Discussion, News, Meme 등 WSB 플레어 중요

**본문 추출 시 주의:**
- **티커 심볼** ($GME, $TSLA 등)은 반드시 추출. 본문과 댓글 모두에서 수집
- **포지션 정보**: 콜/풋, 행사가(strike), 만기일(expiry), 수량, 진입가가 있으면 반드시 추출
- **수익/손실 금액**: 구체적 달러/퍼센트 숫자가 있으면 추출
- **차트/이미지 링크**: imgur, reddit gallery 등 이미지 URL 보존 (DD의 차트 증거)
- **외부 소스 링크**: SEC 파일링, 뉴스 기사, 재무제표 등 DD 근거 자료

### 4. 총 요약 문서 생성

추출한 모든 게시물 데이터를 분석하여 **하나의 요약 문서**로 생성한다.

Obsidian 볼트 경로: `C:\Users\rollrat\Documents\Obsidian Vault`

파일 경로: `reddit-stocks/{YYYY-MM-DD_HHmm}/{subreddit}.md`

#### 마크다운 템플릿

**중요: 아래 형식을 정확히 따른다. 단순 요약이 아니라 비판적 금융 분석을 포함해야 한다.**

```markdown
---
title: "r/{서브레딧} 금융 분석 - {날짜 시간}"
subreddit: "{서브레딧}"
date_saved: "{YYYY-MM-DD HH:mm}"
posts_count: {수집 게시물 수}
tags:
  - reddit
  - stocks
  - finance
  - digest
---

# r/{서브레딧} 금융 분석 - {YYYY-MM-DD HH:mm}

## 📊 오늘의 센티먼트 요약

| 지표 | 값 |
|------|------|
| 전체 분위기 | {🟢 강세 / 🔴 약세 / 🟡 혼조 / ⚪ 중립} |
| 가장 많이 언급된 종목 | {$TICKER1, $TICKER2, $TICKER3} |
| 핵심 테마 | {1줄 요약} |

---

## 1. {이모지} {한국어 요약 제목} (⬆{점수}, 💬{댓글수})
[{영어 원문 제목}]({Reddit permalink})

| 항목 | 내용 |
|------|------|
| 종목/자산 | {$TICKER 또는 자산명} |
| 포지션/방향 | {🟢 롱/콜 / 🔴 숏/풋 / ⚪ 관망 / 📊 분석만} |
| 핵심 논지 | {1-2문장 요약} |
| 포지션 상세 | {콜/풋, 행사가, 만기일, 수량 — 있는 경우만} |
| 수익/손실 | {금액/퍼센트 — 있는 경우만} |
| DD 품질 | {⭐⭐⭐⭐⭐ 5점 만점 평가 — DD 글인 경우만} |

댓글 핵심:
- {핵심 댓글 인용 또는 요약} (⬆{점수}) — {부연 설명}
- {반대 포지션 의견이 있으면 반드시 포함}
- {펌프앤덤프/쉴링 의심 시 적극 지적}

---

## 2. {이모지} {다음 게시물}...

(모든 게시물 반복. 점수 높은 순서대로 정렬)

---

## 📈 메타 분석: r/{서브레딧} 시장 센티먼트

### 1. {트렌드 제목}
{전체 게시물에서 반복되는 패턴/합의/갈등을 분석. 2-3문장.}

### 2. {트렌드 제목}
{구체적 예시와 함께 설명}

### 3. {트렌드 제목}
...

(3-5개 트렌드 도출)

---

## 🏷️ 종목 언급 빈도

| 종목 | 언급 횟수 | 센티먼트 | 맥락 |
|------|----------|----------|------|
| {$TICKER} | {N회} | {🟢/🔴/🟡} | {한줄 요약} |
| ... | ... | ... | ... |

(본문 + 댓글에서 언급된 모든 티커 심볼을 집계)

---

## ⚠️ 리스크 & 주의사항
- {커뮨니티에서 과열/FOMO 징후가 보이면 경고}
- {펌프앤덤프 의심 종목이 있으면 명시}
- {DD의 논리적 허점이나 빠진 리스크 요인}

---

> **면책:** 이 문서는 Reddit 커뮤니티 게시물의 정리 목적으로 생성되었으며, 투자 조언이 아닙니다. 모든 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
```

#### 작성 가이드라인

**게시물별 작성 규칙:**
- **링크와 표 사이에 반드시 빈 줄을 넣는다.** Obsidian 마크다운 파서는 이전 블록과 표 사이에 빈 줄이 없으면 표를 렌더링하지 않는다. `[제목](URL)` 바로 다음 줄에 `| 항목 |`이 오면 안 되고, 반드시 한 줄 띄어야 한다.
- 헤더에 게시물 성격을 나타내는 이모지 포함:
  - 📈 강세 분석/DD
  - 📉 약세 분석/숏 DD
  - 🚀 YOLO/올인 포지션
  - 💰 수익 인증 (Gain)
  - 💀 손실 인증 (Loss)
  - 📊 중립 분석/데이터
  - 🔥 밈/유머
  - ⚠️ 경고/리스크 알림
  - 📰 뉴스/이벤트
  - 🏦 매크로 경제
  - 🤖 알고리즘/퀀트
  - 💎 다이아몬드 핸즈 (장기 홀딩)
  - 🐻 베어 마켓 관점
  - 🐂 불 마켓 관점

**DD(Due Diligence) 품질 평가 기준 (⭐1-5):**
- ⭐: 논지만 있고 근거 없음. "trust me bro" 수준
- ⭐⭐: 기본적 논리는 있으나 데이터/소스 부족
- ⭐⭐⭐: 재무 데이터 인용, 차트 분석 포함. 읽을 가치 있음
- ⭐⭐⭐⭐: SEC 파일링, 기관 보유량, 산업 분석 등 다층 근거. 높은 품질
- ⭐⭐⭐⭐⭐: 독자적 리서치, 데이터 크로스체크, 반론 고려까지 포함. 기관급

**포지션/수익 검증 규칙:**
- 스크린샷 없는 수익/손실 주장은 "미검증"으로 표시
- 포지션 스크린샷이 있어도 날짜/금액 일관성 확인
- "나는 X주 보유 중"이라는 주장만으로 검증된 것으로 보지 않음

**펌프앤덤프/쉴링 감지 규칙:**
- 신규 계정(30일 미만)이 특정 종목을 강하게 추천하면 경고
- OP의 포스트 히스토리에서 같은 종목 반복 홍보 패턴 체크
- 소형주/페니스탁 + 과도한 이모지 + "이건 다음 GME" 류 표현 = 높은 쉴링 확률
- 댓글에서 "bot", "shill", "pump" 지적이 있으면 반드시 기록
- 특정 종목 글에 비정상적으로 많은 어워드 → 유료 프로모션 의심

**댓글 분석 규칙:**
- 단순 "to the moon 🚀" 류 댓글은 생략
- **반대 포지션** 의견은 반드시 포함 (롱 글에 숏 근거, 숏 글에 롱 근거)
- 구체적 숫자(목표가, 지지선/저항선, P/E, 공매도 비율 등)가 있는 댓글 우선
- 실제 포지션을 공개한 댓글 우선 ("$50C 3/21 holding 100 contracts")
- 기관/내부자 매매 정보를 인용하는 댓글 우선
- 과거 예측이 맞았다/틀렸다는 후속 보고 댓글 포함

**메타 분석 규칙:**
- 개별 글 요약이 아니라, 전체 게시물을 관통하는 **시장 센티먼트 패턴**을 도출
- 강세/약세 비율, 섹터별 관심도, 매크로 이벤트 반응을 분석
- 커뮈니티가 과열(FOMO)인지 공포(FUD)인지 판단
- "반대 지표"로서의 가치 평가 (WSB 합의의 반대가 정답인 경우가 많음)
- 옵션 만기일(OPEX), FOMC, 어닝 시즌 등 다가오는 이벤트와의 연결
- 구체적 게시물을 예시로 인용하며 근거 제시

**종목 언급 빈도 집계 규칙:**
- 본문과 댓글 모두에서 $TICKER 패턴 또는 종목명을 추출
- ETF($SPY, $QQQ 등)와 개별 종목 구분
- 각 종목의 센티먼트(강세/약세/혼조)를 다수 의견 기준으로 판정
- 3회 이상 언급된 종목만 테이블에 포함

## Examples

```bash
# 특정 게시물 하나 분석
/reddit-stocks-to-obsidian https://www.reddit.com/r/wallstreetbets/comments/abc123/gme_dd_the_moass_thesis/

# r/wallstreetbets 인기글 10개 수집 (기본)
/reddit-stocks-to-obsidian wallstreetbets

# r/stocks 최신글 15개 수집
/reddit-stocks-to-obsidian stocks --top 15 --sort new

# r/options 인기글 수집
/reddit-stocks-to-obsidian options
```

## 인자 없이 실행 시 동작 (기본 채널 안내)

**`/reddit-stocks-to-obsidian`을 인자 없이 실행하면 수집하지 않고, 아래 기본 서브레딧 목록을 출력한다.**

출력 형식 (정확히 이대로 출력):

```
📈 Reddit 금융/주식 수집 가능한 기본 채널:

  wallstreetbets  — YOLO, 밈주식, 옵션, DD, 손익 인증
  stocks          — 주식 전반, 중장기 투자, 뉴스 토론
  options         — 옵션 전략, 그릭스, 스프레드
  investing       — 장기 투자, 포트폴리오, ETF, 배당
  stockmarket     — 시장 분석, 뉴스, 섹터 동향
  economy         — 거시경제, 금리, 인플레이션, 고용지표
  dividends       — 배당주, 배당 성장, DRIP 전략
  SecurityAnalysis— 가치투자, 재무제표 분석, DCF

사용법:
  /reddit-stocks-to-obsidian wallstreetbets              — r/wallstreetbets 인기글 10개 수집
  /reddit-stocks-to-obsidian stocks --top 5              — r/stocks 5개 수집
  /reddit-stocks-to-obsidian options --sort new           — 최신글 기준 수집
  /reddit-stocks-to-obsidian <Reddit URL>                 — 특정 게시물 하나 수집
  /reddit-stocks-to-obsidian 기본 채널 수집해줘           — 위 8개 채널 전체 수집
```

**이 안내만 출력하고 종료한다. Chrome MCP 연결, 데이터 수집 등 어떤 동작도 하지 않는다.**

## Implementation Notes

Claude가 이 skill을 실행할 때:

0. **인자 확인**: 인자가 없으면 위의 "기본 채널 안내"를 출력하고 즉시 종료. 이하 단계를 실행하지 않는다.
1. **Chrome DevTools MCP 연결 확인**: `list_pages` 호출. 실패 시 에러 출력 후 중단.
2. **Chrome DevTools MCP로 Reddit JSON API 접근**: `navigate_page`로 JSON URL 이동, `evaluate_script`로 데이터 추출.
3. **비판적 금융 분석 요약 생성**: 추출된 데이터를 분석하여 한국어로 요약. 단순 정리가 아닌 **비판적 금융 시각** 포함:
   - 펌프앤덤프/쉴링 감지 및 명시
   - DD 품질 평가 (⭐1-5)
   - 포지션/수익 주장의 검증 여부 표시
   - 반대 포지션 의견 균형 있게 포함
   - 센티먼트 과열/공포 판단
   - 종목 언급 빈도 집계
   - 커뮤니티 전체 시장 센티먼트 메타 분석
4. **게시물 정렬**: 점수(score) 높은 순서대로 정렬하여 문서 작성.
5. **Obsidian에 저장**: Obsidian MCP의 `write_note` 도구를 사용하여 볼트에 저장. **파일명의 날짜+시간은 반드시 Bash `date "+%Y-%m-%d_%H%M"` 명령으로 실제 현재 시간을 확인한 후 사용한다.** 추측이나 임의 시간을 넣지 않는다.
6. **종합 요약 생성 (멀티 채널 수집 시에만)**: 2개 이상 서브레딧을 수집한 경우, 모든 개별 문서 저장 완료 후 Task 도구로 `general-purpose` 서브에이전트를 실행하여 `summary.md`를 생성한다. 위의 "멀티 채널 수집 후 종합 요약" 섹션의 프롬프트와 템플릿을 따른다. 서브에이전트에게 실제 폴더 경로(날짜+시간)를 정확히 전달한다.

### Reddit JSON API 활용

Reddit URL 뒤에 `.json`을 붙이면 JSON 데이터를 얻을 수 있습니다:
- 게시물: `https://www.reddit.com/r/wallstreetbets/hot.json?limit=10`
- 특정 글: `https://www.reddit.com/r/wallstreetbets/comments/{id}.json`

Chrome DevTools로 이 JSON URL에 접근하여 `evaluate_script`로 파싱합니다.

## 멀티 채널 수집 후 종합 요약 (summary.md)

**여러 서브레딧을 한 번에 수집했을 때 (예: "기본 채널 수집해줘"), 모든 개별 채널 문서 저장이 완료된 후 반드시 summary.md를 생성한다.**

### 트리거 조건
- 2개 이상의 서브레딧을 수집한 경우 자동 실행
- 단일 서브레딧/단일 URL 수집 시에는 실행하지 않음

### 실행 방법

**모든 개별 채널 .md 파일 저장이 완료된 직후**, Task 도구로 서브에이전트를 실행한다:

```
Task(
  subagent_type: "general-purpose",
  description: "Reddit 종합 요약 생성",
  prompt: 아래 프롬프트 참조
)
```

서브에이전트에게 전달할 프롬프트:

```
Obsidian 볼트의 reddit-stocks/{YYYY-MM-DD_HHmm}/ 폴더에 있는 모든 .md 파일을 읽고,
전체 채널을 관통하는 종합 요약 문서 summary.md를 같은 폴더에 생성하라.

저장 경로: reddit-stocks/{YYYY-MM-DD_HHmm}/summary.md

## 작업 순서
1. Obsidian MCP의 list_directory로 reddit-stocks/{YYYY-MM-DD_HHmm}/ 폴더 내 파일 목록 확인
2. Obsidian MCP의 read_multiple_notes로 모든 .md 파일을 읽기 (10개 제한이므로 필요 시 나눠서)
3. 아래 템플릿에 따라 summary.md 작성
4. Obsidian MCP의 write_note로 저장

## summary.md 템플릿

---
title: "Reddit 금융 종합 분석 - {날짜 시간}"
date_saved: "{YYYY-MM-DD HH:mm}"
channels: [{수집된 채널 목록}]
total_posts: {전체 게시물 수 합계}
tags:
  - reddit
  - stocks
  - finance
  - summary
---

# Reddit 금융 종합 분석 - {YYYY-MM-DD HH:mm}

## 📊 전체 시장 센티먼트 대시보드

| 채널 | 센티먼트 | 핵심 테마 |
|------|----------|----------|
| r/wallstreetbets | {🟢/🔴/🟡/⚪} | {1줄} |
| r/stocks | {🟢/🔴/🟡/⚪} | {1줄} |
| ... | ... | ... |

**종합 판정: {🟢 강세 / 🔴 약세 / 🟡 혼조}**
{전체 채널을 종합한 1-2문장 시장 분위기 판단}

---

## 🔥 크로스 채널 핵심 이슈 TOP 5

각 이슈는 2개 이상 채널에서 언급된 것만 포함. 중복 뉴스는 하나로 통합.

### 1. {이슈 제목}
- **언급 채널**: r/xxx, r/yyy, r/zzz
- **요약**: {3-5문장. 각 채널에서의 반응 차이 포함}
- **투자 시사점**: {1-2문장}

### 2. {이슈 제목}
...

(5개)

---

## 🏷️ 종합 종목 언급 빈도 (전체 채널 통합)

| 종목 | 총 언급 | 센티먼트 | 주요 채널 | 맥락 |
|------|---------|----------|----------|------|
| {$TICKER} | {N회} | {🟢/🔴/🟡} | {채널명} | {한줄} |
| ... | ... | ... | ... | ... |

(전체 채널에서 3회 이상 언급된 종목만. 언급 횟수 내림차순 정렬)

---

## 📈 채널별 온도 차이 분석

같은 이슈/종목에 대해 채널마다 반응이 다른 경우를 분석.

| 주제 | WSB | stocks | options | investing | 기타 |
|------|-----|--------|---------|-----------|------|
| {주제1} | {반응} | {반응} | {반응} | {반응} | {반응} |
| ... | ... | ... | ... | ... | ... |

---

## 🗓️ 다음 주 주요 이벤트 & 워치리스트

게시물에서 언급된 다가오는 이벤트:
- {날짜}: {이벤트} — {관련 종목/영향}
- ...

워치리스트 (강세/약세 양쪽 근거가 있는 종목):
- {$TICKER}: {강세 근거 vs 약세 근거}
- ...

---

## ⚠️ 종합 리스크 경고
- {전체 채널에서 반복되는 리스크 요인}
- {채널 간 모순되는 시그널이 있으면 명시}
- {커뮤니티 과열/공포 징후}

---

## 📋 개별 채널 문서 링크

| 채널 | 문서 |
|------|------|
| r/wallstreetbets | [[wallstreetbets]] |
| r/stocks | [[stocks]] |
| ... | ... |

(Obsidian 내부 링크 [[파일명]] 형식 사용)

---

> **면책:** 이 문서는 Reddit 커뮤니티 게시물의 정리 목적으로 생성되었으며, 투자 조언이 아닙니다. 모든 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.

## 작성 핵심 원칙
- 개별 채널 문서의 단순 복붙이 아니라, **채널을 관통하는 패턴과 모순**을 도출
- 같은 뉴스(예: CPI)가 여러 채널에 있으면 하나로 통합하되, 채널별 반응 차이를 비교
- 종목 언급 빈도는 모든 채널의 데이터를 합산하여 재집계
- Obsidian 내부 링크로 개별 채널 문서 연결
- 한국어로 작성
```

**중요: 서브에이전트 프롬프트의 {YYYY-MM-DD_HHmm} 부분은 실제 폴더명으로 치환하여 전달한다.**

## Error Handling

- **Chrome MCP 연결 실패**: 에러 메시지 출력 후 **즉시 중단**. 다른 도구로 우회하지 않음.
- **Reddit 접근 불가**: 로그인 필요 시 안내, rate limit 시 안내 후 중단
- **Obsidian 볼트 없음**: 볼트 경로 확인 안내
