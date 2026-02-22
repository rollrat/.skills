---
name: dcinside-stocks-to-obsidian-and-blog
description: DCInside 주식/금융 갤러리 글을 Chrome DevTools MCP로 읽고, 분석해서 Obsidian 볼트에 저장한 후 블로그 content/에도 복사하고 git push까지 자동 배포합니다. /dcinside-stocks-to-obsidian-and-blog <url_or_gallery> 로 실행.
---

# DCInside 주식/금융 갤러리 → Obsidian + Blog 자동 배포

## Overview

DCInside 주식/금융 관련 갤러리의 인기글을 Chrome DevTools MCP로 수집하여 분석 문서를 생성하고, Obsidian과 블로그에 동시 배포한다:
1. Chrome DevTools MCP로 DCInside 갤러리 데이터 수집 & 금융 분석
2. **Obsidian 볼트** `dcinside-stocks/{YYYY-MM-DD_HHmm}/{gallery_id}.md` 저장
3. **블로그** `C:/Users/rollrat/Desktop/agents/content/dcinside-stocks/{YYYY-MM-DD_HHmm}/{gallery_id}.md` 복사
4. `git add → commit → push` 자동 배포 → GitHub Actions가 사이트 자동 빌드

## Usage

```
/dcinside-stocks-to-obsidian-and-blog <url_or_gallery> [options]
```

### Options
- `<url>`: 특정 DCInside 갤러리 URL (목록 또는 개별 글)
- `<gallery_id>`: 갤러리 ID (예: stockus, tenbagger, kospi)
- `--top <n>`: 수집할 게시물 수 (기본: 15)
- `--no-push`: git commit만 하고 push는 생략

## Critical Rules

### Chrome MCP 에러 처리
**Chrome DevTools MCP 접근이 실패하면 즉시 사용자에게 에러 메시지를 출력하고 중단한다.** WebFetch 등 다른 도구로 우회하지 않는다.

### 날짜 처리 (필수)
**가장 먼저 Bash로 `date "+%Y-%m-%d_%H%M"` 명령을 실행하여 실제 현재 시간을 확인한다.** 절대 추론하거나 추정하지 않는다.

### 문서 생성 규칙
- **글마다 개별 문서를 만들지 않는다**
- **모든 글을 하나의 총 요약 문서로 합쳐서 생성한다**
- 파일명은 **날짜+시간** 형식: `{YYYY-MM-DD_HHmm}/{gallery_id}.md`

### 투자 조언 면책
생성되는 문서는 정보 정리 목적이며, 투자 조언이 아니다. 문서 하단에 면책 문구를 반드시 포함한다.

## Workflow

### 0. 현재 시간 확인 (필수)

Bash로 `date "+%Y-%m-%d_%H%M"` 실행. 이 값을 모든 경로에 사용.

### 1. Chrome DevTools MCP 연결 확인

`list_pages`를 호출하여 Chrome MCP 연결 상태를 확인. 실패 시 에러 출력 후 즉시 중단.

### 2. Chrome DevTools MCP로 DCInside 갤러리 데이터 수집

DCInside는 JSON API가 없으므로 **HTML 페이지를 직접 탐색**하여 데이터를 추출한다.

#### 2-1. 갤러리 목록 페이지 접근

갤러리 URL 구성:
- 마이너 갤러리 (개념글): `https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}&exception_mode=recommend`
- 마이너 갤러리 (전체): `https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}`
- 정규 갤러리 (개념글): `https://gall.dcinside.com/board/lists/?id={gallery_id}&exception_mode=recommend`

기본 갤러리(stockus, tenbagger, kospi)는 모두 **마이너 갤러리**이며, 기본 모드는 **개념글(exception_mode=recommend)**.

1. `navigate_page`로 갤러리 목록 URL 이동
2. `evaluate_script`로 게시물 목록 추출:

```javascript
() => {
  const rows = document.querySelectorAll('.gall_list .ub-content:not(.us-post)');
  const posts = [];
  rows.forEach(row => {
    const titleEl = row.querySelector('.gall_tit a:first-child');
    const writerEl = row.querySelector('.gall_writer .nickname, .gall_writer .ip');
    const dateEl = row.querySelector('.gall_date');
    const countEl = row.querySelector('.gall_count');
    const recommendEl = row.querySelector('.gall_recommend');
    const numEl = row.querySelector('.gall_num');
    if (titleEl && titleEl.href && !titleEl.href.includes('javascript')) {
      posts.push({
        title: titleEl.textContent.trim(),
        url: titleEl.href,
        author: writerEl ? writerEl.textContent.trim() : '익명',
        date: dateEl ? dateEl.getAttribute('title') || dateEl.textContent.trim() : '',
        views: countEl ? countEl.textContent.trim() : '0',
        recommend: recommendEl ? recommendEl.textContent.trim() : '0',
        postNo: numEl ? numEl.textContent.trim() : ''
      });
    }
  });
  return posts;
}
```

3. 공지글 및 광고글 제외 (postNo가 숫자가 아닌 것 필터링)

#### 2-2. 개별 게시물 상세 수집

목록에서 추출한 각 게시물 URL로 이동하여 상세 데이터 수집:

1. `navigate_page`로 게시물 URL 이동
2. `evaluate_script`로 본문 + 댓글 추출:

```javascript
() => {
  // 본문 추출
  const contentEl = document.querySelector('.write_div');
  const content = contentEl ? contentEl.innerText.trim().substring(0, 3000) : '';

  // 추천/비추천 수
  const recEl = document.querySelector('.gall_reply_num .up_num, .btn_recommend_box .up_num, .recgall_box .red_btn .smallnum');
  const nonrecEl = document.querySelector('.gall_reply_num .down_num, .btn_recommend_box .down_num, .recgall_box .blue_btn .smallnum');
  const recommend = recEl ? recEl.textContent.trim() : '0';
  const nonRecommend = nonrecEl ? nonrecEl.textContent.trim() : '0';

  // 댓글 추출
  const commentEls = document.querySelectorAll('.reply_info .usertxt');
  const commentAuthors = document.querySelectorAll('.reply_info .nickname, .reply_info .ip');
  const comments = [];
  commentEls.forEach((el, i) => {
    const author = commentAuthors[i] ? commentAuthors[i].textContent.trim() : '익명';
    comments.push({
      author: author,
      content: el.textContent.trim().substring(0, 500)
    });
  });

  // 조회수
  const viewEl = document.querySelector('.gall_count');
  const views = viewEl ? viewEl.textContent.replace('조회', '').trim() : '0';

  return {
    content,
    recommend,
    nonRecommend,
    views,
    comments: comments.slice(0, 15)
  };
}
```

**주의**: DCInside는 댓글이 AJAX로 로딩될 수 있다. 댓글이 비어있으면 잠시 대기 후 재시도하거나, 댓글 영역이 존재하는지 확인한다. 댓글을 못 가져와도 본문 수집은 계속 진행한다.

### 3. 데이터 추출 대상

각 게시물에서:
- **제목** (title)
- **원문 URL**
- **작성자** (author) — 닉네임 또는 IP
- **작성일** (date)
- **추천 수** (recommend)
- **비추천 수** (nonRecommend)
- **조회 수** (views)
- **본문 내용** — 최대 3000자
- **댓글** — 상위 15개: 작성자, 내용(최대 500자)
- **티커 심볼** ($TSLA, 삼성전자 등) 및 종목 관련 키워드

### 4. 총 요약 문서 생성

추출한 모든 게시물 데이터를 분석하여 **하나의 요약 문서**로 생성.

#### 마크다운 템플릿

```markdown
---
title: "DCInside {갤러리명} 분석 - {날짜 시간}"
gallery: "{gallery_id}"
gallery_name: "{갤러리 한국어 이름}"
date_saved: "{YYYY-MM-DD HH:mm}"
posts_count: {수집 게시물 수}
tags:
  - dcinside
  - stocks
  - finance
  - digest
---

# DCInside {갤러리명} 분석 - {YYYY-MM-DD HH:mm}

## 📊 커뮤니티 센티먼트 요약

| 지표 | 값 |
|------|------|
| 전체 분위기 | {🟢 강세 / 🔴 약세 / 🟡 혼조 / ⚪ 중립} |
| 가장 많이 언급된 종목 | {종목1, 종목2, 종목3} |
| 핵심 테마 | {1줄 요약} |
| 커뮤니티 온도 | {🔥 과열 / 😰 공포 / 😐 평온 / 🎉 축제} |

---

## 1. {이모지} {요약 제목} (👍{추천}, 👀{조회수})
[{원문 제목}]({DCInside URL})

| 항목 | 내용 |
|------|------|
| 종목/자산 | {종목명 또는 $TICKER} |
| 포지션/방향 | {🟢 매수 / 🔴 매도 / ⚪ 관망 / 📊 분석} |
| 핵심 논지 | {1-2문장 요약} |
| 손익 현황 | {수익/손실 금액/퍼센트 — 있는 경우만} |

댓글 핵심:
- {핵심 댓글 인용 또는 요약} — {부연 설명}

---

## 📈 메타 분석: {갤러리명} 커뮤니티 동향

### 1. {트렌드 제목}
{전체 게시물에서 반복되는 패턴 분석. 2-3문장.}

---

## 🏷️ 종목 언급 빈도

| 종목 | 언급 횟수 | 센티먼트 | 맥락 |
|------|----------|----------|------|
| {종목명} | {N회} | {🟢/🔴/🟡} | {한줄 요약} |

---

## ⚠️ 리스크 & 주의사항
- {과열/FOMO 징후, 루머 의심, 정보 신뢰도 이슈 등}
- {DC 특성상 유머/과장 표현 감안 필요}

---

> **면책:** 이 문서는 DCInside 커뮤니티 게시물의 정리 목적으로 생성되었으며, 투자 조언이 아닙니다. 모든 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다. DCInside 게시물의 특성상 유머, 과장, 허위 정보가 포함될 수 있습니다.
```

#### 작성 가이드라인

- **링크와 표 사이에 반드시 빈 줄을 넣는다** (Obsidian 마크다운 파서 요구사항)
- 헤더 이모지: 📈 강세, 📉 약세, 🚀 급등, 💰 수익인증, 💀 손실인증, 📊 분석, 🔥 핫이슈, ⚠️ 경고, 📰 뉴스, 😂 유머
- DC 특유의 은어/밈을 적절히 번역하여 맥락 제공 (예: "존버" → 장기보유, "물타기" → 평단 낮추기 추가매수)
- **반대 의견** 반드시 포함
- 루머/찌라시와 팩트를 구분하여 표기
- 인증 없는 손익 주장은 "미검증"으로 표시
- DCInside 특성상 과장/유머가 많으므로 이를 감안한 분석

### 5. Obsidian에 저장

Obsidian MCP의 `write_note` 도구로 볼트에 저장:
- **경로**: `dcinside-stocks/{YYYY-MM-DD_HHmm}/{gallery_id}.md`

### 6. 블로그 content/ 폴더 저장

Obsidian에 저장한 것과 **동일한 내용**을 블로그 content 폴더에도 저장:

- **경로**: `C:/Users/rollrat/Desktop/agents/content/dcinside-stocks/{YYYY-MM-DD_HHmm}/{gallery_id}.md`
- `os.makedirs`로 디렉토리 자동 생성

멀티 갤러리 수집 시 `summary.md`도 동일하게 복사한다.

### 7. Git commit + push

```bash
cd /c/Users/rollrat/Desktop/agents

git add "content/dcinside-stocks/{YYYY-MM-DD_HHmm}/"

git commit -m "content: DCInside {갤러리명} 분석 추가 ({YYYY-MM-DD_HHmm})

출처: https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}
수집: {posts_count}개 게시물"

# --no-push 옵션이 없을 때만 push
git push origin main
```

### 8. 정리 및 완료 보고

```
✅ 완료

📊 DCInside {갤러리명} 분석
📁 Obsidian: dcinside-stocks/{YYYY-MM-DD_HHmm}/{gallery_id}.md
📁 블로그:   content/dcinside-stocks/{YYYY-MM-DD_HHmm}/{gallery_id}.md
🚀 GitHub Actions 배포 시작됨
```

## 인자 없이 실행 시 동작

인자 없이 실행하면 **기본 3개 갤러리 모두 수집**한다:

```
📊 DCInside 주식/금융 수집 기본 갤러리:

  stockus    — 미국주식 마이너갤러리 (개념글)
               https://gall.dcinside.com/mgallery/board/lists/?id=stockus&exception_mode=recommend
  tenbagger  — 텐배거 마이너갤러리 (개념글)
               https://gall.dcinside.com/mgallery/board/lists/?id=tenbagger&exception_mode=recommend
  kospi      — 코스피 마이너갤러리
               https://gall.dcinside.com/mgallery/board/lists/?id=kospi

→ 인자 없이 실행: 위 3개 갤러리 모두 자동 수집

사용법:
  /dcinside-stocks-to-obsidian-and-blog                     — 기본 3개 갤러리 모두 수집 + 블로그 배포
  /dcinside-stocks-to-obsidian-and-blog stockus             — 미주갤 개념글만 수집 + 블로그 배포
  /dcinside-stocks-to-obsidian-and-blog <DCInside URL>      — 특정 URL 수집 + 블로그 배포
  /dcinside-stocks-to-obsidian-and-blog stockus --top 5     — 5개만 수집 + 블로그 배포
  /dcinside-stocks-to-obsidian-and-blog stockus --no-push   — push 생략
```

## 기본 갤러리 URL 매핑

| gallery_id | 갤러리명 | URL | 모드 |
|-----------|---------|-----|------|
| stockus | 미국주식 마이너갤러리 | `https://gall.dcinside.com/mgallery/board/lists/?id=stockus&exception_mode=recommend` | 개념글 |
| tenbagger | 텐배거 마이너갤러리 | `https://gall.dcinside.com/mgallery/board/lists/?id=tenbagger&exception_mode=recommend` | 개념글 |
| kospi | 코스피 마이너갤러리 | `https://gall.dcinside.com/mgallery/board/lists/?id=kospi` | 전체 |

## 멀티 갤러리 수집 후 종합 요약 (summary.md)

2개 이상의 갤러리를 수집한 경우 (인자 없이 실행 시 기본 동작), 모든 개별 갤러리 문서 저장 완료 후 Task 도구로 `general-purpose` 서브에이전트를 실행하여 `summary.md`를 생성한다.

### summary.md 생성 요구사항

서브에이전트에게 전달할 프롬프트:
- 모든 개별 갤러리 분석 문서를 Obsidian MCP `read_note`로 읽기
- 교차 분석하여 종합 요약 문서 생성
- 한국/미국 시장 간 센티먼트 비교
- 공통 관심 종목 및 상반된 의견 정리

서브에이전트 완료 후 `summary.md`도 블로그 content 폴더에 복사하고, 전체 폴더를 한 번에 git commit + push한다.

## DCInside 스크래핑 주의사항

### 페이지 로딩 대기
- `navigate_page` 후 페이지가 완전히 로드될 때까지 대기
- `wait_for` 도구로 `.gall_list` 또는 `.write_div` 요소 확인 가능
- 광고/팝업이 뜰 수 있으므로 `evaluate_script`가 실패하면 한 번 더 시도

### 댓글 로딩
- DCInside 댓글은 AJAX로 별도 로딩됨
- 본문 수집 후 약간의 대기 시간이 필요할 수 있음
- 댓글이 빈 배열로 돌아오면 `evaluate_script`로 댓글 영역 재확인
- 댓글 수집 실패해도 본문 수집은 계속 진행

### 차단/제한 대응
- 너무 빠른 연속 접근 시 차단될 수 있으므로 게시물 간 자연스러운 간격 유지
- CAPTCHA나 차단 페이지가 나타나면 사용자에게 안내 후 중단
- User-Agent가 Chrome이므로 일반적으로 문제없음 (실제 Chrome 브라우저 사용)

## Error Handling

- **Chrome MCP 연결 실패**: 에러 메시지 출력 후 **즉시 중단**. 다른 도구로 우회하지 않음.
- **DCInside 접근 불가**: 차단/CAPTCHA 시 안내 후 중단
- **게시물 파싱 실패**: 해당 게시물 건너뛰고 다음 게시물 계속 수집, 완료 보고에서 실패 건수 표기
- **content/ 폴더 없음**: 디렉토리 자동 생성
- **git push 실패**: 에러 출력 후 "Obsidian/content 저장은 완료됨, 수동 push 필요" 안내
