---
name: youtube-single-to-obsidian-and-blog
description: 단일 YouTube 영상을 자막 기반으로 요약하여 Obsidian 볼트와 블로그 content/youtube/ 폴더에 동시 저장하고 git commit+push까지 자동 수행합니다. /youtube-single-to-obsidian-and-blog <url> 로 실행.
---

# YouTube Single → Obsidian + Blog 자동 배포

## Overview

단일 YouTube 영상의 자막을 추출하고, **현재 세션에서 직접** 한국어 요약을 생성한 뒤:
1. **Obsidian 볼트** `youtube/{영상제목}.md` 저장
2. **블로그** `C:/Users/rollrat/Desktop/agents/content/youtube/{영상제목}.md` 복사
3. `git add → commit → push` 자동 배포 → GitHub Actions가 사이트 자동 빌드

## Usage

```
/youtube-single-to-obsidian-and-blog <url> [options]
```

### Parameters
- `<url>`: YouTube 영상 URL (예: `https://www.youtube.com/watch?v=xxxxx`)

### Options
- `--lang <code>`: 자막 언어 (기본: `ko`)
- `--no-push`: git commit만 하고 push는 생략

## Critical Rules

### 날짜 처리 (필수)
- 현재 날짜/시간은 반드시 Bash 커맨드로 얻는다. 절대 추론하거나 추정하지 않는다.
- 파일명, frontmatter, 본문 등 모든 곳에서 커맨드 출력값만 사용한다.

### 출력 언어
- 자막이 어떤 언어이든 **요약은 항상 한국어**로 작성한다.

### 인코딩 처리 (Windows) — 중요
- yt-dlp stdout 디코딩은 **반드시 utf-8 먼저 시도**, 실패 시 cp949 fallback.
- `cp949` 고정 사용 금지 — 이모지 포함 제목에서 `UnicodeEncodeError` 발생함.
- 자막 json3 파일은 UTF-8이므로 별도 처리 불필요.

```python
try:
    raw = result.stdout.decode('utf-8')
except UnicodeDecodeError:
    raw = result.stdout.decode('cp949', errors='replace')
```

### 경로 처리 (Windows)
- Python 스크립트 내 모든 경로는 `C:/Users/rollrat/...` 형식 사용.
- `/c/Users/...` (Git Bash 형식) 금지 — Python `open()`에서 작동하지 않음.
- Bash 커맨드(git 등)에서는 `C:/Users/rollrat/Desktop/agents` 그대로 사용.

### 파일명 처리
- 영상 제목에서 파일시스템 금지 문자(`:`, `?`, `*`, `"`, `<`, `>`, `|`, `\`) 제거.
- 제목이 100자 초과 시 앞 100자까지만 사용.
- **Obsidian 경로와 content/ 경로에 동일한 정제된 파일명을 사용한다.**

### 파일 관리
- 임시 파일은 `C:/Users/rollrat/yt_obsidian_tmp/` 에 저장하고, 완료 후 삭제한다.

### 블로그 저장 경로
- 항상 `C:/Users/rollrat/Desktop/agents/content/youtube/{정제된파일명}.md`
- 서브폴더 없이 youtube/ 바로 아래 저장 (채널별 폴더 없음)

## Workflow

### 1. 환경 확인 & 입력 파싱

- yt-dlp 설치 확인. 없으면 `pip install yt-dlp`로 설치.
- URL에서 video ID 추출.
- `--no-push` 옵션 여부 확인.

### 2. 메타데이터 + 자막 한 번에 다운로드 (yt-dlp 단일 호출)

**yt-dlp를 두 번 호출하지 않는다.** `--dump-json`과 `--write-auto-sub`를 동시에 실행한다.

```python
import subprocess, sys, json, re, os

vid = 'VIDEO_ID'
lang = 'ko'
tmp_dir = 'C:/Users/rollrat/yt_obsidian_tmp'
os.makedirs(tmp_dir, exist_ok=True)

result = subprocess.run(
    [sys.executable, '-m', 'yt_dlp',
     '--dump-json',
     '--write-auto-sub', '--sub-lang', lang,
     '--skip-download', '--sub-format', 'json3',
     '-o', f'{tmp_dir}/{vid}.%(ext)s',
     f'https://www.youtube.com/watch?v={vid}'],
    capture_output=True
)

# utf-8 우선, 실패 시 cp949 fallback (이모지 포함 제목 대응)
try:
    raw = result.stdout.decode('utf-8')
except UnicodeDecodeError:
    raw = result.stdout.decode('cp949', errors='replace')

data = json.loads(raw)
meta = {
    'id': data.get('id'),
    'title': data.get('title'),
    'upload_date': data.get('upload_date'),
    'duration': round(data.get('duration', 0) / 60, 1),
    'description': data.get('description', '')[:1000],
    'channel': data.get('channel'),
}
with open(f'{tmp_dir}/meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
```

메타데이터 JSON은 **Read 도구로 읽어서** 한글 제목 등을 확인한다 (stdout 깨짐 방지).

파일명 정제:
```python
safe_title = re.sub(r'[\\/:*?"<>|]', '', meta['title']).strip()
safe_title = safe_title[:100] if len(safe_title) > 100 else safe_title
```

### 3. 자막 → 텍스트 변환

```python
with open(f'{tmp_dir}/{vid}.{lang}.json3', 'r', encoding='utf-8') as f:
    sub_data = json.load(f)

texts = []
for event in sub_data.get('events', []):
    segs = event.get('segs', [])
    line = ''.join(s.get('utf8', '') for s in segs).strip()
    if line and line != '\n':
        texts.append(line)

full_text = re.sub(r'\s+', ' ', ' '.join(texts)).strip()

with open(f'{tmp_dir}/{vid}.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)
```

자막이 없는 영상은 제목+설명으로 간략 요약 처리.

### 4. 요약 — 현재 세션에서 직접 작성

**Task 에이전트를 사용하지 않는다.** `{tmp_dir}/{vid}.txt`를 Read 도구로 읽은 뒤, 현재 Claude가 직접 아래 형식으로 요약한다.

```
## {title}
> 📅 {upload_date} | ⏱️ {duration}분 | [영상 링크](https://www.youtube.com/watch?v={vid})

### 핵심 요약
(3-5개 bullet point로 핵심 내용)

### 주요 내용
(영상 설명에 챕터/타임코드가 있으면 그에 맞춰 상세 요약. 없으면 자체적으로 주제별 구분. 핵심 수치, 사실, 논거 포함)

### Q&A
(시청자가 영상을 보고 궁금해할 만한 질문 3가지를 선정하고, 각각 간략하게 답변)

**Q1. {질문1}**
{답변1 - 3~5문장}

**Q2. {질문2}**
{답변2 - 3~5문장}

**Q3. {질문3}**
{답변3 - 3~5문장}

### 키워드
(쉼표로 구분된 관련 키워드/태그)
```

### 5. Obsidian 저장

`mcp__obsidian__write_note`로 저장한다.

- **경로**: `youtube/{safe_title}.md`
- **frontmatter**:

```yaml
title: {영상 제목}
channel: {채널명}
upload_date: {업로드 날짜}
duration: {길이}분
video_id: {vid}
tags:
  - youtube
  - {채널명_태그}
```

### 6. 블로그 content/ 폴더 저장

Obsidian에 저장한 것과 **동일한 내용(frontmatter + 본문)**을 블로그 content 폴더에도 저장한다.

```python
blog_dir = 'C:/Users/rollrat/Desktop/agents/content/youtube'
os.makedirs(blog_dir, exist_ok=True)
blog_path = f'{blog_dir}/{safe_title}.md'

with open(blog_path, 'w', encoding='utf-8') as f:
    f.write(full_content)  # frontmatter + summary_body 조합
```

### 7. Git commit + push

```bash
cd "C:/Users/rollrat/Desktop/agents"

git add "content/youtube/{safe_title}.md"

git commit -m "content: {title} 추가

출처: https://www.youtube.com/watch?v={vid}
채널: {channel}
업로드: {upload_date}"

# --no-push 옵션이 없을 때만 push
git push origin main
```

### 8. 정리

- 임시 디렉토리 삭제: `rm -rf C:/Users/rollrat/yt_obsidian_tmp`
- 사용자에게 완료 보고:

```
✅ 완료

📺 {title}
📁 Obsidian: youtube/{safe_title}.md
📁 블로그:   content/youtube/{safe_title}.md
🚀 GitHub Actions 배포 시작됨
```

## 인자 없이 실행 시 동작

**`/youtube-single-to-obsidian-and-blog`를 인자 없이 실행하면 아래 안내를 출력하고 즉시 종료한다.**

```
📺 YouTube Single → Obsidian + Blog 자동 배포

사용법:
  /youtube-single-to-obsidian-and-blog https://www.youtube.com/watch?v=xxxxx
  /youtube-single-to-obsidian-and-blog https://youtu.be/xxxxx --lang en
  /youtube-single-to-obsidian-and-blog <url> --no-push

옵션:
  --lang <code>   자막 언어 (기본: ko)
  --no-push       commit만 하고 push 생략

결과:
  1. Obsidian 볼트 youtube/{영상제목}.md 저장
  2. content/youtube/{영상제목}.md 복사
  3. git commit + push → GitHub Actions 자동 배포
```

## Error Handling

- **yt-dlp 미설치**: `pip install yt-dlp`로 자동 설치 후 재시도.
- **잘못된 URL**: YouTube URL 형식 확인 안내 후 중단.
- **자막 없음**: 제목+설명만으로 간략 요약. `(자막 없음 - 설명 기반 요약)` 표시.
- **git push 실패**: 에러 출력 후 "Obsidian/content 저장은 완료됨, 수동 push 필요" 안내.
- **content/ 폴더 없음**: `os.makedirs(..., exist_ok=True)`로 자동 생성.
- **동일 파일 존재**: 덮어쓰기 (최신 요약으로 업데이트).
