import json
import sys

from ledger_patterns import creation_commands


def main():
    payload = json.load(sys.stdin)
    command = (payload.get("tool_input") or {}).get("command", "")
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
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
