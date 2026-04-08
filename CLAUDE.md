# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

tport 조직의 공용 Claude Code 스킬 플러그인 마켓플레이스 (`tportio/skills`). Claude Code 플러그인 시스템을 통해 팀 전체가 공유하는 커스텀 스킬을 관리한다.

## 구조

- `.claude-plugin/marketplace.json` — 마켓플레이스 매니페스트. 모든 플러그인을 `plugins` 배열에 등록
- `.claude-plugin/plugin.json` — 루트 플러그인 메타데이터
- `plugins/<name>/` — 개별 플러그인 디렉토리
  - `.claude-plugin/plugin.json` — 플러그인 메타데이터
  - `skills/<skill-name>/SKILL.md` — 스킬 정의 (프롬프트, 허용 도구, 인수 힌트)
  - `skills/<skill-name>/` — 스킬에서 사용하는 스크립트/리소스

## 플러그인 추가 방법

1. `plugins/<name>/` 디렉토리 생성
2. `plugins/<name>/.claude-plugin/plugin.json` 작성 (name, description, version)
3. `plugins/<name>/skills/<skill>/SKILL.md` 작성 (frontmatter + 스킬 프롬프트)
4. `.claude-plugin/marketplace.json`의 `plugins` 배열에 등록

## SKILL.md frontmatter 필수 필드

```yaml
---
name: <스킬 이름>
description: <한 줄 설명>
disable-model-invocation: false
argument-hint: "<사용 예시>"
allowed-tools: Bash, Read, Write, Edit, ...
---
```

## 현재 플러그인

- **presentation-pdf**: HTML 슬라이드 프레젠테이션 생성 → Puppeteer 스크린샷 → pdf-lib로 PDF 조합. 런타임 의존성: `puppeteer`, `pdf-lib` (npm).
