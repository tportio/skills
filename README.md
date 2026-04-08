# tport-skills

tport 공용 Claude Code 스킬 플러그인 마켓플레이스.

## 사용법

Claude Code 설정에서 이 저장소를 플러그인 소스로 등록하면, 포함된 스킬들을 `/스킬명` 형태로 사용할 수 있습니다.

## 플러그인 목록

| 플러그인 | 설명 |
|----------|------|
| [presentation-pdf](plugins/presentation-pdf) | HTML 슬라이드 프레젠테이션 생성 및 PDF 변환 |

## 플러그인 추가

1. `plugins/<name>/` 디렉토리 생성
2. `plugins/<name>/.claude-plugin/plugin.json` 작성
3. `plugins/<name>/skills/<skill>/SKILL.md` 작성
4. `.claude-plugin/marketplace.json`의 `plugins` 배열에 등록

### plugin.json 예시

```json
{
  "name": "my-skill",
  "description": "스킬 설명",
  "version": "1.0.0"
}
```

### SKILL.md frontmatter

```yaml
---
name: my-skill
description: 한 줄 설명
disable-model-invocation: false
argument-hint: "<사용 예시>"
allowed-tools: Bash, Read, Write, Edit
---
```
