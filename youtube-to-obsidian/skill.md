---
name: youtube-to-obsidian
description: YouTube 채널의 최근 N개 영상을 자막 기반으로 요약하여 Obsidian 볼트의 youtube/ 폴더에 주간별로 저장합니다. /youtube-to-obsidian <channel> <count> 로 실행.
---

# YouTube to Obsidian - 채널 영상 요약 → 옵시디언 저장

## Overview

YouTube 채널의 최근 N개 영상에서 자막을 추출하고, 병렬 에이전트로 각 영상을 한국어로 요약한 뒤, 주간 단위로 그룹핑하여 Obsidian 볼트에 저장합니다.

## Usage

```
/youtube-to-obsidian <channel> <count> [options]
```

### Parameters
- `<channel>`: YouTube 채널 (예: `@syukaworld`, `@3blue1brown`, 또는 채널 URL)
- `<count>`: 가져올 최근 영상 수 (예: `10`, `20`)

### Options
- `--lang <code>`: 자막 언어 (기본: `ko`). 자막 다운로드 언어만 변경, 요약은 항상 한국어
- `--model <model>`: 요약 에이전트 모델 (기본: `sonnet`)
- `--folder <name>`: Obsidian 폴더명 오버라이드 (기본: 채널명 자동 추출)

## Critical Rules

### 날짜 처리
- **현재 날짜/시간은 반드시 Bash 커맨드로 얻는다.** 절대 추론하거나 추정하지 않는다.
- `date '+%Y-%m-%d_%H%M'` 또는 `date '+%y.%m.%d'` 등으로 직접 가져온다.
- summary 파일명, frontmatter의 날짜 필드 등 모든 곳에 커맨드 출력값을 사용한다.

### 인코딩 처리 (Windows)
- yt-dlp의 stdout은 Windows에서 cp949로 출력된다.
- 반드시 Python subprocess로 실행하고, `.decode('cp949', errors='replace')`로 디코딩한다.
- 자막 json3 파일은 UTF-8이므로 별도 처리 불필요.

### 요약 언어
- 자막이 어떤 언어이든 **요약은 항상 한국어**로 작성한다.

### 에이전트 관리
- 영상당 1개 에이전트, 모두 `run_in_background: true`로 병렬 실행한다.
- 한 번에 최대 10개씩 배치로 실행한다. 10개 초과 시 배치 나눠 순차 실행.
- 에이전트 모델은 기본 `sonnet`. `--model`로 오버라이드 가능.

### 파일 관리
- 임시 파일은 `C:/Users/rollrat/yt_obsidian_tmp/` 에 저장하고, 완료 후 삭제한다.

## Workflow

### 1. 입력 파싱 & 환경 확인

```python
# 채널 형식 정규화
# @handle → https://www.youtube.com/@handle/videos
# URL → URL + /videos (없으면 추가)
```

- yt-dlp 설치 확인. 없으면 `pip install yt-dlp`로 설치.
- Bash로 현재 날짜/시간을 가져와 변수로 저장:
  ```bash
  date '+%Y-%m-%d_%H%M'
  ```

### 2. 영상 목록 수집

Python 스크립트로 최근 N개 영상의 ID와 제목을 가져온다:

```python
import subprocess, sys, json

result = subprocess.run(
    [sys.executable, '-m', 'yt_dlp', '--flat-playlist',
     '--print', '%(id)s|||%(title)s|||%(upload_date)s',
     '--playlist-end', str(count),
     channel_url],
    capture_output=True
)
# cp949 디코딩
text = result.stdout.decode('cp949', errors='replace')
```

**주의**: flat-playlist에서는 upload_date가 NA로 나올 수 있다.

### 3. 메타데이터 수집

각 영상의 상세 메타데이터를 가져온다:

```python
for vid in video_ids:
    result = subprocess.run(
        [sys.executable, '-m', 'yt_dlp', '--dump-json', '--skip-download',
         f'https://www.youtube.com/watch?v={vid}'],
        capture_output=True
    )
    data = json.loads(result.stdout.decode('cp949', errors='replace'))
    # title, upload_date, duration, description 추출
```

결과를 JSON 파일로 저장: `{tmp_dir}/meta.json`

### 4. 자막 다운로드

모든 영상의 자막을 일괄 다운로드:

```python
for vid in video_ids:
    subprocess.run([
        sys.executable, '-m', 'yt_dlp',
        '--write-auto-sub', '--sub-lang', lang,
        '--skip-download', '--sub-format', 'json3',
        '-o', f'{tmp_dir}/{vid}.%(ext)s',
        f'https://www.youtube.com/watch?v={vid}'
    ], capture_output=True)
```

### 5. 자막 → 텍스트 변환

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
```

자막이 없는 영상은 제목+설명으로 간략 요약 처리.

### 6. 병렬 요약 에이전트 실행

각 영상마다 Task 에이전트를 `run_in_background: true`로 실행한다.
**10개 이하면 한 번에, 초과하면 10개씩 배치.**

에이전트 프롬프트 템플릿:

```
C:/{tmp_dir}/{vid}.txt 파일의 자막 텍스트를 읽어라.

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
(설명의 챕터 구분에 맞춰 상세 요약. 핵심 수치, 사실, 논거 포함)

### 키워드
(쉼표로 구분된 관련 키워드/태그)
```

### 7. 주간 그룹핑

영상을 업로드 날짜 기준 **월~일(ISO week)** 단위로 그룹핑한다:

```python
from datetime import datetime, timedelta

def get_week_range(date_str):
    """YYYYMMDD → (월요일, 일요일) 튜플 반환"""
    dt = datetime.strptime(date_str, '%Y%m%d')
    monday = dt - timedelta(days=dt.weekday())  # 0=Mon
    sunday = monday + timedelta(days=6)
    return monday, sunday

# 그룹핑
weeks = {}
for video in videos:
    mon, sun = get_week_range(video['upload_date'])
    key = f"{mon.strftime('%y.%m.%d')}-{sun.strftime('%m.%d')}"
    weeks.setdefault(key, []).append(video)
```

파일명 예시: `26.02.03-02.09`, `26.01.27-02.02`
- 같은 연도면: `26.02.03-02.09`
- 연도가 다르면: `25.12.30-01.05`

### 8. Obsidian 주간 문서 저장

각 주간 그룹마다 하나의 마크다운 문서를 생성한다.

경로: `youtube/{채널명}/{주간범위}.md`

문서 구조:
```markdown
# {채널명} {주간범위}
> {시작일} ~ {종료일} 방송분 ({N}개 영상)

---

{영상1 요약 (에이전트 결과)}

---

{영상2 요약 (에이전트 결과)}

...
```

영상은 업로드 날짜 오름차순으로 정렬한다.

### 9. Summary 문서 저장

**파일명은 반드시 Bash 커맨드로 얻은 현재 날짜/시간을 사용한다.**

```bash
date '+%y.%m.%d_%H%M'
# 출력 예: 26.02.15_1430
```

경로: `youtube/{채널명}/summary_{날짜시간}.md`
예: `youtube/슈카월드/summary_26.02.15_1430.md`

Summary 문서 구조:
```markdown
# {채널명} 최근 영상 요약 ({날짜범위})
> 총 {N}개 영상 | {기간} 방송분 총망라

---

## 주간 목록

### [[{주간범위1}|1주차: {시작} ~ {종료}]] ({N}개)
| 날짜 | 제목 | 시간 |
|------|------|------|
| {MM.DD} | {제목} | {N}분 |
| ... | ... | ... |

### [[{주간범위2}|2주차: {시작} ~ {종료}]] ({N}개)
...

---

## 주제별 분류

{영상들을 주제별로 분류하여 각 영상의 핵심 한줄 요약과 함께 정리}

---

## 핵심 키워드 TOP 20
`키워드1` `키워드2` `키워드3` ...

---

## 기간 요약

{전체 기간의 흐름을 3-5문단으로 종합 정리}
```

### 10. 정리

- 임시 디렉토리 삭제: `rm -rf {tmp_dir}`
- 사용자에게 완료 보고: 저장된 파일 목록과 각 파일의 영상 수

## 인자 없이 실행 시 동작

**`/youtube-to-obsidian`을 인자 없이 실행하면 아래 안내를 출력하고 즉시 종료한다.**

출력 형식:

```
📺 YouTube to Obsidian - 채널 영상 요약 → 옵시디언 저장

사용법:
  /youtube-to-obsidian @syukaworld 10           — 슈카월드 최근 10개 영상 요약
  /youtube-to-obsidian @3blue1brown 5           — 3Blue1Brown 최근 5개 영상 요약
  /youtube-to-obsidian @channel 20 --lang en    — 영어 자막으로 다운로드 (요약은 한국어)
  /youtube-to-obsidian @channel 10 --folder 커스텀  — 폴더명 직접 지정

옵션:
  --lang <code>     자막 언어 (기본: ko)
  --model <model>   요약 에이전트 모델 (기본: sonnet)
  --folder <name>   Obsidian 폴더명 오버라이드

결과는 Obsidian 볼트의 youtube/{채널명}/ 폴더에 저장됩니다.
  - 주간별 문서: {날짜범위}.md
  - 종합 요약: summary_{날짜시간}.md
```

**이 안내만 출력하고 종료한다.**

## Error Handling

- **yt-dlp 미설치**: `pip install yt-dlp`로 자동 설치 후 재시도.
- **채널 못 찾음**: 채널 URL/핸들 확인 안내 후 중단.
- **자막 없음**: 해당 영상은 제목+설명만으로 간략 요약. `(자막 없음 - 설명 기반 요약)` 표시.
- **에이전트 실패**: 실패한 영상은 제목만 표시하고 나머지로 문서 생성.
- **Obsidian 볼트 없음**: 볼트 연결 확인 안내 후 중단.
- **영상 수 부족**: 채널에 요청한 수보다 영상이 적으면 있는 만큼만 처리.
