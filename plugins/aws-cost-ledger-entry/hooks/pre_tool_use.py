import json
import sys

from ledger_patterns import is_ledger_post, ledger_repo_problem


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not is_ledger_post(command):
        return
    problem = ledger_repo_problem(command)
    if not problem:
        return
    reason = (
        f"비용 대장 기재를 막았다: {problem}.\n"
        "Repo 는 이 자원의 주인 앱 레포 이름이다(tportio 조직명 없이, 예: hub, pension-plus-core). "
        "여러 앱이 같이 쓰거나 플랫폼 자원이면 infra. 모르면 지어내지 말고 사용자에게 물어서 채운 뒤 다시 보낸다. "
        "대장은 지울 수 없으니 Repo 없이 먼저 보내지 않는다."
    )
    json.dump(
        {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }},
        sys.stdout,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
