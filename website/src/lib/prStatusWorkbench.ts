import { localized } from "./i18n";

export const PR_STATUS_ENDPOINT = "/api/forge/pr-status";

export const PR_STATUS_LABELS = {
  title: localized("Pull request status", "拉取请求状态"),
  workflow: localized("Forge review workflow", "Forge 审查流程"),
  prNumber: localized("PR number", "PR 编号"),
  base: localized("Base", "目标分支"),
  head: localized("Head branch", "提交分支"),
  sync: localized("Sync status", "同步状态"),
  viewGithub: localized("View GitHub PR", "查看 GitHub PR"),
  githubDisconnected: localized(
    "GitHub disconnected",
    "GitHub 连接断开"
  ),
  notSynced: localized("Not synced", "未同步"),
  githubCollaboration: localized(
    "GitHub collaboration",
    "GitHub 协作"
  ),
  cosheafReview: localized("Cosheaf review", "Cosheaf 审查"),
  checklist: localized("Checklist", "清单"),
  comments: localized("Comments", "评论"),
  status: localized("Status", "状态"),
  noComments: localized("No comments loaded", "未加载评论"),
  noChecklist: localized("No checklist items", "无清单项"),
  notImported: localized("Not imported", "未导入"),
  ci: localized("CI", "CI"),
  gate: localized("Gate", "准入检查"),
  updated: localized("Updated", "更新时间")
} as const;

export interface PrStatusInput {
  number?: string;
  base?: string;
  head?: string;
}

export interface PrStatusPayload {
  pr_status?: {
    github_auth_available?: boolean;
    source_of_truth?: string;
    updated_at?: string;
    pr?: Record<string, unknown>;
    linked_issue?: Record<string, unknown> | null;
    checklist?: ChecklistPayload;
    ci?: StatusGroupPayload;
    gate?: StatusGroupPayload;
    cosheaf_review?: Record<string, unknown>;
    github_reviews?: Array<Record<string, unknown>>;
    review_comments?: Array<Record<string, unknown>>;
    warnings?: string[];
  };
}

export interface ChecklistPayload {
  completed?: number;
  total?: number;
  items?: Array<{ text?: string; checked?: boolean }>;
}

export interface StatusGroupPayload {
  status?: string;
  checks?: Array<Record<string, unknown>>;
}

export function hasPrSelector(input: PrStatusInput): boolean {
  return Boolean(input.number?.trim() || input.head?.trim());
}

export function buildPrStatusUrl(apiBase: string, input: PrStatusInput): URL {
  const url = new URL(PR_STATUS_ENDPOINT, apiBase);
  for (const [key, value] of Object.entries(input)) {
    const normalized = value?.trim();
    if (normalized) {
      url.searchParams.set(key, normalized);
    }
  }
  return url;
}

export function checklistSummary(checklist: ChecklistPayload | undefined): string {
  const completed = Number(checklist?.completed ?? 0);
  const total = Number(checklist?.total ?? 0);
  return `${completed} / ${total}`;
}

export function githubReviewIsCosheafAuthority(): false {
  return false;
}

export function visibleCommentCount(payload: PrStatusPayload, limit = 3): number {
  return Math.min(payload.pr_status?.review_comments?.length ?? 0, limit);
}

export function statusTone(status: string | undefined): "good" | "warning" | "bad" | "neutral" {
  const normalized = (status ?? "").toLowerCase();
  if (["success", "clean", "mergeable", "approved", "open"].includes(normalized)) {
    return "good";
  }
  if (["failure", "blocked", "dirty", "changes_requested", "closed"].includes(normalized)) {
    return "bad";
  }
  if (["pending", "queued", "unknown", "not_imported"].includes(normalized)) {
    return "warning";
  }
  return "neutral";
}

export function textValue(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}
