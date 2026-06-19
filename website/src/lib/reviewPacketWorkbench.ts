import { localized } from "./i18n";

export const REVIEW_PACKET_ENDPOINTS = {
  preview: "/api/reviews/packets/preview",
  create: "/api/reviews/packets/create"
} as const;

export const REVIEW_PACKET_LABELS = {
  generate: localized("Generate review packet", "生成审阅包"),
  reviewPacket: localized("Review packet", "审阅包"),
  preview: localized("Preview packet", "预览审阅包"),
  confirm: localized("Confirm write", "确认写入"),
  focusArtifact: localized("Focus artifact", "聚焦工件"),
  relatedIssue: localized("Related issue", "相关议题"),
  allRelatedArtifacts: localized("All related artifacts", "全部相关工件"),
  packetPreview: localized("Packet preview", "审阅包预览"),
  authorityNotice: localized(
    "Review packets are informational context. They do not mark human review complete, pass gates, or grant accepted status.",
    "审阅包只是信息上下文，不代表人工审阅完成、准入检查通过或授予 accepted 状态。"
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
