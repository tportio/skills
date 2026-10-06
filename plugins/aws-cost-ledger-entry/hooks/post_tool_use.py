import json
import sys

from ledger_patterns import creation_commands


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return
    found = creation_commands(command)
    if not found:
        return
    listed = "\n".join(f"- {c[:200]}" for c in found)
    context = (
        "AWS 자원을 만들거나 늘리는 명령이 실행됐다:\n"
        f"{listed}\n"
        "지금 aws-cost-ledger-entry 스킬로 비용 대장에 한 행을 기재한다. "
        "명령이 실패했거나 자원이 생기지 않았으면 기재하지 않는다."
    )
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}},
        sys.stdout,
        ensure_ascii=True,
    )


if __name__ == "__main__":
    main()
