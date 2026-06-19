import type { SiteData } from "./siteData";

export const PREVIEW_API_BASE = "http://127.0.0.1:8765";
export const PREVIEW_AUTHORITY_WARNING =
  "Preview actions are dry-run planning output only; they do not write repository files, call GitHub, store tokens, mark human review, pass gates, accept artifacts, or promote knowledge.";

export type PreviewActionId =
  | "local-issue"
  | "github-issue"
  | "github-pr"
  | "review-packet";

export interface PreviewRequest {
  id: PreviewActionId;
  label: string;
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
      label: "Local issue",
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
      label: "GitHub issue",
      endpoint: "/api/forge/issues/preview",
      method: "POST",
      payload: {
        source_path: issueSourcePath
      }
    },
    {
      id: "github-pr",
      label: "Pull request",
      endpoint: "/api/forge/prs/preview",
      method: "POST",
      payload: {
        base,
        head
      }
    },
    {
      id: "review-packet",
      label: "Review packet",
      endpoint: "/api/forge/review-packets/preview",
      method: "POST",
      payload: {
        issue_id: issue.id
      }
    }
  ];
}
