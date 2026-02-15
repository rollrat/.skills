---
name: youtube-live
description: YouTube 라이브 스트림을 실시간 캡처하여 음성인식(Whisper) 후 Obsidian에 요약 저장합니다. /youtube-live <url> 로 실행.
---

# YouTube Live - 라이브 스트림 실시간 캡처 & 요약

## Overview

YouTube 라이브 스트림의 오디오를 실시간으로 캡처하고, faster-whisper로 음성인식하여 트랜스크립트를 누적합니다. 방송 종료 후(또는 수동 중단 시) 전체 트랜스크립트를 요약하여 Obsidian 볼트에 저장합니다.

**기술 스택**: yt-dlp (스트림 URL 추출) → ffmpeg (오디오 캡처) → faster-whisper (음성인식)

## Usage

```
/youtube-live <youtube_url> [options]
/youtube-live stop
/youtube-live status
```

### Commands
- `<url>`: 라이브 스트림 캡처 시작
- `stop`: 캡처 중단 + 트랜스크립트 요약 + Obsidian 저장
- `status`: 현재 캡처 진행 상황 확인

### Options
- `--model <size>`: Whisper 모델 크기 (기본: `base`). `tiny`, `base`, `small`, `medium`, `large-v3`
- `--chunk <seconds>`: 캡처 청크 길이 (기본: `300` = 5분)
- `--folder <name>`: Obsidian 저장 폴더 (기본: `youtube-live`)
- `--no-summary`: 요약 없이 트랜스크립트만 저장

## Critical Rules

### 날짜 처리 (필수)
- 현재 날짜/시간은 반드시 Bash 커맨드로 얻는다. 절대 추론하거나 추정하지 않는다.
- 파일명, frontmatter, 본문 등 모든 곳에서 커맨드 출력값만 사용한다.
- 예시:
  - `date '+%Y-%m-%d'` → 2026-02-15
  - `date '+%y.%m.%d_%H%M'` → 26.02.15_2130
  - `date '+%Y-%m-%dT%H:%M:%S'` → ISO 형식

### 출력 언어
- 모든 출력(요약, 트랜스크립트 정리, Obsidian 문서)은 **한국어**로 작성한다.
- 에이전트 프롬프트에 반드시 `한국어로 작성하라`를 포함한다.

### Windows 호환
- yt-dlp 출력은 cp949 인코딩일 수 있으므로 `.decode('cp949', errors='replace')` 처리한다.
- 경로는 Unix 스타일 사용 (`/c/Users/rollrat/...`).

### 임시 파일 관리
- 작업 디렉토리: `C:/Users/rollrat/yt_live_tmp/`
- 캡처 시작 시 디렉토리 생성, `stop` 또는 요약 완료 후 WAV 청크 파일 삭제.
- `full_transcript.txt`는 요약 완료 후에도 보존 (백업용).

### 의존성 자동 설치
- `faster-whisper` 미설치 시 `pip install faster-whisper`로 자동 설치.
- `yt-dlp` 미설치 시 `pip install yt-dlp`로 자동 설치.
- `ffmpeg`는 시스템에 설치되어 있어야 한다. 없으면 안내 후 중단.

## Workflow

### 1. `/youtube-live <url>` — 캡처 시작

#### 1-1. 입력 검증 & 환경 확인

```python
# URL에서 video ID 추출
# 라이브 여부 확인 (yt-dlp --dump-json → is_live == True)
# 채널명, 방송 제목 추출
```

의존성 확인:
```bash
python -c "from faster_whisper import WhisperModel; print('ok')" 2>/dev/null || pip install faster-whisper
python -m yt_dlp --version 2>/dev/null || pip install yt-dlp
where ffmpeg 2>/dev/null || echo "ffmpeg 필요"
```

Bash로 현재 날짜/시간 획득:
```bash
date '+%y.%m.%d_%H%M'
```

#### 1-2. 스트림 포맷 확인

```python
import subprocess, sys
# 사용 가능한 포맷 확인
r = subprocess.run(
    [sys.executable, '-m', 'yt_dlp', '--list-formats', url],
    capture_output=True
)
# 가장 낮은 품질의 비디오+오디오 포맷 선택 (오디오 품질은 동일)
# 보통 format ID '91' (256x144, mp4a)
```

#### 1-3. 캡처 스크립트 생성 & 백그라운드 실행

아래 Python 스크립트를 `{tmp_dir}/live_capture.py`에 생성하고 백그라운드로 실행한다.

**핵심 로직:**

```python
import subprocess, sys, os, time
from datetime import datetime
from faster_whisper import WhisperModel

STREAM_URL = "{url}"
TMP_DIR = "C:/Users/rollrat/yt_live_tmp"
CHUNK_DURATION = {chunk_seconds}  # 기본 300초 (5분)
TRANSCRIPT_FILE = os.path.join(TMP_DIR, "full_transcript.txt")
FORMAT_ID = "{format_id}"  # 가장 낮은 품질

os.makedirs(TMP_DIR, exist_ok=True)

def get_stream_url():
    r = subprocess.run(
        [sys.executable, '-m', 'yt_dlp', '-f', FORMAT_ID, '-g', STREAM_URL],
        capture_output=True, text=True
    )
    return r.stdout.strip()

def capture_audio(chunk_path, duration):
    url = get_stream_url()
    if not url:
        return False
    r = subprocess.run([
        'ffmpeg', '-y', '-i', url,
        '-t', str(duration),
        '-vn', '-acodec', 'pcm_s16le',
        '-ar', '16000', '-ac', '1',
        chunk_path
    ], capture_output=True, timeout=duration + 60)
    return r.returncode == 0

# 모델 1회 로드
model = WhisperModel('{whisper_model}', device='cpu', compute_type='int8')

chunk_num = 0
while True:
    chunk_num += 1
    chunk_path = os.path.join(TMP_DIR, f"chunk_{chunk_num:03d}.wav")
    timestamp = datetime.now().strftime('%H:%M:%S')

    try:
        success = capture_audio(chunk_path, CHUNK_DURATION)
    except subprocess.TimeoutExpired:
        break
    if not success:
        break

    # 음성인식
    segments, info = model.transcribe(chunk_path, language='ko')
    text = ' '.join([seg.text for seg in segments])

    # 트랜스크립트 누적
    with open(TRANSCRIPT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n\n--- Chunk {chunk_num} [{timestamp}] ---\n")
        f.write(text)

    # WAV 삭제 (디스크 절약)
    try:
        os.remove(chunk_path)
    except:
        pass
```

**실행 방법**: Bash 도구의 `run_in_background: true`로 실행한다.

```bash
python C:/Users/rollrat/yt_live_tmp/live_capture.py
```

#### 1-4. 사용자에게 시작 알림

캡처 시작 후 아래 정보를 출력:
```
🔴 라이브 캡처 시작

방송: {제목}
채널: {채널명}
모델: {whisper_model}
청크: {chunk_seconds}초 단위
트랜스크립트: C:/Users/rollrat/yt_live_tmp/full_transcript.txt

캡처가 백그라운드에서 진행 중입니다.
  /youtube-live status  — 진행 상황 확인
  /youtube-live stop    — 캡처 중단 + 요약 저장
```

---

### 2. `/youtube-live status` — 진행 상황 확인

1. 백그라운드 프로세스 동작 여부 확인
2. `full_transcript.txt` 파일 크기와 청크 수 확인:
   ```bash
   wc -c C:/Users/rollrat/yt_live_tmp/full_transcript.txt
   grep -c "^--- Chunk" C:/Users/rollrat/yt_live_tmp/full_transcript.txt
   ```
3. 마지막 청크의 텍스트 미리보기 (tail 500자)
4. 정보 출력:
   ```
   📊 캡처 진행 중

   청크 수: {N}개 완료
   트랜스크립트: {size} 글자
   마지막 청크: [{timestamp}]
   미리보기: {마지막 500자}...
   ```

---

### 3. `/youtube-live stop` — 캡처 중단 + 요약 + Obsidian 저장

#### 3-1. 캡처 중단

백그라운드 프로세스를 중단한다 (TaskStop 도구 사용).

#### 3-2. 메타데이터 수집

Bash로 현재 날짜/시간 획득:
```bash
date '+%y.%m.%d_%H%M'
```

yt-dlp로 방송 메타데이터 수집:
```python
# 제목, 채널명, 시작 시간, 길이 등
r = subprocess.run(
    [sys.executable, '-m', 'yt_dlp', '--dump-json', '--skip-download', url],
    capture_output=True
)
```

#### 3-3. 트랜스크립트 읽기

```python
with open('C:/Users/rollrat/yt_live_tmp/full_transcript.txt', 'r', encoding='utf-8') as f:
    transcript = f.read()
```

#### 3-4. 요약 에이전트 실행

트랜스크립트가 길면 (30,000자 초과) 청크별로 나눠서 병렬 에이전트로 요약한 뒤 종합한다.
트랜스크립트가 짧으면 단일 에이전트로 요약한다.

**에이전트 프롬프트 (단일)**:
```
아래는 YouTube 라이브 방송의 음성인식 트랜스크립트이다.

방송 정보:
- 제목: {title}
- 채널: {channel}
- 날짜: {date}
- URL: {url}

트랜스크립트:
{transcript}

아래 형식으로 한국어 요약을 작성하라 (마크다운만 출력):

## {title}
> 📅 {date} | 🔴 라이브 | [영상 링크]({url})

### 핵심 요약
(5-10개 bullet point로 방송 전체 핵심 내용)

### 주제별 정리
(방송에서 다룬 각 주제를 소제목으로 나누어 상세 요약)

### 키워드
(쉼표로 구분된 관련 키워드)
```

**에이전트 프롬프트 (분할 - 트랜스크립트가 긴 경우)**:
- 트랜스크립트를 ~25,000자 단위로 분할
- 각 파트를 별도 에이전트로 요약 (run_in_background)
- 모든 에이전트 완료 후, 메인 컨텍스트에서 파트별 요약을 종합

#### 3-5. Obsidian 저장

**날짜/시간은 반드시 Bash `date` 커맨드로 획득한 값을 사용한다.**

저장 경로: `youtube-live/{채널명}/{날짜시간}_{제목 요약}.md`
예: `youtube-live/슈카월드/26.02.15_2200_슈카월드_라이브.md`

문서 구조:
```markdown
---
tags:
  - youtube-live
  - {채널명}
channel: "{채널명}"
title: "{제목}"
date: "{YYYY-MM-DD}"
url: "{url}"
whisper_model: "{model}"
chunks: {N}
transcript_length: {글자수}
---

# {제목}
> 📅 {date} | 🔴 라이브 | 채널: {채널명} | [영상 링크]({url})

---

{에이전트 요약 결과}

---

## 트랜스크립트 (원문)

<details>
<summary>전체 트랜스크립트 펼치기 ({글자수}자)</summary>

{full_transcript}

</details>
```

Obsidian MCP `write_note`로 저장.

#### 3-6. 정리 & 완료 보고

- WAV 청크 파일 삭제
- full_transcript.txt는 보존
- 완료 메시지 출력:
  ```
  ✅ 라이브 요약 완료

  방송: {제목}
  채널: {채널명}
  청크: {N}개 ({총 분}분)
  트랜스크립트: {글자수}자
  저장: youtube-live/{채널명}/{파일명}.md
  ```

## 인자 없이 실행 시 동작

**`/youtube-live`를 인자 없이 실행하면 아래 안내를 출력하고 즉시 종료한다.**

```
🔴 YouTube Live - 라이브 스트림 실시간 캡처 & 요약

사용법:
  /youtube-live https://youtube.com/watch?v=VIDEO_ID     — 캡처 시작
  /youtube-live status                                     — 진행 상황 확인
  /youtube-live stop                                       — 캡처 중단 + 요약 저장

옵션:
  --model <size>      Whisper 모델 (tiny/base/small/medium/large-v3, 기본: base)
  --chunk <seconds>   청크 길이 (기본: 300 = 5분)
  --folder <name>     Obsidian 폴더명 (기본: youtube-live)
  --no-summary        요약 없이 트랜스크립트만 저장

모델 비교:
  tiny      — 가장 빠름, 정확도 낮음
  base      — 빠르고 적당한 정확도 (기본, 추천)
  small     — 균형 잡힌 속도/정확도
  medium    — 높은 정확도, 느림
  large-v3  — 최고 정확도, 매우 느림 (GPU 권장)

기술 스택: yt-dlp → ffmpeg → faster-whisper → Obsidian
```

**이 안내만 출력하고 종료한다.**

## Error Handling

- **라이브가 아닌 영상**: `is_live`가 False이면 "현재 라이브 중인 영상이 아닙니다" 안내 후 중단. 이미 끝난 라이브는 `/youtube-to-obsidian` 스킬 사용을 안내.
- **ffmpeg 미설치**: "ffmpeg가 필요합니다. winget install ffmpeg 또는 공식 사이트에서 설치하세요" 안내 후 중단.
- **스트림 URL 추출 실패**: yt-dlp JS 런타임 경고 시 무시하고 진행. URL 자체가 비면 "스트림 URL을 가져올 수 없습니다" 안내.
- **음성인식 실패**: 해당 청크 건너뛰고 다음 청크 진행. 에러 로그는 `{tmp_dir}/error.log`에 기록.
- **방송 종료 감지**: ffmpeg 캡처 실패 시 자동으로 캡처 루프 종료. 사용자에게 "방송이 종료된 것으로 보입니다. /youtube-live stop 으로 요약을 생성하세요" 안내.
- **이미 캡처 중**: 새 URL로 시작 시도 시 "이미 캡처가 진행 중입니다. /youtube-live stop 후 다시 시작하세요" 안내.
- **Obsidian 볼트 없음**: 볼트 연결 확인 안내 후 트랜스크립트만 로컬에 저장.
