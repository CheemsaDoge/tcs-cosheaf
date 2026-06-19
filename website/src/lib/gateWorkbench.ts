import { localized } from "./i18n";

export const CHECK_RUN_ENDPOINTS = {
  validate: "/api/validate/run",
  gate: "/api/gate/run"
} as const;

export const CHECK_RUN_LABELS = {
  actions: localized("Run checks", "执行检查"),
  runValidate: localized("Run Validate", "运行验证"),
  runGate: localized("Run Gate", "运行准入检查"),
  result: localized("Result", "结果"),
  pass: localized("Pass", "通过"),
  fail: localized("Fail", "失败"),
  skipped: localized("Skipped", "已跳过")
} as const;

export interface CheckStatusSummary {
  pass: number;
  fail: number;
  skipped: number;
}

export function summarizeCheckStatuses(rows: unknown[]): CheckStatusSummary {
  const summary = { pass: 0, fail: 0, skipped: 0 };
  for (const row of rows) {
    const status = checkStatus(row);
    if (status === "pass") {
      summary.pass += 1;
    } else if (
      status === "skipped" ||
      status === "not_applicable" ||
      status === "unavailable" ||
      status === "not_run" ||
      status === "missing"
    ) {
      summary.skipped += 1;
    } else if (status) {
      summary.fail += 1;
    }
  }
  return summary;
}

function checkStatus(row: unknown): string {
  if (!row || typeof row !== "object") {
    return "";
  }
  const record = row as Record<string, unknown>;
  return String(record.status ?? record.result ?? record.verdict ?? record.state ?? "")
    .trim()
    .toLowerCase();
}
