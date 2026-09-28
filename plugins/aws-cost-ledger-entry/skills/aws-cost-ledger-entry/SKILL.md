---
name: aws-cost-ledger-entry
description: 신규 AWS 인프라를 만들거나 기존 인프라를 확장할 때, 기재 항목(대상·이용 목적·시점·예상 비용 증가폭)을 산출해 비용 대장에 자동으로 기록하는 스킬. "인프라 만들었어", "리소스 추가했는데", "노드 늘렸어", "인스턴스 띄웠어", "RDS 만들어야 해", "용량 늘릴게", "디스크 늘려야 해", "비용 대장", "비용 공유", "예상 비용 얼마 나와", "terraform apply 했어" 같은 말이 나오거나, 신규 AWS 자원 생성·스케일업·스토리지 증설 맥락이면 반드시 이 스킬을 사용한다. 단순 조회·자원 삭제·기존 비용 분석에는 쓰지 않는다.
---

# 비용 대장 기재

신규 AWS 자원을 만들거나 늘릴 때, 대장 `인프라 변경 이력` 탭에 한 행을 남긴다.
나중에 경영지원이 "이 비용 왜 늘었냐" 고 물었을 때 답할 근거가 된다.

승인 절차가 아니다. 허들처럼 굴지 말고 빠르게 처리한다.

## 1. 항목 채우기

| 키 | 내용 |
|---|---|
| `by` | 작성자. 아래 명령으로 판별한다. 사용자에게 묻지 않는다 |
| `env` | `prd` 또는 `dev`. **추측 금지** — 틀리면 운영 변경으로 오해된다. 모르면 한 줄로 확인 |
| `target` | 서비스명 + 자원 타입 + 규모. 예: `EKS prd 노드그룹 m5.4xlarge 1대 증설` |
| `purpose` | 왜 필요한지 한 문장 |
| `when` | `YYYY-MM-DD`. 작업 전이면 예정일, 후면 적용일 |
| `delta` | 월 USD + 산정 근거. **모르면 비운다** — 지어낸 숫자가 빈칸보다 나쁘다 |
| `arn` | 만든 자원의 ARN. 여러 개면 쉼표로. 아직 안 만들었으면 비운다 |
| `tags` | 붙인 태그를 `키=값` 쉼표 구분으로. 예: `Billing=shared,Name=eks-onda-dev` |

작성자는 이 명령을 실제로 실행해서 얻는다. 추측하거나 대화 맥락에서 유추하지 않는다.

```bash
git config user.email
```

대화에 이미 있는 정보는 그대로 쓰고, 모르는 것만 묻는다.

### `arn` 을 꼭 채울 것

비용 데이터(HyperBilling CSV)에는 `resourceid` 가 ARN 으로 들어 있다. 대장에 같은
ARN 이 있으면 **"이 자원이 왜 생겼는지" 가 문자열 매칭으로 바로 붙는다.** 없으면
나중에 증감 표를 보며 사람이 눈으로 찾아야 한다.

만든 직후라면 생성 명령의 출력이나 `describe-*` 로 ARN 을 얻어 넣는다.
만들기 전 사전 공유라면 비워두고, 만든 뒤 한 행을 더 기재한다.

### 태그

붙일 태그는 최소 이 둘이다.

| 키 | 값 |
|---|---|
| `Billing` | `commission` / `subscription` / `shared` |
| `Name` | 사람이 알아볼 이름 |

`Billing` 은 수수료·구독·공유 중 무엇의 비용인지다. 판단이 안 서면 `shared` 로 두고
`tags` 에 그대로 적는다 — 대장에 남아 있으면 나중에 고칠 수 있다.

**붙이는 위치를 틀리면 태그가 조용히 사라진다.**

| 만드는 것 | 태그 넣을 곳 |
|---|---|
| EKS 노드그룹 | launch template `TagSpecifications` — 수동 태그는 ASG 재생성 때 사라진다 |
| ALB / Ingress | **yaml 어노테이션** — 수동 태그는 LB 컨트롤러가 reconcile 때 지운다 |
| 그 외 | 생성 명령의 `--tags`, 콘솔이면 생성 마법사의 태그 단계 |

`tags` 에는 **실제로 붙인 것만** 적는다. 붙이려다 만 것을 적으면 대장이 거짓이 된다.

## 2. 비용 산정

**AWS 공식 요금 기준으로 잡는다.** 온디맨드 단가 × 730시간(월)이 기본이다.

```bash
aws pricing get-products --service-code AmazonEC2 --region us-east-1 \
  --filters 'Type=TERM_MATCH,Field=instanceType,Value=m5.4xlarge' \
            'Type=TERM_MATCH,Field=location,Value=Asia Pacific (Seoul)' \
            'Type=TERM_MATCH,Field=operatingSystem,Value=Linux' \
            'Type=TERM_MATCH,Field=tenancy,Value=Shared' \
            'Type=TERM_MATCH,Field=preInstalledSw,Value=NA' \
            'Type=TERM_MATCH,Field=capacitystatus,Value=Used' \
  --max-results 1
```

`--service-code` 는 자원에 맞춰 바꾼다 — `AmazonRDS`, `AmazonEBS`, `AmazonS3`,
`AWSELB` 등. 조회 권한이 없으면 <https://calculator.aws> 로 산정하고 근거에 남긴다.

**인스턴스 단가만 세면 절반 이하로 잡게 된다.** 함께 세야 할 것:
EBS 볼륨과 gp3 프로비저닝 처리량·IOPS, 가용영역 간 데이터 전송, NAT 게이트웨이,
ELB 의 LCU, 스냅샷 보존, CloudWatch 로그 적재량. RDS·ElastiCache 는 스토리지·백업이
인스턴스 비용과 별개다.

근거를 값에 같이 적는다. 예: `월 $689 (m5.4xlarge 1대, 온디맨드 $0.944/hr × 730h)`.
근거가 없으면 나중에 그 숫자가 맞는지 아무도 다시 따져볼 수 없다.

## 3. 기재

보내기 전에 필수 5개(`by`·`env`·`target`·`purpose`·`when`)가 찼는지 확인한다.
**공백만 있는 값도 빈 값으로 본다** — 스크립트는 앞뒤 공백을 떼고 판단하므로, 여기서 통과시키면 서버에서 거부된다.
빠진 채 보내면 스크립트가 거부하는데, 응답으로는 성공과 구분되지 않아 기재된 줄 알고
넘어가게 된다.

```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 15 --connect-timeout 5 -X POST \
  "https://script.google.com/macros/s/AKfycbxKYs0wD0y8poc5fpZhXGkkbHZ02pf_Rl-1wF0oLbFGo_K-BDwVisSI1JBYhXdXgOKh/exec" \
  -H "Content-Type: application/json" -d "$(cat <<'JSON'
{ "by": "<작성자>", "env": "<prd 또는 dev>", "target": "<대상>",
  "purpose": "<목적 한 문장>", "when": "<YYYY-MM-DD>",
  "delta": "<월 $N (근거)>", "note": "",
  "arn": "<리소스 ARN, 여러 개면 쉼표>", "tags": "<Billing=...,Name=...>" }
JSON
)"
```

**응답 본문은 읽을 수 없다.** Apps Script 는 실행 후 결과 페이지로 리다이렉트하는데,
`-L` 로 따라가도 구글 드라이브 오류 HTML 이 돌아온다 (2026-09-22 확인). 그래서
스크립트가 뭐라고 답했는지는 알 방법이 없고, 판정은 상태 코드뿐이다.

| 코드 | 뜻 |
|---|---|
| `302` | 요청이 스크립트까지 도달했다. **재시도 금지** |
| `401`/`404` | 웹훅이 죽었다. **재시도하지 말고** 사용자에게 알린다 (조치는 jin.lee) |

**302 는 "도달"이지 "기재"가 아니다.** 필수 필드가 빠져 스크립트가 거부해도 302 다.
그래서 위의 사전 검사가 유일한 방어선이고, 그걸 건너뛰면 기재가 조용히 누락된다.

재시도도 하지 않는다. 302 를 실패로 읽고 다시 쏘면 중복 행이 쌓이는데, 스크립트가
append 전용이라 지우는 건 사람이 해야 한다. 기재 여부를 확인해야 하면 대장
`인프라 변경 이력` 탭을 직접 연다.

## 경계

- 자원을 대신 만들지 않는다. 산출과 기재까지다
- Slack·메일 공유는 하지 않는다.
- 금액을 추측으로 채우지 않는다
- 삭제·축소는 대상이 아니다
- 기존 대장 탭의 셀을 고치지 않는다. 웹훅은 전용 탭에 append 만 한다
- 1번 탭(계약 대장)에 올릴 신규 SaaS·용역 계약은 컬럼이 달라 웹훅으로 못 넣는다.
  붙여넣기용 행만 출력한다
