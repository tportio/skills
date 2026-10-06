"""Detects AWS create/scale-up commands and ledger webhook POSTs for both hooks."""

import re

AWS_GLOBAL_VALUE_OPTIONS = {
    "--profile", "--region", "--output", "--endpoint-url", "--query",
    "--cli-read-timeout", "--cli-connect-timeout", "--ca-bundle", "--color",
    "--cli-binary-format", "--cli-input-json", "--cli-input-yaml",
}

AWS_GROWTH_OPERATIONS = {
    "run-instances", "request-spot-instances",
    "modify-db-instance", "modify-db-cluster",
    "update-nodegroup-config", "set-desired-capacity", "update-auto-scaling-group",
    "modify-volume", "modify-instance-attribute", "modify-cache-cluster",
    "modify-replication-group", "increase-replica-count",
    "update-broker-storage", "update-broker-type",
}
AWS_GROWTH_PREFIXES = ("create-", "allocate-", "restore-db-")
AWS_SERVICE_GROWTH_OPERATIONS = {
    ("opensearch", "update-domain-config"),
    ("es", "update-elasticsearch-domain-config"),
}

# These creates cost nothing by themselves (config, networking plumbing, credentials);
# prompting on them is noise that trains people to ignore the prompt.
AWS_EXCLUDED_OPERATIONS = {
    "create-tags", "create-token", "create-login-profile", "create-access-key",
    "create-security-group", "create-key-pair", "create-launch-template",
    "create-launch-template-version", "create-placement-group", "create-network-acl",
    "create-network-acl-entry", "create-route-table", "create-route", "create-subnet",
    "create-internet-gateway", "create-db-subnet-group", "create-db-parameter-group",
    "create-db-cluster-parameter-group", "create-cache-subnet-group",
    "create-cache-parameter-group", "create-target-group", "create-listener",
    "create-rule", "create-log-stream",
}
AWS_EXCLUDED_SERVICES = {"iam", "sts", "sso", "sso-oidc", "organizations"}

EKSCTL_EXCLUDED_CREATE = {"iamidentitymapping", "iamserviceaccount"}

TERRAFORM_BINARIES = {"terraform", "tofu"}

COMMAND_WRAPPERS = {"sudo", "env", "time", "command", "exec", "nohup"}
SHELL_KEYWORDS = {"do", "then", "else", "elif", "while", "until", "if", "!", "{", "}"}
SHELLS = {"bash", "sh", "zsh", "dash"}
SSH_VALUE_OPTIONS = {
    "-b", "-c", "-D", "-E", "-e", "-F", "-I", "-i", "-J", "-L", "-l", "-m",
    "-O", "-o", "-p", "-Q", "-R", "-S", "-W", "-w", "-B",
}

OPERATORS = ("&&", "||", ";;", "|&", ";", "|", "&", "(", ")", "\n")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
HEREDOC_START = re.compile(r"(?<!<)<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
DESIRED_COUNT = re.compile(r"^--desired-count(=.*)?$")

LEDGER_WEBHOOK = re.compile(r"script\.google\.com/macros/s/[^/\s\"']+/exec")


def _strip_heredocs(command):
    """Drop heredoc bodies: they are data written somewhere, not commands run here."""
    out = []
    pending = []
    for line in command.split("\n"):
        if pending:
            dash, delimiter = pending[0]
            if (line.lstrip("\t") if dash else line) == delimiter:
                pending.pop(0)
            continue
        out.append(line)
        pending.extend((m.group(1) == "-", m.group(3)) for m in HEREDOC_START.finditer(line))
    return "\n".join(out)


def _matching_paren(s, start):
    depth = 1
    i = start
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            end = s.find("'", i + 1)
            i = len(s) if end < 0 else end + 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(s)


def _substitution(s, i, subs):
    """Consume a `$(...)` or backtick substitution at s[i]; return (raw, next index)."""
    if s[i] == "`":
        end = s.find("`", i + 1)
        end = len(s) if end < 0 else end
        subs.append(s[i + 1:end])
        return s[i:end + 1], end + 1
    end = _matching_paren(s, i + 2)
    subs.append(s[i + 2:end])
    return s[i:end + 1], end + 1


def _lex(s):
    """Shell-ish tokens: ("word", text) / ("op", text) / ("redir", text), plus substitutions.

    Quoting is honoured, so text inside quotes never becomes a command. Command substitutions
    in unquoted or double-quoted text are returned separately because they do execute.
    """
    tokens, subs, buf = [], [], []
    in_word = False

    def flush():
        nonlocal in_word
        if in_word:
            tokens.append(("word", "".join(buf)))
        buf.clear()
        in_word = False

    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            buf.append(s[i + 1])
            in_word = True
            i += 2
        elif c == "'":
            end = s.find("'", i + 1)
            end = n if end < 0 else end
            buf.append(s[i + 1:end])
            in_word = True
            i = end + 1
        elif c == '"':
            i += 1
            while i < n and s[i] != '"':
                if s[i] == "\\" and i + 1 < n:
                    buf.append(s[i + 1])
                    i += 2
                elif s.startswith("$(", i) or s[i] == "`":
                    raw, i = _substitution(s, i, subs)
                    buf.append(raw)
                else:
                    buf.append(s[i])
                    i += 1
            in_word = True
            i += 1
        elif s.startswith("$(", i) or c == "`":
            raw, i = _substitution(s, i, subs)
            buf.append(raw)
            in_word = True
        elif c == "#" and not in_word:
            end = s.find("\n", i)
            i = n if end < 0 else end
        elif c in " \t\r":
            flush()
            i += 1
        elif c in "<>" or s.startswith("&>", i):
            if in_word and "".join(buf).isdigit():
                buf.clear()
                in_word = False
            flush()
            j = i
            while j < n and s[j] in "<>&":
                j += 1
            tokens.append(("redir", s[i:j]))
            i = j
        else:
            op = next((o for o in OPERATORS if s.startswith(o, i)), None)
            if op:
                flush()
                tokens.append(("op", op))
                i += len(op)
            else:
                buf.append(c)
                in_word = True
                i += 1
    flush()
    return tokens, subs


def _segments(tokens):
    """Split tokens into simple commands (word lists), dropping redirect targets."""
    segment = []
    skip_next = False
    for kind, text in tokens:
        if kind == "op":
            if segment:
                yield segment
            segment = []
        elif kind == "redir":
            skip_next = True
        elif skip_next:
            skip_next = False
        else:
            segment.append(text)
    if segment:
        yield segment


def _program_and_args(words):
    i = 0
    while i < len(words) and (
        ENV_ASSIGNMENT.match(words[i]) or words[i] in COMMAND_WRAPPERS or words[i] in SHELL_KEYWORDS
    ):
        i += 1
    if i >= len(words):
        return None, []
    return words[i].rsplit("/", 1)[-1], words[i + 1:]


def _positional_indices(args, value_options):
    out = []
    skip = False
    for n, a in enumerate(args):
        if skip:
            skip = False
            continue
        if a.startswith("-"):
            if a in value_options:
                skip = True
            continue
        out.append(n)
    return out


def _positional(args, value_options):
    return [args[n] for n in _positional_indices(args, value_options)]


def _is_aws_growth(args):
    if "--dry-run" in args:
        return False
    idx = _positional_indices(args, AWS_GLOBAL_VALUE_OPTIONS)
    if len(idx) < 2:
        return False
    service, operation = args[idx[0]], args[idx[1]]
    if args[idx[1] + 1:] == ["help"]:
        return False
    if service in AWS_EXCLUDED_SERVICES or operation in AWS_EXCLUDED_OPERATIONS:
        return False
    if service == "ecs" and operation == "update-service":
        return any(DESIRED_COUNT.match(a) for a in args)
    return (
        operation in AWS_GROWTH_OPERATIONS
        or (service, operation) in AWS_SERVICE_GROWTH_OPERATIONS
        or operation.startswith(AWS_GROWTH_PREFIXES)
    )


def _is_eksctl_growth(args):
    if "--dry-run" in args or "--help" in args:
        return False
    pos = _positional(args, set())
    if not pos:
        return False
    if pos[0] == "scale":
        return True
    return pos[0] == "create" and not (len(pos) > 1 and pos[1] in EKSCTL_EXCLUDED_CREATE)


def _is_terraform_apply(args):
    if "-destroy" in args or "--destroy" in args or "-help" in args:
        return False
    pos = [a for a in args if not a.startswith("-")]
    return bool(pos) and pos[0] == "apply"


def _nested_script(program, args):
    """The command string a shell or ssh wrapper will run, if any."""
    if program in SHELLS:
        for n, a in enumerate(args):
            if re.fullmatch(r"-[a-z]*c[a-z]*", a) and n + 1 < len(args):
                return args[n + 1]
        return None
    if program == "ssh":
        pos = _positional(args, SSH_VALUE_OPTIONS)
        return " ".join(pos[1:]) if len(pos) > 1 else None
    return None


def creation_commands(command):
    """Return the simple commands in `command` that create or grow AWS resources."""
    text = _strip_heredocs(re.sub(r"\\\r?\n", " ", command or ""))
    tokens, subs = _lex(text)
    found = []
    for words in _segments(tokens):
        program, args = _program_and_args(words)
        nested = _nested_script(program, args)
        if nested:
            found.extend(creation_commands(nested))
        elif (
            (program == "aws" and _is_aws_growth(args))
            or (program == "eksctl" and _is_eksctl_growth(args))
            or (program in TERRAFORM_BINARIES and _is_terraform_apply(args))
        ):
            found.append(" ".join([program, *args]))
    for sub in subs:
        found.extend(creation_commands(sub))
    return found


def is_ledger_post(command):
    return "curl" in (command or "") and bool(LEDGER_WEBHOOK.search(command))


TAGS_FIELD = re.compile(r'"tags"\s*:\s*"([^"]*)"')
REPO_PAIR = re.compile(r"(?:^|,)\s*Repo\s*=\s*([^,]*)")
# GitHub repository names: letters, digits, '.', '_', '-'. Rejects '...', '-', '?', '<...>'.
REPO_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
# Words a blocked model might reach for instead of asking who owns the resource.
EVASIVE_REPOS = {"unknown", "tbd", "todo", "none", "null", "na", "n/a", "repo"}


def _repo_value_problem(value):
    if not value:
        return "tags 에 Repo=<레포 이름> 이 없다"
    if not REPO_NAME.match(value):
        return f"Repo={value} 는 레포 이름 형식이 아니다. tportio/ 같은 조직명 없이 레포 이름만 쓴다(영문·숫자·._-)"
    if value.lower() == "unmanaged":
        return "Repo=unmanaged 는 기존 자원 조사용 표시라 새로 만들거나 늘린 자원에는 쓸 수 없다"
    if value.lower() in EVASIVE_REPOS:
        return f"Repo={value} 는 레포 이름이 아니다"
    return None


def ledger_repo_problem(command):
    """Why a ledger POST may not go out for lack of a Repo tag, or None when it is fine.

    The ledger is append-only, so a row without Repo has to be stopped before it is sent.
    Every "tags" field and every Repo= pair is checked, so a second POST or a duplicate key
    cannot slip an empty or evasive value past the first good one.
    """
    fields = TAGS_FIELD.findall(command or "")
    if not fields:
        return "보내는 내용에서 \"tags\" 필드를 찾지 못했다. 스킬의 기재 명령처럼 본문을 명령 안에 그대로 넣어 보낸다"
    for field in fields:
        values = [v.strip() for v in REPO_PAIR.findall(field)] or [""]
        for value in values:
            problem = _repo_value_problem(value)
            if problem:
                return problem
    return None
