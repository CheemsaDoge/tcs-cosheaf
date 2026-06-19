import { localized } from "./i18n";

export const ISSUE_ACTION_ENDPOINTS = {
  previewCreate: "/api/issues/preview-create",
  create: "/api/issues/create",
  previewUpdate: (id: string) =>
    `/api/issues/${encodeURIComponent(id)}/preview-update`,
  update: (id: string) => `/api/issues/${encodeURIComponent(id)}/update`,
  previewClose: (id: string) =>
    `/api/issues/${encodeURIComponent(id)}/preview-close`,
  close: (id: string) => `/api/issues/${encodeURIComponent(id)}/close`
} as const;

export const ISSUE_WORKBENCH_LABELS = {
  createIssue: localized("New issue", "新建议题"),
  editIssue: localized("Edit issue", "编辑议题"),
  closeIssue: localized("Close issue", "关闭议题"),
  preview: localized("Preview changes", "预览变更"),
  confirm: localized("Confirm write", "确认写入"),
  cancel: localized("Cancel", "取消"),
  issueId: localized("Issue ID", "议题 ID"),
  title: localized("Title", "标题"),
  summary: localized("Summary", "摘要"),
  scope: localized("Scope", "范围"),
  labels: localized("Labels", "标签"),
  relatedArtifacts: localized("Related artifacts", "相关工件"),
  relatedSources: localized("Sources", "来源"),
  authors: localized("Authors", "作者"),
  closeReason: localized("Close reason", "关闭原因"),
  previewDiff: localized("Change preview", "变更预览")
} as const;

export interface IssueFormInput {
  issueId: string;
  title: string;
  summary: string;
  scope: string;
  labels: string;
  relatedArtifacts: string;
  relatedSources: string;
  authors: string;
}

export interface IssueActionPayload {
  issue_id: string;
  title: string;
  summary?: string;
  scope: "private" | "public";
  labels: string[];
  related_artifacts: string[];
  related_sources: string[];
  authors: string[];
  confirm?: true;
}

export function parseDelimitedList(value: string): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const item of value.split(/[,\n;]/)) {
    const normalized = item.trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
}

export function buildIssueActionPayload(
  input: IssueFormInput,
  options: { confirm?: true } = {}
): IssueActionPayload {
  const payload: IssueActionPayload = {
    issue_id: input.issueId.trim(),
    title: input.title.trim(),
    scope: input.scope === "public" ? "public" : "private",
    labels: parseDelimitedList(input.labels),
    related_artifacts: parseDelimitedList(input.relatedArtifacts),
    related_sources: parseDelimitedList(input.relatedSources),
    authors: parseDelimitedList(input.authors)
  };
  const summary = input.summary.trim();
  if (summary) {
    payload.summary = summary;
  }
  if (options.confirm) {
    payload.confirm = true;
  }
  return payload;
}
