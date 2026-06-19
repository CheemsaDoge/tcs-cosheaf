import { localized } from "./i18n";

export const REVIEW_DECISION_ENDPOINTS = {
  preview: "/api/reviews/decisions/preview",
  create: "/api/reviews/decisions/create"
} as const;

export const HUMAN_REVIEW_DECISIONS = [
  "accept_for_private_use",
  "accept_for_public_candidate",
  "changes_requested",
  "keep_draft",
  "refute_candidate",
  "mark_obsolete"
] as const;

export type HumanReviewDecision = (typeof HUMAN_REVIEW_DECISIONS)[number];

export const HUMAN_REVIEW_DECISION_OPTIONS = [
  {
    value: "accept_for_private_use",
    label: localized("Accept for private use", "接受用于私有用途")
  },
  {
    value: "accept_for_public_candidate",
    label: localized("Accept as public candidate", "接受为公开候选")
  },
  {
    value: "changes_requested",
    label: localized("Request changes", "要求修改")
  },
  {
    value: "keep_draft",
    label: localized("Keep as draft", "保持草稿")
  },
  {
    value: "refute_candidate",
    label: localized("Refute candidate", "驳回候选")
  },
  {
    value: "mark_obsolete",
    label: localized("Mark obsolete", "标记过时")
  }
] as const;

export const REVIEW_DECISION_LABELS = {
  recordReview: localized("Record review decision", "记录审阅决策"),
  reviewDecision: localized("Review decision", "审阅决策"),
  preview: localized("Preview decision", "预览决策"),
  confirm: localized("Confirm write", "确认写入"),
  artifactId: localized("Artifact ID", "工件 ID"),
  reviewer: localized("Reviewer", "审阅者"),
  decision: localized("Decision", "决策"),
  reviewNotes: localized("Review notes", "审阅笔记"),
  scope: localized("Scope", "范围"),
  limitations: localized("Limitations", "局限性"),
  dependenciesChecked: localized("Dependencies checked", "已检查依赖"),
  sourcesChecked: localized("Sources checked", "已检查来源"),
  evidenceChecked: localized("Evidence checked", "已检查证据"),
  gateStateAcknowledged: localized(
    "Gate state acknowledged",
    "已确认准入状态"
  ),
  humanConfirmation: localized(
    "I am recording a human review decision",
    "我正在记录人工审阅决策"
  ),
  previewOutput: localized("Decision preview", "决策预览"),
  authorityNotice: localized(
    "Human review decisions record reviewer judgment and may update review state. They do not automatically grant accepted status or promotion authority. AI/Codex cannot be recorded as reviewer.",
    "人工审阅决策记录审阅者判断，并可能更新审阅状态；它不会自动授予 accepted 状态或晋升权限。AI/Codex 不可作为审阅者。"
  )
} as const;

export interface ReviewDecisionFormInput {
  artifactId: string;
  reviewer: string;
  decision: HumanReviewDecision;
  reviewNotes: string;
  scope: string;
  limitations: string;
  dependenciesChecked: boolean;
  sourcesChecked: boolean;
  evidenceChecked: boolean;
  gateStateAcknowledged: boolean;
  explicitHumanConfirmation: boolean;
}

export interface ReviewDecisionPayload {
  artifact_id: string;
  reviewer: string;
  decision: HumanReviewDecision;
  review_notes: string;
  scope: string;
  limitations: string;
  dependencies_checked: boolean;
  sources_checked: boolean;
  evidence_checked: boolean;
  gate_state_acknowledged: boolean;
  explicit_human_confirmation: boolean;
  confirm?: true;
}

export interface ReviewDecisionConfirmState {
  previewLoaded: boolean;
  reviewer: string;
  reviewNotes: string;
  explicitHumanConfirmation: boolean;
}

export function buildReviewDecisionPayload(
  input: ReviewDecisionFormInput,
  options: { confirm?: true } = {}
): ReviewDecisionPayload {
  const payload: ReviewDecisionPayload = {
    artifact_id: input.artifactId.trim(),
    reviewer: input.reviewer.trim(),
    decision: input.decision,
    review_notes: input.reviewNotes.trim(),
    scope: input.scope.trim() || "private",
    limitations: input.limitations.trim(),
    dependencies_checked: input.dependenciesChecked,
    sources_checked: input.sourcesChecked,
    evidence_checked: input.evidenceChecked,
    gate_state_acknowledged: input.gateStateAcknowledged,
    explicit_human_confirmation: input.explicitHumanConfirmation
  };
  if (options.confirm) {
    payload.confirm = true;
  }
  return payload;
}

export function canConfirmReviewDecision(
  input: ReviewDecisionConfirmState
): boolean {
  return (
    input.previewLoaded &&
    Boolean(input.reviewer.trim()) &&
    Boolean(input.reviewNotes.trim()) &&
    input.explicitHumanConfirmation
  );
}
