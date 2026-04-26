---
name: gemini-image
description: 마크다운 글의 [IMAGE] 블록에서 Gemini API로 이미지를 생성한다.
disable-model-invocation: false
argument-hint: "[파일경로] [--dry-run] 또는 --prompt '...' --filename name.png"
allowed-tools: Bash(python3 *), Bash(pip3 install *), Read, Glob, AskUserQuestion
---

# Gemini 이미지 생성

마크다운 글에 포함된 `[IMAGE]` 블록을 파싱하여 Gemini API(Nano Banana — `gemini-2.5-flash-image`)로 이미지를 생성한다.

## Input

`$ARGUMENTS` — 마크다운 파일 경로, 또는 `--prompt` 플래그로 단건 프롬프트.

## Phase 1: 환경 확인

1. Python 패키지 확인. 없으면 설치:
   ```bash
   pip3 install google-genai python-dotenv 2>/dev/null
   ```
2. `GEMINI_API_KEY` 확인. 프로젝트 루트의 `.env` 파일, 또는 환경변수에서 로드.
   - 키가 없으면 사용자에게 안내: "프로젝트 루트의 `.env` 파일에 `GEMINI_API_KEY=...`를 추가하세요. Google AI Studio(https://aistudio.google.com/apikey)에서 무료로 발급 가능합니다."

## Phase 2: 입력 처리

인자에 따라 두 가지 모드로 동작한다.

### 파일 모드 (기본)

인자가 마크다운 파일 경로인 경우:

```bash
python3 "${CLAUDE_SKILL_DIR}/generate_images.py" "$ARGUMENTS"
```

- 파일에서 `[IMAGE]` 블록을 자동 파싱
- 발견된 블록 수와 프롬프트를 사용자에게 보여줌
- 생성된 이미지는 `--outdir` 경로에 저장 (기본: `./images`)

### 단건 모드

`--prompt` 플래그가 있는 경우:

```bash
python3 "${CLAUDE_SKILL_DIR}/generate_images.py" --prompt "프롬프트" --filename "name.png" --outdir "./images"
```

## Phase 3: 이미지 생성

`generate_images.py` 스크립트를 실행한다. 주요 옵션:

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--model` | `gemini-2.5-flash-image` | Gemini 모델 |
| `--ratio` | `16:9` | 비율 (1:1, 3:4, 4:3, 9:16, 16:9 등) |
| `--outdir` | `./images` | 출력 디렉토리 |
| `--dry-run` | - | 프롬프트만 출력, 생성하지 않음 |
| `--no-enhance` | - | 프롬프트 자동 보강 비활성화 |

**프롬프트 자동 보강**: 기본적으로 프롬프트에 품질 향상 지시가 추가된다.
- 일반 이미지: 에디토리얼 품질, 깨끗한 구성, 아티팩트 없음
- 인포그래픽(timeline, chart 등 키워드 감지): 플랫 디자인, 텍스트 없이 아이콘만

## Phase 4: 결과 보고

생성이 완료되면:
1. 생성된 이미지 파일 경로를 보고
2. Read 도구로 이미지를 보여주며 품질 확인
3. 문제가 있으면 프롬프트 수정 후 재생성 제안

## [IMAGE] 블록 형식

글 본문에 아래 두 가지 형식을 지원한다.

### 형식 1 — 영문 프롬프트 직접 기재 (권장)
```markdown
> **[IMAGE 1 — 썸네일]**
> A split-screen conceptual illustration showing...
```

### 형식 2 — 구조화 형식
```markdown
> **[IMAGE]**
> **제목**: 이미지 제목
> **프롬프트**: 이미지 생성 AI에 전달할 상세 설명
> **비율**: 16:9
```

## 에러 처리

| 에러 | 조치 |
|------|------|
| `GEMINI_API_KEY` 없음 | `.env` 파일 설정 안내 |
| `google-genai` 미설치 | `pip3 install google-genai python-dotenv` 실행 |
| 이미지 생성 실패 | finish_reason 확인, 프롬프트 수정 제안 |
| `[IMAGE]` 블록 없음 | 형식 가이드 안내 |

## 지원 모델

| 모델 | ID | 특징 |
|------|-----|------|
| **Nano Banana (권장)** | `gemini-2.5-flash-image` | 안정, 무료 티어, 한국어 지원 |
| Imagen 4 Standard | `imagen-4.0-generate-001` | 2026.6 폐기 예정 |
| Imagen 4 Ultra | `imagen-4.0-ultra-generate-001` | 2026.6 폐기 예정 |

## 프롬프트 작성 팁

- **구체적으로 서술**: "호텔 로비" → "밝은 자연광이 드는 미니멀 호텔 로비, 흰 대리석 바닥, 단독 오키드 화분"
- **원하는 것을 서술**: "차 없는 거리" 대신 "빈 거리"
- **한글 텍스트 지양**: AI가 한글 렌더링을 잘 못함. "No readable text — icons and numbers only" 지시 후 Canva 등으로 오버레이
- **스타일 명시**: "editorial illustration", "flat infographic", "photorealistic", "watercolor" 등
