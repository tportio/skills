/**
 * 비용 대장 — 인프라 변경 이력 기재 웹훅
 *
 * 설치: 대장 시트 > 확장 프로그램 > Apps Script > 이 코드 붙여넣기 > 저장
 *       > 배포 > 배포 관리 > 편집 > 버전 "새 버전" > 배포
 *         (실행 계정: 나 / 액세스 권한: 모든 사용자)
 *
 * 인증은 URL 자체다. URL 을 아는 쪽만 기재할 수 있고, 할 수 있는 일은
 * 전용 탭에 행 추가 하나뿐이다. 읽기·수정·삭제 함수를 두지 않는 이유가 그것이다.
 * URL 이 샜다고 판단되면 새 배포를 만들어 URL 을 갈고 스킬만 다시 배포하면 된다.
 */

const TAB = '인프라 변경 이력';
// 열은 반드시 끝에만 추가한다. 중간에 끼우면 기존 행의 값이 다른 헤더 밑으로 밀린다.
const HEADER = ['기재일시', '작성자', '환경', '대상', '이용 목적', '적용 시점', '예상 비용 증가폭', '비고', '리소스 ARN', '태그'];

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return json({ ok: false, error: 'no body' });
    }
    const b = JSON.parse(e.postData.contents);
    if (!b || typeof b !== 'object' || Array.isArray(b)) {
      return json({ ok: false, error: 'invalid body' });
    }

    for (const f of ['by', 'env', 'target', 'purpose', 'when']) {
      if (!b[f] || !String(b[f]).trim()) {
        return json({ ok: false, error: 'missing field: ' + f });
      }
    }

    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sh = ss.getSheetByName(TAB);
    if (!sh) {
      sh = ss.insertSheet(TAB);
      sh.appendRow(HEADER);
      sh.setFrozenRows(1);
    } else {
      // 열이 늘어난 버전으로 배포됐을 때 헤더를 스스로 맞춘다.
      // 사람이 시트에서 열을 추가할 필요가 없고, 기존 행은 건드리지 않는다.
      // getLastColumn() 으로 판단하지 않는 이유 — 누가 우측에 메모를 적어두면
      // 이미 열 수가 차 있어 보정이 건너뛰어지고, 값이 엉뚱한 헤더 밑으로 들어간다.
      const rng = sh.getRange(1, 1, 1, HEADER.length);
      const cur = rng.getValues()[0];
      if (HEADER.some(function (h, i) { return cur[i] !== h; })) {
        rng.setValues([HEADER]);
      }
    }

    const delta = String(b.delta == null ? '' : b.delta).trim();

    sh.appendRow([
      Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm'),
      safe(b.by), safe(b.env), safe(b.target), safe(b.purpose), safe(b.when),
      safe(delta === '' ? '(미산정)' : delta),
      safe(b.note),
      safe(b.arn), safe(b.tags)
    ]);

    return json({ ok: true, row: sh.getLastRow() });
  } catch (err) {
    // 예외 문자열을 그대로 돌려주면 구현이 드러난다. 인증 없는 엔드포인트라 더 그렇다.
    return json({ ok: false, error: 'internal error' });
  }
}

/**
 * `=`, `+`, `-`, `@` 로 시작하는 값은 시트가 수식으로 해석한다.
 * 웹훅에 인증이 없으므로 `=IMPORTDATA(...)` 같은 값이 들어오면 대장에서 실행된다.
 * 앞에 작은따옴표를 붙여 문자열로 고정한다.
 *
 * 선행 공백·탭·개행도 함께 본다. 시트나 CSV 를 여는 다른 도구가 앞 공백을
 * 떼고 해석하면 우회되기 때문이다.
 */
function safe(v) {
  const s = String(v == null ? '' : v);
  return /^[\s=+\-@|]/.test(s) ? "'" + s : s;
}

function json(o) {
  return ContentService.createTextOutput(JSON.stringify(o))
    .setMimeType(ContentService.MimeType.JSON);
}
