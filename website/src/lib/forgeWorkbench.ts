import { localized } from "./i18n";

export const FORGE_PR_FLOW_ENDPOINTS = {
  branchPreview: "/api/forge/branch/preview",
  branchCreate: "/api/forge/branch/create",
  commitPreview: "/api/forge/commit/preview",
  commitCreate: "/api/forge/commit/create",
  pushPreview: "/api/forge/push/preview",
  pushCreate: "/api/forge/push/create",
  prPreview: "/api/forge/pr/preview",
  prCreate: "/api/forge/pr/create"
} as const;

export const FORGE_PR_FLOW_LABELS = {
  title: localized("Submit pull request", "提交拉取请求"),
  workflow: localized("Forge workflow", "Forge 流程"),
  branch: localized("Branch", "分支"),
  commit: localized("Commit & Validate", "提交并验证"),
  push: localized("Push branch", "推送分支"),
  pr: localized("Create draft PR", "创建草稿 PR"),
  branchName: localized("Branch name", "分支名"),
  useExistingBranch: localized("Use existing branch", "使用已有分支"),
  createBranch: localized("Create branch", "新建分支"),
  commitMessage: localized("Commit message", "提交消息"),
  base: localized("Base", "目标分支"),
  head: localized("Head", "提交分支"),
  draft: localized("Draft", "草稿"),
  confirmPush: localized("Confirm push", "确认推送"),
  confirmPr: localized("Confirm PR", "确认 PR"),
  preview: localized("Preview", "预览"),
  result: localized("Result", "结果"),
  prUrl: localized("Pull request URL", "拉取请求链接"),
  manualStage: localized("Stage files outside web", "在网页外暂存文件")
} as const;

export interface BranchInput {
  branch: string;
}

export interface CommitInput {
  message: string;
}

export interface PushInput {
  head: string;
  confirm?: boolean;
}

export interface PrInput {
  base: string;
  head: string;
  draft?: boolean;
  confirm?: boolean;
}

export function isProtectedBranch(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  return normalized === "main" || normalized === "master";
}

export function canCreateBranch(input: BranchInput): boolean {
  const branch = input.branch.trim();
  return Boolean(branch) && !isProtectedBranch(branch);
}

export function canPushBranch(input: PushInput): boolean {
  const head = input.head.trim();
  return Boolean(input.confirm) && Boolean(head) && !isProtectedBranch(head);
}

export function canCreatePr(input: PrInput): boolean {
  const base = input.base.trim();
  const head = input.head.trim();
  return (
    Boolean(input.confirm) &&
    Boolean(base) &&
    Boolean(head) &&
    base !== head &&
    !isProtectedBranch(head)
  );
}

export function buildBranchCreatePayload(input: BranchInput): {
  branch: string;
  confirm: true;
} {
  return { branch: input.branch.trim(), confirm: true };
}

export function buildCommitCreatePayload(input: CommitInput): {
  message: string;
  confirm: true;
} {
  return { message: input.message.trim(), confirm: true };
}

export function buildPushCreatePayload(input: PushInput): {
  head: string;
  confirm: true;
} {
  return { head: input.head.trim(), confirm: true };
}

export function buildPrCreatePayload(input: PrInput): {
  base: string;
  head: string;
  draft: boolean;
  confirm: true;
} {
  return {
    base: input.base.trim(),
    head: input.head.trim(),
    draft: input.draft ?? true,
    confirm: true
  };
}

export function extractPrUrl(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "";
  }
  const action = (payload as Record<string, unknown>).forge_action;
  if (!action || typeof action !== "object") {
    return "";
  }
  const url = (action as Record<string, unknown>).github_pr_url;
  return typeof url === "string" ? url : "";
}
