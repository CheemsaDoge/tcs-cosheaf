import type { SiteData } from "./siteData";
import { type LocalizedText, localized } from "./i18n";

export const PREVIEW_API_BASE = "http://127.0.0.1:8765";
export const PREVIEW_AUTHORITY_WARNING = localized(
  "Preview actions are dry-run plans only. They do not write repository files, call GitHub, store tokens, mark human review, pass gates, accept artifacts, or promote knowledge.",
  "预览动作只返回 dry-run 计划，不会写仓库文件、调用 GitHub、保存 token、记录人工审阅、通过准入检查、接受工件或提升知识。"
);

export type PreviewActionId =
  | "local-issue"
  | "github-issue"
  | "github-pr"
  | "review-packet";

export interface PreviewRequest {
  id: PreviewActionId;
  label: LocalizedText;
  endpoint: string;
  method: "POST";
  payload: Record<string, unknown>;
}

export interface PreviewRefs {
  base?: string;
  head?: string;
}

export function buildPreviewRequests(
  data: SiteData,
  refs: PreviewRefs = {}
): PreviewRequest[] {
  const issue = data.issues.issues[0];
  const base = refs.base ?? "main";
  const head = refs.head ?? "website-preview-actions";
  const issueSourcePath = `issues/open/${issue.id}.yaml`;

  return [
    {
      id: "local-issue",
      label: localized("Local issue", "本地议题"),
      endpoint: "/api/forge/local-issues/preview",
      method: "POST",
      payload: {
        issue_id: "issue.website-preview.demo",
        title: "Preview local issue",
        summary: `Dry-run local issue plan for ${issue.id}.`,
        authors: ["website-preview"],
        labels: ["website-preview"],
        related_artifacts: issue.related_artifacts,
        related_sources: issue.related_sources,
        scope: issue.scope === "public" ? "public" : "private"
      }
    },
    {
      id: "github-issue",
      label: localized("GitHub issue", "GitHub 议题"),
      endpoint: "/api/forge/issues/preview",
      method: "POST",
      payload: {
        source_path: issueSourcePath
      }
    },
    {
      id: "github-pr",
      label: localized("Pull request", "拉取请求"),
      endpoint: "/api/forge/prs/preview",
      method: "POST",
      payload: {
        base,
        head
      }
    },
    {
      id: "review-packet",
      label: localized("Review packet", "审阅包"),
      endpoint: "/api/forge/review-packets/preview",
      method: "POST",
      payload: {
        issue_id: issue.id
      }
    }
  ];
}
