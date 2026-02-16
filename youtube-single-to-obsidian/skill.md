---
name: youtube-single-to-obsidian
description: 단일 YouTube 영상을 자막 기반으로 요약하여 Obsidian 볼트의 youtube/{영상제목}.md 에 저장합니다. /youtube-single-to-obsidian <url> 로 실행.
---

# YouTube Single to Obsidian - 단일 영상 요약 → 옵시디언 저장

## Overview

단일 YouTube 영상의 자막을 추출하고, 에이전트로 한국어 요약을 생성한 뒤, Obsidian 볼트의 `youtube/{영상제목}.md`에 저장합니다.

## Usage

```
/youtube-single-to-obsidian <url> [options]
```

### Parameters
- `<url>`: YouTube 영상 URL (예: `https://www.youtube.com/watch?v=xxxxx`)

### Options
- `--lang <code>`: 자막 언어 (기본: `ko`). 자막 다운로드 언어만 변경, 요약은 항상 한국어
- `--model <model>`: 요약 에이전트 모델 (기본: `sonnet`)
- `--folder <path>`: Obsidian 저장 경로 오버라이드 (기본: `youtube/{영상제목}.md`)

## Critical Rules

### 날짜 처리 (필수)
- 현재 날짜/시간은 반드시 Bash 커맨드로 얻는다. 절대 추론하거나 추정하지 않는다.
- 파일명, frontmatter, 본문 등 모든 곳에서 커맨드 출력값만 사용한다.
- 예시:
  - `date '+%Y-%m-%d'` → 2026-02-15
  - `date '+%y.%m.%d_%H%M'` → 26.02.15_2130

### 출력 언어
- 자막이 어떤 언어이든 **요약은 항상 한국어**로 작성한다.

### 인코딩 처리 (Windows)
- yt-dlp의 stdout은 Windows에서 cp949로 출력된다.
- 반드시 Python subprocess로 실행하고, `.decode('cp949', errors='replace')`로 디코딩한다.
- 자막 json3 파일은 UTF-8이므로 별도 처리 불필요.

### 파일명 처리
- 영상 제목에서 Obsidian/파일시스템 금지 문자(`:`, `?`, `*`, `"`, `<`, `>`, `|`) 제거.
- 제목이 너무 길면 (100자 초과) 앞 100자까지만 사용.

### 파일 관리
- 임시 파일은 `C:/Users/rollrat/yt_obsidian_tmp/` 에 저장하고, 완료 후 삭제한다.

## Workflow

### 1. 환경 확인 & 입력 파싱

- yt-dlp 설치 확인. 없으면 `pip install yt-dlp`로 설치.
- URL에서 video ID 추출.

### 2. 메타데이터 수집

Python 스크립트로 영상 메타데이터를 가져온다:

```python
import subprocess, sys, json

result = subprocess.run(
    [sys.executable, '-m', 'yt_dlp', '--dump-json', '--skip-download',
     f'https://www.youtube.com/watch?v={vid}'],
    capture_output=True
)
data = json.loads(result.stdout.decode('cp949', errors='replace'))
meta = {
    'id': data.get('id'),
    'title': data.get('title'),
    'upload_date': data.get('upload_date'),
    'duration': data.get('duration'),
    'description': data.get('description', '')[:1000],
    'channel': data.get('channel'),
}
# JSON 파일로 저장
with open(f'{tmp_dir}/meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
```

메타데이터 JSON은 Read 도구로 읽어서 한글 제목 등을 확인한다 (stdout cp949 깨짐 방지).

### 3. 자막 다운로드

```python
subprocess.run([
    sys.executable, '-m', 'yt_dlp',
    '--write-auto-sub', '--sub-lang', lang,
    '--skip-download', '--sub-format', 'json3',
    '-o', f'{tmp_dir}/{vid}.%(ext)s',
    f'https://www.youtube.com/watch?v={vid}'
], capture_output=True)
```

### 4. 자막 → 텍스트 변환

json3 자막에서 텍스트를 추출:

```python
import json, re

with open(f'{tmp_dir}/{vid}.{lang}.json3', 'r', encoding='utf-8') as f:
    data = json.load(f)

texts = []
for event in data.get('events', []):
    segs = event.get('segs', [])
    line = ''.join(s.get('utf8', '') for s in segs).strip()
    if line and line != '\n':
        texts.append(line)

full_text = re.sub(r'\s+', ' ', ' '.join(texts)).strip()

with open(f'{tmp_dir}/{vid}.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)
```

자막이 없는 영상은 제목+설명으로 간략 요약 처리.

### 5. 요약 에이전트 실행

Task 에이전트를 `run_in_background: true`로 실행한다.

에이전트 프롬프트 템플릿:

```
{tmp_dir}/{vid}.txt 파일의 자막 텍스트를 읽어라.

이것은 유튜브 영상이다:
- 제목: {title}
- 업로드: {upload_date}
- 길이: {duration}분
- Video ID: {vid}
- 설명: {description}

아래 형식으로 **한국어** 요약을 작성하라 (마크다운만 출력, 다른 코멘트 없이):

## {title}
> 📅 {upload_date} | ⏱️ {duration}분 | [영상 링크](https://www.youtube.com/watch?v={vid})

### 핵심 요약
(3-5개 bullet point로 핵심 내용)

### 주요 내용
(영상 설명에 챕터/타임코드가 있으면 그에 맞춰 상세 요약. 없으면 자체적으로 주제별 구분. 핵심 수치, 사실, 논거 포함)

### Q&A
(시청자가 영상을 보고 궁금해할 만한 질문 3가지를 선정하고, 각각 간략하게 답변. 영상 내용과 일반 지식을 종합하여 답변 작성)

**Q1. {질문1}**
{답변1 - 3~5문장}

**Q2. {질문2}**
{답변2 - 3~5문장}

**Q3. {질문3}**
{답변3 - 3~5문장}

### 키워드
(쉼표로 구분된 관련 키워드/태그)
```

에이전트 완료 후 결과를 받아온다 (TaskOutput으로 대기).

### 6. Obsidian 저장

mcp__obsidian__write_note로 저장한다.

- **경로**: `youtube/{영상제목}.md` (기본) 또는 `--folder`로 오버라이드
- **frontmatter** 포함:

```yaml
title: {영상 제목}
channel: {채널명}
upload_date: {업로드 날짜}
duration: {길이}분
video_id: {vid}
tags: [youtube, ...]
```

### 7. 정리

- 임시 디렉토리 삭제: `rm -rf {tmp_dir}`
- 사용자에게 완료 보고: 저장 경로와 영상 정보

## 인자 없이 실행 시 동작

**`/youtube-single-to-obsidian`을 인자 없이 실행하면 아래 안내를 출력하고 즉시 종료한다.**

출력 형식:

```
📺 YouTube Single to Obsidian - 단일 영상 요약 → 옵시디언 저장

사용법:
  /youtube-single-to-obsidian https://www.youtube.com/watch?v=xxxxx
  /youtube-single-to-obsidian https://youtu.be/xxxxx --lang en
  /youtube-single-to-obsidian <url> --folder "youtube/과학"

옵션:
  --lang <code>     자막 언어 (기본: ko)
  --model <model>   요약 에이전트 모델 (기본: sonnet)
  --folder <path>   저장 경로 오버라이드 (기본: youtube/{영상제목}.md)

결과는 Obsidian 볼트의 youtube/{영상제목}.md 에 저장됩니다.
```

**이 안내만 출력하고 종료한다.**

## Error Handling

- **yt-dlp 미설치**: `pip install yt-dlp`로 자동 설치 후 재시도.
- **잘못된 URL**: YouTube URL 형식 확인 안내 후 중단.
- **자막 없음**: 제목+설명만으로 간략 요약. `(자막 없음 - 설명 기반 요약)` 표시.
- **에이전트 실패**: 에러 내용 출력 후 중단.
- **Obsidian 볼트 없음**: 볼트 연결 확인 안내 후 중단.
- **제목 특수문자**: 파일명 금지 문자 자동 제거.
