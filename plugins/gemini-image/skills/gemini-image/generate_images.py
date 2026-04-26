#!/usr/bin/env python3
"""
Gemini 이미지 생성 스크립트.
마크다운 글의 [IMAGE] 블록을 파싱하여 이미지를 생성하거나,
개별 프롬프트로 단건 생성한다.

사용법:
  # 마크다운 파일에서 [IMAGE] 블록 추출 → 일괄 생성
  python3 generate_images.py "path/to/article.md"

  # 단건 생성
  python3 generate_images.py --prompt "A modern hotel lobby" --filename "lobby.png"

  # 옵션
  --ratio 16:9|1:1|4:3|...  비율 (기본: 16:9)
  --outdir path              출력 디렉토리 (기본: ./images)
  --dry-run                  프롬프트만 출력, 생성하지 않음
  --model MODEL              모델명 (기본: gemini-2.5-flash-image)
  --no-enhance               프롬프트 자동 보강 비활성화
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    # 프로젝트 루트의 .env 파일 로드 시도
    for candidate in [Path.cwd() / ".env", Path(__file__).resolve().parent / ".env"]:
        if candidate.exists():
            load_dotenv(candidate)
            break
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("google-genai 패키지가 필요합니다: pip install google-genai")


# ---------------------------------------------------------------------------
# 프롬프트 보강: 에디토리얼 이미지 품질 향상
# ---------------------------------------------------------------------------
ENHANCE_SUFFIX = (
    " High detail, professional editorial illustration quality. "
    "Clean composition with balanced negative space. "
    "Publication-ready, 4K resolution rendering. "
    "No watermarks, no artifacts."
)

INFOGRAPHIC_SUFFIX = (
    " Clean infographic style, flat design with subtle shadows. "
    "Professional business publication aesthetic. "
    "No readable text — use icons, arrows, and numbers only. "
    "High detail, sharp vector-like rendering, 4K quality."
)


def enhance_prompt(prompt):
    """프롬프트에 품질 향상 지시를 자동 추가한다."""
    lower = prompt.lower()
    is_infographic = any(w in lower for w in [
        "infographic", "timeline", "flowchart", "diagram",
        "chart", "comparison", "data visualization",
    ])
    suffix = INFOGRAPHIC_SUFFIX if is_infographic else ENHANCE_SUFFIX
    return prompt.rstrip(". ") + "." + suffix


# ---------------------------------------------------------------------------
# API 클라이언트
# ---------------------------------------------------------------------------
def get_client():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        sys.exit(
            "GEMINI_API_KEY 환경변수가 설정되지 않았습니다.\n"
            "프로젝트 루트의 .env 파일에 GEMINI_API_KEY=... 를 추가하세요."
        )
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# [IMAGE] 블록 파서
# ---------------------------------------------------------------------------
def parse_image_blocks(md_path):
    """마크다운 파일에서 [IMAGE] 블록을 파싱한다.

    지원 형식:
    > **[IMAGE 1 — 썸네일]**
    > 프롬프트 텍스트...

    또는:
    > **[IMAGE]**
    > **제목**: 이미지 제목
    > **프롬프트**: 프롬프트 텍스트
    > **비율**: 16:9
    """
    text = md_path.read_text(encoding="utf-8")
    blocks = []

    # 연속된 blockquote 라인을 그룹으로 묶기
    lines = text.split("\n")
    bq_groups = []
    current_group = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">"):
            current_group.append(stripped.lstrip("> ").strip())
        else:
            if current_group:
                bq_groups.append(current_group)
                current_group = []
    if current_group:
        bq_groups.append(current_group)

    for group in bq_groups:
        joined = "\n".join(group)
        header_match = re.search(r"\[IMAGE[^\]]*\]", joined)
        if not header_match:
            continue

        header_text = header_match.group(0)
        label_match = re.search(
            r"\[IMAGE\s*(\d*)\s*(?:—|[-–])\s*(.+?)\]", header_text
        )
        if label_match:
            num = label_match.group(1) or ""
            label = label_match.group(2).strip()
        else:
            num_match = re.search(r"\[IMAGE\s*(\d*)\s*\]", header_text)
            num = num_match.group(1) if num_match else ""
            label = ""

        field_prompt = ""
        field_ratio = "16:9"
        field_title = ""

        title_m = re.search(r"\*\*제목\*\*:\s*(.+)", joined)
        prompt_m = re.search(r"\*\*프롬프트\*\*:\s*(.+)", joined)
        ratio_m = re.search(r"\*\*비율\*\*:\s*(.+)", joined)

        if prompt_m:
            field_prompt = prompt_m.group(1).strip()
        if title_m:
            field_title = title_m.group(1).strip()
        if ratio_m:
            field_ratio = ratio_m.group(1).strip()

        if not field_prompt:
            remaining = []
            header_found = False
            for line in group:
                if not header_found and re.search(r"\[IMAGE", line):
                    header_found = True
                    continue
                if re.match(r"\*\*\w+\*\*:", line):
                    continue
                remaining.append(line)
            field_prompt = " ".join(remaining).strip()

        if not field_prompt:
            continue

        # 파일명 생성
        stem = md_path.stem
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})", stem)
        date_prefix = date_match.group(1) if date_match else ""

        if num:
            safe_label = (
                re.sub(r"[^\w가-힣]", "-", label).strip("-") if label else "image"
            )
            filename = (
                "%s-img%s-%s.png" % (date_prefix, num, safe_label)
                if date_prefix
                else "img%s-%s.png" % (num, safe_label)
            )
        else:
            idx = len(blocks) + 1
            filename = (
                "%s-img%d.png" % (date_prefix, idx)
                if date_prefix
                else "img%d.png" % idx
            )

        blocks.append({
            "prompt": field_prompt,
            "filename": filename,
            "aspect_ratio": field_ratio,
            "title": field_title or label or "Image %s" % (num or len(blocks) + 1),
        })

    return blocks


# ---------------------------------------------------------------------------
# 이미지 생성
# ---------------------------------------------------------------------------
def generate_image(client, prompt, filename, aspect_ratio, output_dir, model,
                   do_enhance=True):
    """Gemini 모델로 이미지를 생성하여 저장한다."""
    final_prompt = enhance_prompt(prompt) if do_enhance else prompt

    print("\n  생성 중: %s" % filename)
    print("  모델: %s | 비율: %s" % (model, aspect_ratio))
    print("  프롬프트: %s%s" % (prompt[:100], "..." if len(prompt) > 100 else ""))
    if do_enhance:
        print("  (프롬프트 자동 보강 적용)")

    try:
        # Nano Banana 계열 (gemini-*): generate_content API
        if "gemini" in model:
            image_cfg = types.ImageConfig(aspect_ratio=aspect_ratio)
            response = client.models.generate_content(
                model=model,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=image_cfg,
                ),
            )

            if (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                for part in response.candidates[0].content.parts:
                    if (
                        hasattr(part, "inline_data")
                        and part.inline_data
                        and part.inline_data.mime_type
                        and part.inline_data.mime_type.startswith("image/")
                    ):
                        img_bytes = part.inline_data.data
                        if isinstance(img_bytes, str):
                            img_bytes = base64.b64decode(img_bytes)

                        output_dir.mkdir(parents=True, exist_ok=True)
                        out_path = output_dir / filename
                        out_path.write_bytes(img_bytes)
                        print("  -> 저장 완료: %s" % out_path)
                        return str(out_path)

            print("  [실패] 이미지가 생성되지 않았습니다.")
            if response.candidates:
                cand = response.candidates[0]
                if hasattr(cand, "finish_reason"):
                    print("  finish_reason: %s" % cand.finish_reason)
            return None

        # Imagen 계열 (레거시): generate_images API
        else:
            response = client.models.generate_images(
                model=model,
                prompt=final_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                ),
            )

            if response.generated_images:
                img_bytes = response.generated_images[0].image.image_bytes
                output_dir.mkdir(parents=True, exist_ok=True)
                out_path = output_dir / filename
                out_path.write_bytes(img_bytes)
                print("  -> 저장 완료: %s" % out_path)
                return str(out_path)
            else:
                print("  [실패] 이미지가 생성되지 않았습니다.")
                return None

    except Exception as e:
        print("  [에러] %s" % e)
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Gemini 이미지 생성")
    parser.add_argument(
        "file", nargs="?", help="마크다운 파일 경로 ([IMAGE] 블록에서 추출)"
    )
    parser.add_argument("--prompt", help="단건 생성 프롬프트")
    parser.add_argument(
        "--filename", default="output.png", help="출력 파일명 (기본: output.png)"
    )
    parser.add_argument("--ratio", default="16:9", help="비율 (기본: 16:9)")
    parser.add_argument(
        "--outdir", default="./images", help="출력 디렉토리 (기본: ./images)",
    )
    parser.add_argument(
        "--model", default="gemini-2.5-flash-image",
        help="모델명 (기본: gemini-2.5-flash-image)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="프롬프트만 출력, 생성하지 않음"
    )
    parser.add_argument(
        "--no-enhance", action="store_true",
        help="프롬프트 자동 보강 비활성화",
    )
    args = parser.parse_args()

    output_dir = Path(args.outdir)
    do_enhance = not args.no_enhance

    # 단건 모드
    if args.prompt:
        final = enhance_prompt(args.prompt) if do_enhance else args.prompt
        print("=" * 60)
        print("단건 이미지 생성")
        print("=" * 60)
        if args.dry_run:
            print("\n  [DRY-RUN]")
            print("  모델: %s" % args.model)
            print("  파일명: %s" % args.filename)
            print("  비율: %s" % args.ratio)
            print("  원본 프롬프트: %s" % args.prompt)
            if do_enhance:
                print("  보강 프롬프트: %s" % final)
            return

        client = get_client()
        result = generate_image(
            client, args.prompt, args.filename, args.ratio,
            output_dir, args.model, do_enhance,
        )
        sys.exit(0 if result else 1)

    # 파일 모드
    if args.file:
        md_path = Path(args.file)
        if not md_path.exists():
            sys.exit("파일을 찾을 수 없습니다: %s" % md_path)

        blocks = parse_image_blocks(md_path)
        if not blocks:
            sys.exit("마크다운에서 [IMAGE] 블록을 찾지 못했습니다.")

        print("=" * 60)
        print("이미지 생성: %s" % md_path.name)
        print("모델: %s" % args.model)
        print("발견된 [IMAGE] 블록: %d개" % len(blocks))
        print("출력: %s" % output_dir)
        print("=" * 60)

        if args.dry_run:
            for i, block in enumerate(blocks, 1):
                original = block["prompt"]
                enhanced = enhance_prompt(original) if do_enhance else original
                print("\n--- [%d/%d] %s ---" % (i, len(blocks), block["title"]))
                print("  파일명: %s" % block["filename"])
                print("  비율: %s" % block["aspect_ratio"])
                print("  원본 프롬프트: %s" % original)
                if do_enhance:
                    print("  보강 프롬프트: %s" % enhanced)
            return

        client = get_client()
        results = []
        for i, block in enumerate(blocks, 1):
            print("\n--- [%d/%d] %s ---" % (i, len(blocks), block["title"]))
            result = generate_image(
                client, block["prompt"], block["filename"],
                block["aspect_ratio"], output_dir, args.model, do_enhance,
            )
            results.append(result)

        print("\n" + "=" * 60)
        print("결과 요약")
        print("=" * 60)
        for block, result in zip(blocks, results):
            status = "OK" if result else "FAIL"
            print("  [%s] %s" % (status, block["filename"]))
        success = sum(1 for r in results if r)
        print("\n총 %d/%d개 생성 완료" % (success, len(blocks)))
        sys.exit(0 if success == len(blocks) else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
