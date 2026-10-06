import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS))

from ledger_patterns import creation_commands, is_ledger_post, ledger_repo_problem  # noqa: E402

LEDGER_POST_NO_TAGS = (
    'curl -s -o /dev/null -w "%{http_code}" -X POST '
    '"https://script.google.com/macros/s/AKfycbxKYs0wD0y8/exec" -d \'{"by":"a"}\''
)
LEDGER_POST = (
    'curl -s -o /dev/null -w "%{http_code}" -X POST '
    '"https://script.google.com/macros/s/AKfycbxKYs0wD0y8/exec" -d \'{"by":"a","tags":"Repo=hub,Service=hub"}\''
)


def state_path(data_dir, session_id):
    digest = hashlib.sha256(str(session_id).encode("utf-8")).hexdigest()[:32]
    return Path(data_dir) / f"stop-blocked-{digest}.json"


def run_hook(script, payload, data_dir, raw_stdin=None):
    env = {"PATH": "/usr/bin:/bin"}
    if data_dir is not None:
        env["CLAUDE_PLUGIN_DATA"] = data_dir
    proc = subprocess.run(
        [sys.executable, "-B", str(HOOKS / script)],
        input=json.dumps(payload) if raw_stdin is None else raw_stdin,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def write_transcript(path, commands, failed=(), with_ids=True):
    with open(path, "w", encoding="utf-8") as f:
        for n, command in enumerate(commands):
            tool_id = f"toolu_{n}"
            tool_use = {"type": "tool_use", "name": "Bash", "input": {"command": command}}
            if with_ids:
                tool_use["id"] = tool_id
            f.write(json.dumps({"type": "assistant", "message": {"content": [tool_use]}}) + "\n")
            f.write(json.dumps({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": tool_id, "is_error": command in failed,
                 "content": "Exit code 1" if command in failed else "ok"},
            ]}}) + "\n")


class CreationCommandsTest(unittest.TestCase):
    def test_detected(self):
        cases = [
            "aws ec2 run-instances --instance-type m5.large",
            "aws --profile okta.dev --region ap-northeast-2 rds create-db-instance --db-instance-identifier x",
            "AWS_PROFILE=okta.prod aws eks update-nodegroup-config --cluster-name c --nodegroup-name n",
            "aws autoscaling set-desired-capacity --auto-scaling-group-name g --desired-capacity 3",
            "aws ec2 allocate-address",
            "aws rds modify-db-instance --db-instance-identifier x --allocated-storage 500",
            "aws ec2 modify-volume --volume-id vol-1 --size 200",
            "eksctl create nodegroup --cluster c",
            "eksctl scale nodegroup --cluster c --nodes 4",
            "terraform apply -auto-approve",
            "terraform -chdir=infra/prd apply",
            "cd infra && tofu apply",
            "sudo aws elasticache create-replication-group --replication-group-id r",
            "aws rds restore-db-instance-from-db-snapshot --db-instance-identifier x",
            "aws rds restore-db-cluster-from-snapshot --db-cluster-identifier x",
            "aws elasticache increase-replica-count --replication-group-id r",
            "aws mq update-broker-storage --broker-id b",
            "aws mq update-broker-type --broker-id b",
            "aws ec2 request-spot-instances --instance-count 2",
            "aws opensearch update-domain-config --domain-name d",
            "aws ecs create-service --service-name s",
            "aws ecs update-service --service s --desired-count 4",
            "aws ecs update-service --service s --desired-count=4",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(len(creation_commands(command)), 1)

    def test_shell_forms_detected(self):
        cases = {
            "ID=$(aws ec2 run-instances --instance-type m5.large --query 'Instances[0].InstanceId')":
                "aws ec2 run-instances --instance-type m5.large --query Instances[0].InstanceId",
            "ID=`aws ec2 allocate-address`": "aws ec2 allocate-address",
            'echo "created $(aws ec2 create-volume --size 10)"': "aws ec2 create-volume --size 10",
            "for i in 1 2; do aws ec2 run-instances --count 1; done": "aws ec2 run-instances --count 1",
            "if aws sts get-caller-identity; then aws ec2 allocate-address; fi": "aws ec2 allocate-address",
            "bash -c 'aws ec2 run-instances --count 1'": "aws ec2 run-instances --count 1",
            "sh -lc \"terraform apply -auto-approve\"": "terraform apply -auto-approve",
            "ssh -i key.pem bastion 'aws rds create-db-instance --db-instance-identifier x'":
                "aws rds create-db-instance --db-instance-identifier x",
            "aws \\\n  ec2 run-instances --count 1": "aws ec2 run-instances --count 1",
            "aws --profile okta.dev \\\n  rds create-db-instance --db-instance-identifier x":
                "aws --profile okta.dev rds create-db-instance --db-instance-identifier x",
            "aws ec2 run-instances --user-data help": "aws ec2 run-instances --user-data help",
            "(cd infra && terraform apply -auto-approve)": "terraform apply -auto-approve",
            "{ aws ec2 allocate-address; }": "aws ec2 allocate-address",
            "! aws ec2 allocate-address": "aws ec2 allocate-address",
            "aws ec2 run-instances --count 1 > out.json 2>&1": "aws ec2 run-instances --count 1",
            "aws ec2 allocate-address &> log.txt": "aws ec2 allocate-address",
        }
        for command, segment in cases.items():
            with self.subTest(command=command):
                self.assertEqual(creation_commands(command), [segment])

    def test_text_that_only_mentions_a_create_is_ignored(self):
        cases = [
            'git commit -m "docs: note; aws ec2 run-instances example"',
            "echo 'aws ec2 run-instances && terraform apply'",
            "cat > deploy.sh <<'EOF'\naws ec2 run-instances --count 1\nterraform apply\nEOF\nchmod +x deploy.sh",
            "cat <<EOF > notes.md\naws rds create-db-instance\nEOF",
            "cat <<-EOF\n\taws ec2 allocate-address\n\tEOF",
            "grep -r 'aws ec2 run-instances' .",
            "echo '$(aws ec2 run-instances)'",
            "cat <<< \"aws ec2 run-instances\"",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(creation_commands(command), [])

    def test_command_after_heredoc_is_still_scanned(self):
        command = "cat > a.txt <<EOF\nhello\nEOF\naws ec2 allocate-address"
        self.assertEqual(creation_commands(command), ["aws ec2 allocate-address"])

    def test_zero_cost_creates_ignored(self):
        cases = [
            "aws ec2 create-security-group --group-name g --description d",
            "aws ec2 create-key-pair --key-name k",
            "aws ec2 create-launch-template --launch-template-name t",
            "aws ec2 create-launch-template-version --launch-template-id t",
            "aws ec2 create-subnet --vpc-id v --cidr-block 10.0.0.0/24",
            "aws ec2 create-route-table --vpc-id v",
            "aws rds create-db-subnet-group --db-subnet-group-name s",
            "aws rds create-db-parameter-group --db-parameter-group-name p",
            "aws elbv2 create-target-group --name t",
            "aws elbv2 create-listener --load-balancer-arn a",
            "aws logs create-log-stream --log-group-name g --log-stream-name s",
            "aws ecs update-service --service s --force-new-deployment",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(creation_commands(command), [])

    def test_ignored(self):
        cases = [
            "aws ec2 create-tags --resources i-1 --tags Key=Service,Value=hub",
            "aws sso-oidc create-token --client-id x",
            "aws iam create-role --role-name r",
            "aws ec2 describe-instances",
            "aws ec2 run-instances --dry-run --instance-type m5.large",
            "aws ec2 create-volume help",
            "terraform plan",
            "terraform apply -destroy",
            "terraform destroy",
            "eksctl get nodegroup --cluster c",
            "eksctl create iamidentitymapping --cluster c",
            "grep create-db-instance notes.md",
            "echo 'terraform apply' # reminder",
            "",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(creation_commands(command), [])

    def test_help_is_judged_at_the_operation_position(self):
        self.assertEqual(creation_commands("aws ec2 --output create-volume create-volume help"), [])
        self.assertEqual(
            creation_commands("aws ec2 create-volume --description help"),
            ["aws ec2 create-volume --description help"],
        )

    def test_chained_command_reports_each_segment(self):
        command = "aws ec2 create-volume --size 100 && aws ec2 create-tags --resources v && terraform apply"
        self.assertEqual(
            creation_commands(command),
            ["aws ec2 create-volume --size 100", "terraform apply"],
        )

    def test_ledger_post(self):
        self.assertTrue(is_ledger_post(LEDGER_POST))
        self.assertFalse(is_ledger_post("open https://script.google.com/macros/s/AKfy/exec"))
        self.assertFalse(is_ledger_post("curl -s https://example.com/exec"))


def ledger_post_with_tags(tags):
    body = json.dumps({"by": "a", "env": "prd", "tags": tags}, ensure_ascii=False)
    return (
        'curl -s -o /dev/null -w "%{http_code}" -X POST '
        '"https://script.google.com/macros/s/AKfycbxKYs0wD0y8/exec" '
        f"-H \"Content-Type: application/json\" -d \"$(cat <<'JSON'\n{body}\nJSON\n)\""
    )


class LedgerRepoTest(unittest.TestCase):
    def test_repo_present_passes(self):
        for tags in ("Repo=hub,Service=hub,Billing=commission,Name=hub-redis-prd",
                     "Service=shared,Repo=infra", " Repo = pension-plus-core "):
            self.assertIsNone(ledger_repo_problem(ledger_post_with_tags(tags)), tags)

    def test_missing_or_placeholder_repo_is_a_problem(self):
        for tags in ("Service=hub,Billing=commission", "Repo=,Service=hub", "",
                     "<Service=...,Billing=...,Name=...>", "Repo=<레포>,Service=hub", "NotRepo=hub"):
            self.assertIn("Repo", ledger_repo_problem(ledger_post_with_tags(tags)), tags)

    def test_unmanaged_is_a_problem(self):
        self.assertIn("unmanaged", ledger_repo_problem(ledger_post_with_tags("Repo=unmanaged,Service=hub")))
        self.assertIn("unmanaged", ledger_repo_problem(ledger_post_with_tags("Repo=Unmanaged")))

    def test_body_without_tags_field_is_a_problem(self):
        self.assertIn("tags", ledger_repo_problem(LEDGER_POST_NO_TAGS))
        self.assertIn("tags", ledger_repo_problem(LEDGER_POST_NO_TAGS.replace("-d '{\"by\":\"a\"}'", "-d @body.json")))

    def test_skill_template_placeholder_is_a_problem(self):
        self.assertIn("Repo", ledger_repo_problem(ledger_post_with_tags("<Repo=...,Service=...,Billing=...,Name=...>")))


class PreToolUseHookTest(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()

    def run_pre(self, command):
        return run_hook("pre_tool_use.py", {
            "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command},
        }, self.data)

    def test_ledger_post_without_repo_is_denied(self):
        out = self.run_pre(ledger_post_with_tags("Service=hub,Billing=commission"))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("Repo", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_ledger_post_with_unmanaged_is_denied(self):
        out = self.run_pre(ledger_post_with_tags("Repo=unmanaged,Service=hub"))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_ledger_post_with_repo_passes(self):
        self.assertIsNone(self.run_pre(ledger_post_with_tags("Repo=hub,Service=hub,Billing=commission")))

    def test_other_commands_pass(self):
        for command in ("aws ec2 run-instances --instance-type m5.large", "curl -s https://example.com/exec",
                        "echo script.google.com/macros/s/AKfy/exec"):
            self.assertIsNone(self.run_pre(command), command)

    def test_malformed_stdin_passes(self):
        self.assertIsNone(run_hook("pre_tool_use.py", None, self.data, raw_stdin="{not json"))
        self.assertIsNone(run_hook("pre_tool_use.py", None, self.data, raw_stdin="[]"))
        self.assertIsNone(run_hook("pre_tool_use.py", {"tool_input": "x"}, self.data))


class PostToolUseHookTest(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()

    def test_creation_adds_context(self):
        out = run_hook("post_tool_use.py", {
            "hook_event_name": "PostToolUse", "tool_name": "Bash",
            "tool_input": {"command": "aws ec2 run-instances --instance-type m5.4xlarge"},
        }, self.data)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertIn("aws-cost-ledger-entry", out["hookSpecificOutput"]["additionalContext"])
        self.assertIn("run-instances", out["hookSpecificOutput"]["additionalContext"])

    def test_read_only_emits_nothing(self):
        out = run_hook("post_tool_use.py", {
            "hook_event_name": "PostToolUse", "tool_name": "Bash",
            "tool_input": {"command": "aws ec2 describe-instances"},
        }, self.data)
        self.assertIsNone(out)

    def test_malformed_stdin_emits_nothing(self):
        self.assertIsNone(run_hook("post_tool_use.py", None, self.data, raw_stdin="{not json"))
        self.assertIsNone(run_hook("post_tool_use.py", None, self.data, raw_stdin="[]"))
        self.assertIsNone(run_hook("post_tool_use.py", {"tool_input": "x"}, self.data))


class StopHookTest(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()
        self.transcript = str(Path(self.data) / "t.jsonl")

    def stop(self, session="s1", active=False):
        return run_hook("stop.py", {
            "hook_event_name": "Stop", "session_id": session,
            "transcript_path": self.transcript, "stop_hook_active": active,
        }, self.data)

    def test_create_without_record_blocks(self):
        write_transcript(self.transcript, ["ls", "aws rds create-db-instance --db-instance-identifier x"])
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("create-db-instance", out["reason"])

    def test_create_then_record_allows(self):
        write_transcript(self.transcript, ["aws rds create-db-instance --db-instance-identifier x", LEDGER_POST])
        self.assertIsNone(self.stop())

    def test_post_without_repo_does_not_count_as_record(self):
        write_transcript(self.transcript, ["aws rds create-db-instance --db-instance-identifier x", LEDGER_POST_NO_TAGS])
        self.assertEqual(self.stop()["decision"], "block")

    def test_post_with_unmanaged_repo_does_not_count_as_record(self):
        write_transcript(self.transcript, ["aws rds create-db-instance --db-instance-identifier x",
                                           ledger_post_with_tags("Repo=unmanaged,Service=hub")])
        self.assertEqual(self.stop()["decision"], "block")

    def test_create_after_record_blocks(self):
        write_transcript(self.transcript, [
            "aws rds create-db-instance --db-instance-identifier x", LEDGER_POST, "eksctl scale nodegroup --nodes 5",
        ])
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("eksctl scale", out["reason"])
        self.assertNotIn("create-db-instance", out["reason"])

    def test_stop_hook_active_allows(self):
        write_transcript(self.transcript, ["terraform apply -auto-approve"])
        self.assertIsNone(self.stop(active=True))

    def test_failed_create_allows(self):
        failed = "aws ec2 run-instances --instance-type m5.large"
        write_transcript(self.transcript, [failed], failed={failed})
        self.assertIsNone(self.stop())

    def test_blocks_once_per_command(self):
        write_transcript(self.transcript, ["terraform apply"])
        self.assertEqual(self.stop()["decision"], "block")
        self.assertIsNone(self.stop())
        write_transcript(self.transcript, ["terraform apply", "aws ec2 allocate-address"])
        out = self.stop()
        self.assertIn("allocate-address", out["reason"])
        self.assertNotIn("terraform apply", out["reason"])

    def test_block_state_is_per_session(self):
        write_transcript(self.transcript, ["terraform apply"])
        self.assertEqual(self.stop(session="a")["decision"], "block")
        self.assertEqual(self.stop(session="b")["decision"], "block")

    def test_no_aws_activity_allows(self):
        write_transcript(self.transcript, ["git status", "npm test"])
        self.assertIsNone(self.stop())

    def test_malformed_and_non_dict_lines_are_skipped(self):
        write_transcript(self.transcript, ["aws ec2 allocate-address"])
        with open(self.transcript, "a", encoding="utf-8") as f:
            f.write("{not json\n[]\n42\n\"text\"\n")
            f.write(json.dumps({"message": {"content": [
                {"type": "tool_use", "id": "x", "name": "Bash", "input": "not a dict"},
            ]}}) + "\n")
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("allocate-address", out["reason"])

    def test_non_utf8_bytes_do_not_hide_creates(self):
        write_transcript(self.transcript, ["aws ec2 allocate-address"])
        with open(self.transcript, "ab") as f:
            f.write(b'{"message": {"content": [{"type": "text", "text": "\xff\xfe"}]}}\n')
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("allocate-address", out["reason"])

    def test_non_dict_message_is_skipped(self):
        write_transcript(self.transcript, ["aws ec2 allocate-address"])
        with open(self.transcript, "a", encoding="utf-8") as f:
            f.write('{"message": "plain string"}\n{"message": ["list"]}\n')
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("allocate-address", out["reason"])

    def test_corrupt_state_file_is_reset(self):
        write_transcript(self.transcript, ["terraform apply"])
        state_path(self.data, "s1").write_text("{corrupt")
        self.assertEqual(self.stop()["decision"], "block")
        self.assertEqual(json.loads(state_path(self.data, "s1").read_text()), ["toolu_0"])
        self.assertIsNone(self.stop())

    def test_non_string_session_id(self):
        write_transcript(self.transcript, ["terraform apply"])
        self.assertEqual(self.stop(session=12345)["decision"], "block")
        self.assertTrue(state_path(self.data, 12345).exists())

    def test_session_ids_that_sanitise_alike_do_not_share_state(self):
        write_transcript(self.transcript, ["terraform apply"])
        self.assertEqual(self.stop(session="a.b")["decision"], "block")
        self.assertEqual(self.stop(session="a/b")["decision"], "block")
        self.assertNotEqual(state_path(self.data, "a.b"), state_path(self.data, "a/b"))

    def test_id_less_tool_use_blocks_once(self):
        write_transcript(self.transcript, ["terraform apply"], with_ids=False)
        self.assertEqual(self.stop()["decision"], "block")
        self.assertIsNone(self.stop())
        stored = json.loads(state_path(self.data, "s1").read_text())
        self.assertEqual(len(stored), 1)
        self.assertTrue(stored[0].startswith("cmd:"))

    def test_missing_transcript_path_allows(self):
        out = run_hook("stop.py", {"hook_event_name": "Stop", "session_id": "s1"}, self.data)
        self.assertIsNone(out)

    def test_unreadable_transcript_allows(self):
        self.transcript = str(Path(self.data) / "does-not-exist.jsonl")
        self.assertIsNone(self.stop())

    def test_malformed_stdin_allows(self):
        self.assertIsNone(run_hook("stop.py", None, self.data, raw_stdin="{not json"))

    def test_missing_plugin_data_still_blocks(self):
        write_transcript(self.transcript, ["terraform apply"])
        payload = {"hook_event_name": "Stop", "session_id": "s1",
                   "transcript_path": self.transcript, "stop_hook_active": False}
        out = run_hook("stop.py", payload, None)
        self.assertEqual(out["decision"], "block")
        self.assertEqual(sorted(p.name for p in Path(self.data).iterdir()), ["t.jsonl"])


if __name__ == "__main__":
    unittest.main()
