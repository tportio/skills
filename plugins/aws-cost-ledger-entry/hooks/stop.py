import hashlib
import json
import os
import sys
import time
from pathlib import Path

from ledger_patterns import creation_commands, is_ledger_post, ledger_repo_problem

STATE_RETENTION_SECONDS = 30 * 24 * 3600


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _blocks(entry, kind):
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    return [b for b in content if isinstance(b, dict) and b.get("type") == kind]


def unrecorded_creations(transcript_path):
    """(key, command) pairs that ran successfully after the last ledger POST.

    key is the tool_use id, or a hash of the command when the block has no id.
    """
    calls = []
    failed = set()
    # errors="replace": one undecodable byte must not skip the whole transcript.
    with open(transcript_path, encoding="utf-8", errors="replace") as f:
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
                    # A post that the PreToolUse hook denies for a missing Repo never left; it records nothing.
                    if not ledger_repo_problem(command):
                        calls = []
                    continue
                tool_use_id = block.get("id")
                for segment in creation_commands(command):
                    key = tool_use_id if isinstance(tool_use_id, str) else f"cmd:{_sha(segment)}"
                    calls.append((key, tool_use_id, segment))
    return [(k, c) for k, i, c in calls if i is None or i not in failed]


def _state_file(session_id):
    """Per-session record of already-blocked keys, or None when there is no data dir."""
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
    return data_dir / f"stop-blocked-{_sha(str(session_id))[:32]}.json"


def _read_state(state):
    try:
        ids = json.loads(state.read_text())
    except (FileNotFoundError, ValueError):
        return set()
    return {i for i in ids if isinstance(i, str)} if isinstance(ids, list) else set()


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    if not isinstance(payload, dict) or payload.get("stop_hook_active"):
        return
    transcript_path = payload.get("transcript_path")
    if not isinstance(transcript_path, str):
        return
    try:
        pending = unrecorded_creations(transcript_path)
    except OSError:
        return
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
        state.write_text(json.dumps(sorted(already | {k for k, _ in fresh})))

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
