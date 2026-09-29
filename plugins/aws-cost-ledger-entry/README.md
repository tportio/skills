# aws-cost-ledger-entry

신규 AWS 자원을 만들거나 늘릴 때, 비용 대장(`AI혁신본부_비용관리대장`)의
`인프라 변경 이력` 탭에 한 행을 남기는 스킬입니다.

## 설치

```
/plugin marketplace add git@github.com:tportio/skills.git   # 최초 1회
/plugin install aws-cost-ledger-entry@tport-skills
```

## 왜 만들었나

AWS 비용이 갑자기 늘었을 때 무엇 때문인지 답할 수 있어야 합니다.
인프라를 바꾼 사람이 그 자리에서 한 줄 남겨두면, 나중에 누가 묻든 대장만 보면 됩니다.
승인 절차가 아닙니다.

## 쓰는 법

따로 호출할 것 없습니다. 인프라를 만들거나 늘리는 맥락이면 Claude 가 알아서 씁니다.

```
노드그룹에 m5.4xlarge 한 대 더 붙였어
RDS 스토리지 500GB 로 늘려야 할 것 같은데
```

작성자·환경·대상·목적·시점·예상 비용·ARN·태그를 채워 기재합니다.
환경(prd/dev)을 대화에서 알 수 없으면 한 번 물어봅니다.

## 자동 강제 (hook)

플러그인을 설치하면 hook 두 개가 같이 켜집니다. 따로 등록할 것 없습니다.

- **PostToolUse**: Claude 가 생성·확장 명령을 실행하면, 바로 이 스킬을 쓰라고 Claude 에게 알립니다.
- **Stop**: 대장 기재 없이 턴을 끝내려 하면 한 번 막고 기재를 요구합니다. 같은 명령으로는 두 번 막지 않습니다.

감지하는 명령:

- `aws` 의 `create-*`·`allocate-*`·`restore-db-*`·`run-instances`·`request-spot-instances`
- `aws` 의 확장 명령: `modify-db-instance`·`modify-db-cluster`·`modify-volume`·`modify-instance-attribute`·
  `modify-cache-cluster`·`modify-replication-group`·`increase-replica-count`·`update-nodegroup-config`·
  `set-desired-capacity`·`update-auto-scaling-group`·`update-broker-storage`·`update-broker-type`·
  `opensearch update-domain-config`·`es update-elasticsearch-domain-config`·`ecs update-service --desired-count`
- `eksctl create`·`eksctl scale`, `terraform apply`·`tofu apply`
- `$(...)`·`bash -c`·`ssh host '...'`·`for/if` 안의 명령도 봅니다. 따옴표 안 문자열과 heredoc 본문은 보지 않습니다.

감지하지 않는 명령:

- 그 자체로 비용이 없는 생성: `create-tags`·`create-security-group`·`create-key-pair`·`create-launch-template(-version)`·
  `create-placement-group`·`create-network-acl(-entry)`·`create-route-table`·`create-route`·`create-subnet`·
  `create-internet-gateway`·`create-db-subnet-group`·`create-db-(cluster-)parameter-group`·
  `create-cache-subnet-group`·`create-cache-parameter-group`·`create-target-group`·`create-listener`·
  `create-rule`·`create-log-stream`
- `iam`·`sts`·`sso`·`sso-oidc`·`organizations` 서비스, `--dry-run`·`help`, `terraform plan`·`apply -destroy`
- 실패한 명령

알아둘 것:

- Claude 가 실행한 명령만 보입니다. 콘솔 작업이나 Claude 밖에서 돌린 `terraform apply` 는 감지하지 못합니다.
- 대장 POST 가 한 번 나가면 그 전의 생성 명령은 모두 기재된 것으로 봅니다. POST 가 실패해도 마찬가지입니다.
- `python3` 가 PATH 에 있어야 합니다. 없으면 hook 이 오류를 내고 강제가 동작하지 않습니다.

감지 규칙은 `hooks/ledger_patterns.py` 에 있습니다. 테스트는 레포 루트에서 이렇게 돌립니다.

```
python3 -B -m unittest discover -s plugins/aws-cost-ledger-entry/tests -p 'test_*.py'
```

## 참고

- 기재는 대장 시트에 붙은 Apps Script 웹훅으로 합니다. 코드는 `apps-script.gs` 에 사본이 있고, 정본은 시트입니다.
- 웹훅은 행 추가만 합니다. 읽기·수정·삭제 함수가 없습니다.
- 이 레포는 Public 이라 웹훅 URL 이 공개돼 있습니다. 대장에 이상한 행이 쌓이면
  **Apps Script 에서 새 배포를 만들어 옛 URL 을 죽이고**, 스킬의 URL 만 바꾸면 됩니다.
  SKILL.md 에서 URL 을 지우는 건 회수가 아닙니다 — git 히스토리에 남습니다.
- 스크립트를 고치면 시트 쪽에서 **배포 관리 → 편집 → 버전 "새 버전" → 배포** 까지 해야 반영됩니다.
- 관리자: jin.lee
