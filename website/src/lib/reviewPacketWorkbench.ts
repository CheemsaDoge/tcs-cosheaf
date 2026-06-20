import { localized } from "./i18n";

export const REVIEW_PACKET_ENDPOINTS = {
  preview: "/api/reviews/packets/preview",
  create: "/api/reviews/packets/create"
} as const;

export const REVIEW_PACKET_LABELS = {
  generate: localized("Generate review summary", "生成审阅摘要"),
  reviewPacket: localized("Review summary", "审阅摘要"),
  preview: localized("Preview summary", "预览摘要"),
  confirm: localized("Confirm write", "确认写入"),
  focusArtifact: localized("Focus artifact", "聚焦工件"),
  relatedIssue: localized("Related issue", "相关议题"),
  allRelatedArtifacts: localized("All related artifacts", "全部相关工件"),
  packetPreview: localized("Summary preview", "摘要预览"),
  authorityNotice: localized(
    "Review summaries collect material for a human reviewer. They do not mark review complete, pass checks, or grant accepted status.",
    "审阅摘要只是给人工审阅者看的材料汇总，不代表审阅完成、检查通过或授予 accepted 状态。"
  )
} as const;

export interface ReviewPacketFormInput {
  issueId: string;
  artifactId: string;
}

export interface ReviewPacketPayload {
  issue_id: string;
  artifact_id?: string;
  confirm?: true;
}

export function buildReviewPacketPayload(
  input: ReviewPacketFormInput,
  options: { confirm?: true } = {}
): ReviewPacketPayload {
  const payload: ReviewPacketPayload = {
    issue_id: input.issueId.trim()
  };
  const artifactId = input.artifactId.trim();
  if (artifactId) {
    payload.artifact_id = artifactId;
  }
  if (options.confirm) {
    payload.confirm = true;
  }
  return payload;
}
