import json
import os
import re
import sys
import time
from pathlib import Path

from ledger_patterns import creation_commands, is_ledger_post

STATE_RETENTION_SECONDS = 30 * 24 * 3600
SAFE_SESSION_ID = re.compile(r"[^A-Za-z0-9_-]")


def _blocks(entry, kind):
    content = (entry.get("message") or {}).get("content")
    if not isinstance(content, list):
        return []
    return [b for b in content if isinstance(b, dict) and b.get("type") == kind]


def unrecorded_creations(transcript_path):
    """(tool_use_id, command) pairs that ran successfully after the last ledger POST."""
    calls = []
    failed = set()
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict):
                continue
            for block in _blocks(entry, "tool_result"):
                if block.get("is_error"):
                    failed.add(block.get("tool_use_id"))
            for block in _blocks(entry, "tool_use"):
                if block.get("name") != "Bash":
                    continue
                tool_input = block.get("input")
                command = tool_input.get("command") if isinstance(tool_input, dict) else None
                if not isinstance(command, str):
                    continue
                if is_ledger_post(command):
                    calls = []
                    continue
                for segment in creation_commands(command):
                    calls.append((block.get("id"), segment))
    return [(i, c) for i, c in calls if i not in failed]


def _state_file(session_id):
    """Per-session record of already-blocked tool_use ids, or None when there is no data dir."""
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data:
        return None
    data_dir = Path(data)
    data_dir.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - STATE_RETENTION_SECONDS
    for old in data_dir.glob("stop-blocked-*.json"):
        try:
            if old.stat().st_mtime < cutoff:
                old.unlink()
        except FileNotFoundError:
            pass
    safe_id = SAFE_SESSION_ID.sub("-", str(session_id))
    return data_dir / f"stop-blocked-{safe_id}.json"


def _read_state(state):
    try:
        ids = json.loads(state.read_text())
    except (FileNotFoundError, ValueError):
        return set()
    return {i for i in ids if isinstance(i, str)} if isinstance(ids, list) else set()


def main():
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return
    pending = unrecorded_creations(payload["transcript_path"])
    if not pending:
        return

    # Block once per creation command so a deliberate skip is not re-demanded every turn.
    # Without a data dir it still blocks; stop_hook_active keeps that from looping.
    state = _state_file(payload.get("session_id") or "unknown")
    already = _read_state(state) if state else set()
    fresh = [(i, c) for i, c in pending if i not in already]
    if not fresh:
        return
    if state:
        state.write_text(json.dumps(sorted(already | {i for i, _ in fresh if isinstance(i, str)})))

    listed = "\n".join(f"- {c[:200]}" for _, c in fresh)
    reason = (
        "비용 대장에 기재하지 않은 AWS 자원 생성·확장 명령이 있다:\n"
        f"{listed}\n"
        "aws-cost-ledger-entry 스킬로 지금 기재한다. 자원이 실제로 생기지 않았으면 "
        "그 이유를 한 줄로 사용자에게 알리고 끝낸다."
    )
    json.dump({"decision": "block", "reason": reason}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
