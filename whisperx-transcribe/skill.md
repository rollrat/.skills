---
name: whisperx-transcribe
description: 오디오 파일을 WhisperX(GPU, large-v3)로 전사하여 같은 이름의 .txt 파일로 저장합니다. /whisperx-transcribe <파일경로> 로 실행.
---

# WhisperX 전사 스킬

오디오 파일을 받아 WhisperX(GPU)로 전사하고, 타임스탬프가 포함된 `.txt` 파일로 저장합니다.

## Usage

```
/whisperx-transcribe <오디오파일경로>
```

### 예시
```
/whisperx-transcribe "C:/Users/rollrat/Desktop/workspace/voicetest/녹음.m4a"
/whisperx-transcribe recording.mp3
/whisperx-transcribe /path/to/audio.wav
```

### 지원 형식
- m4a, mp3, wav, mp4, flac, ogg, webm 등 ffmpeg이 지원하는 모든 오디오 형식

### 출력 형식
```
[HH:MM:SS.ss --> HH:MM:SS.ss] 대사 내용
[00:00:07.54 --> 00:00:12.46] 안녕하세요, 오늘은...
```

출력 파일명: 입력 파일의 확장자를 `.txt`로 교체
- `녹음.m4a` → `녹음.txt`
- `recording.mp3` → `recording.txt`

## Critical Rules

### 날짜 처리 (필수)
- 현재 날짜/시간은 반드시 Bash 커맨드로 얻는다. 절대 추론하거나 추정하지 않는다.
- `date '+%Y-%m-%d'` 형식 사용.

### 출력 언어
- 사용자와의 모든 커뮤니케이션은 한국어로 한다.
- 전사 언어는 오디오 내용에 따라 자동 감지하되, 기본값은 `ko`(한국어).

### Windows 호환
- 외부 프로세스 출력 cp949 디코딩 처리.
- 경로에 한글/특수문자가 포함될 수 있으므로 Python에서 처리.

### GPU 필수
- 반드시 `device='cuda'`, `compute_type='float16'` 으로 실행한다.
- GPU가 없으면 사용자에게 안내하고 종료한다.

## Workflow

### 1. 인자 확인
인자가 없으면 사용법 안내 출력 후 종료.

인자가 있으면:
- 파일 존재 여부 확인
- 출력 파일 경로 결정: 입력 파일 확장자를 `.txt`로 교체
  - 같은 디렉터리에 저장
  - 예: `foo.m4a` → `foo.txt`

### 2. GPU 확인
```python
import torch
print(torch.cuda.is_available())
```
False면 에러 안내 후 종료.

### 3. WhisperX 실행 (Python 스크립트)

아래 Python 코드를 Bash로 실행한다. 경로에 특수문자가 있을 수 있으므로 **반드시 Python 파일로 작성 후 실행**한다.

```python
# transcribe_runner.py (임시 파일로 생성 후 실행)
import warnings
warnings.filterwarnings('ignore')
import whisperx
import gc
import sys
import os

audio_path = sys.argv[1]
output_path = sys.argv[2]

DEVICE = 'cuda'
COMPUTE_TYPE = 'float16'
BATCH_SIZE = 16
LANGUAGE = 'ko'

print(f'입력: {audio_path}')
print(f'출력: {output_path}')

# 1단계: 모델 로드 (VAD 임계값 완화 - 속삭임/짧은 발화 감지)
print('1단계: Whisper 모델 로드 (vad_onset=0.2)...')
model = whisperx.load_model(
    'large-v3', DEVICE,
    compute_type=COMPUTE_TYPE,
    language=LANGUAGE,
    vad_options={
        "vad_onset": 0.2,   # 기본 0.5 → 낮출수록 조용한 소리도 감지
        "vad_offset": 0.2,  # 기본 0.363
    }
)

# 2단계: 전사
print('2단계: 오디오 로드 및 전사...')
audio = whisperx.load_audio(audio_path)
result = model.transcribe(audio, batch_size=BATCH_SIZE, language=LANGUAGE)
print(f'세그먼트 수: {len(result["segments"])}')

# 3단계: 정렬 (단어 단위 타임스탬프)
print('3단계: 정렬(align)...')
del model; gc.collect()
model_a, metadata = whisperx.load_align_model(language_code=LANGUAGE, device=DEVICE)
result = whisperx.align(result['segments'], model_a, metadata, audio, DEVICE, return_char_alignments=False)
del model_a; gc.collect()
print('정렬 완료')

# 4단계: 저장
print(f'4단계: {output_path} 저장...')
with open(output_path, 'w', encoding='utf-8') as f:
    for seg in result['segments']:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        h_s, m_s, s_s = int(start//3600), int((start%3600)//60), start%60
        h_e, m_e, s_e = int(end//3600), int((end%3600)//60), end%60
        line = f'[{h_s:02d}:{m_s:02d}:{s_s:05.2f} --> {h_e:02d}:{m_e:02d}:{s_e:05.2f}] {text}'
        print(line)
        f.write(line + '\n')

print(f'\n완료: {output_path}')

# 통계 출력
with open(output_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'총 {len(lines)}줄 저장됨')
```

실행 방법:
```bash
# 임시 스크립트 파일 생성 후 실행
python /tmp/whisperx_runner.py "<오디오경로>" "<출력경로>"
```

실제 구현 시 Write 도구로 `/tmp/whisperx_runner.py` 작성 후 Bash로 실행.

### 4. 결과 보고

```
✅ 전사 완료

입력: {파일명}
출력: {txt파일명}
총 줄 수: {N}줄
마지막 타임스탬프: {HH:MM:SS}
```

## 인자 없이 실행 시 동작

```
🎙️ WhisperX 전사 스킬

사용법:
  /whisperx-transcribe <오디오파일경로>

예시:
  /whisperx-transcribe "녹음.m4a"
  /whisperx-transcribe "C:/Users/rollrat/Desktop/recording.mp3"

지원 형식: m4a, mp3, wav, mp4, flac, ogg, webm 등
출력: 같은 경로에 같은 이름의 .txt 파일

설정:
  - 모델: large-v3 (GPU 필수)
  - 언어: 한국어 (ko)
  - 타임스탬프: 세그먼트 단위
  - VAD: vad_onset=0.2, vad_offset=0.2 (속삭임/짧은 발화 감지 강화)
```

## Error Handling

- **파일 없음**: `파일을 찾을 수 없습니다: {경로}` 출력 후 종료
- **GPU 없음**: `CUDA GPU가 필요합니다. torch.cuda.is_available() = False` 출력 후 종료
- **whisperx 미설치**: `pip install whisperx` 안내 후 종료
- **출력 파일 이미 존재**: 덮어쓴다 (별도 확인 없음)
- **언어 감지 실패**: 기본값 `ko`로 계속 진행
