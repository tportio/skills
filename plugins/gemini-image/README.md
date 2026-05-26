# gemini-image

마크다운 글 본문의 `[IMAGE]` 블록을 자동 파싱해 **Gemini API(Nano Banana — `gemini-2.5-flash-image`)** 로 일괄 이미지 생성하는 Claude Code 스킬입니다. 단건 프롬프트도 지원합니다.

## 왜 만들었나

블로그/리포트/보고서를 쓸 때 본문에 들어갈 일러스트·인포그래픽을 글과 분리된 도구로 따로 만들면 컨텍스트 스위칭이 큽니다. 이 스킬은 글 안에 `[IMAGE]` 블록만 적어두면 한 번에 전부 생성해 줍니다. 프롬프트 품질 자동 보강·인포그래픽 감지가 들어 있어 평균 결과물이 안정적입니다.

## 사용법

### 파일 모드 (기본)

```
/gemini-image <마크다운 파일 경로>
/gemini-image <마크다운 파일 경로> --dry-run
```

본문에서 `[IMAGE]` 블록을 자동 찾아 일괄 생성합니다. `--dry-run` 으로 프롬프트만 미리 볼 수 있습니다.

### 단건 모드

```
/gemini-image --prompt "프롬프트" --filename name.png
```

### 호출 예시

```
/gemini-image ./blog/2026-01-rag-vs-fine-tuning.md
/gemini-image ./report.md --dry-run
/gemini-image --prompt "minimal hotel lobby, natural light" --filename lobby.png
```

## `[IMAGE]` 블록 형식

본문에 아래 두 가지 형식을 인식합니다.

### 형식 1 — 영문 프롬프트 직접 기재 (권장)

```markdown
> **[IMAGE 1 — 썸네일]**
> A split-screen conceptual illustration showing...
```

### 형식 2 — 구조화

```markdown
> **[IMAGE]**
> **제목**: 이미지 제목
> **프롬프트**: 상세 설명
> **비율**: 16:9
```

## 주요 옵션

| 옵션 | 기본 | 설명 |
|---|---|---|
| `--model` | `gemini-2.5-flash-image` | Gemini 모델 |
| `--ratio` | `16:9` | 비율 (1:1, 3:4, 4:3, 9:16, 16:9 등) |
| `--outdir` | `./images` | 출력 디렉토리 |
| `--dry-run` | — | 프롬프트만 출력 |
| `--no-enhance` | — | 프롬프트 자동 보강 비활성화 |

## 프롬프트 자동 보강

기본 활성화 (`--no-enhance` 로 끔):

- **일반 이미지**: 에디토리얼 품질, 깨끗한 구성, 아티팩트 없음
- **인포그래픽** (timeline, chart 등 키워드 자동 감지): 플랫 디자인, 텍스트 없이 아이콘만

## 사전 준비

1. **Python 패키지** (스킬이 자동 설치 시도):
   ```bash
   pip3 install google-genai python-dotenv
   ```

2. **API 키**: 프로젝트 루트의 `.env` 에 추가
   ```
   GEMINI_API_KEY=...
   ```
   무료 발급: https://aistudio.google.com/apikey

## 지원 모델

| 모델 | ID | 특징 |
|---|---|---|
| **Nano Banana (권장)** | `gemini-2.5-flash-image` | 안정, 무료 티어, 한국어 지원 |
| Imagen 4 Standard | `imagen-4.0-generate-001` | 2026.6 폐기 예정 |
| Imagen 4 Ultra | `imagen-4.0-ultra-generate-001` | 2026.6 폐기 예정 |

## 프롬프트 팁

- **구체적으로 서술**: "호텔 로비" → "밝은 자연광이 드는 미니멀 호텔 로비, 흰 대리석 바닥, 단독 오키드 화분"
- **원하는 것을 서술**: "차 없는 거리" 대신 "빈 거리"
- **한글 텍스트 지양**: AI 가 한글 렌더링을 잘 못함. "No readable text — icons and numbers only" 지시 후 Canva 등으로 오버레이
- **스타일 명시**: `editorial illustration`, `flat infographic`, `photorealistic`, `watercolor` 등
