import { localized, type LocalizedText } from "./i18n";

export const PROMOTION_TARGET_STATES = [
  "accepted",
  "refuted",
  "obsolete"
] as const;

export type PromotionTargetState = (typeof PROMOTION_TARGET_STATES)[number];

export const PROMOTION_LABELS = {
  checkPromotion: localized("Check promotion", "检查晋升"),
  promotionReadiness: localized("Promotion readiness", "晋升检查"),
  ready: localized("Ready for promotion", "可晋升"),
  blocked: localized("Blocked", "阻断"),
  currentStatus: localized("Current status", "当前状态"),
  reviewState: localized("Review state", "审阅状态"),
  gateChecks: localized("Gate checks", "准入检查"),
  dependencies: localized("Dependencies", "依赖项"),
  sourceMetadata: localized("Source metadata", "来源元数据"),
  verifierChecks: localized("Verifier checks", "验证器检查"),
  impact: localized("Impact", "影响"),
  missingRequirements: localized("Missing requirements", "缺失项"),
  preview: localized("Preview promotion", "预览晋升"),
  targetState: localized("Target state", "目标状态"),
  readinessJson: localized("Readiness JSON", "就绪度 JSON"),
  authorityNotice: localized(
    "Promotion readiness is advisory. It does not write accepted artifacts, pass gates, or grant promotion authority.",
    "晋升检查只是建议，不会写入 accepted 工件、通过准入检查或授予晋升权限。"
  ),
  liveLocalRequired: localized(
    "Promotion readiness requires live local mode to check fresh validation and gate results.",
    "晋升检查需要实时本地模式，以获取最新验证和准入结果。"
  )
} as const;

export interface PromotionPreviewFormInput {
  artifactId: string;
  targetState: string;
}

export interface PromotionPreviewPayload {
  artifact_id: string;
  target_state: PromotionTargetState;
}

export interface PromotionReason {
  code: string;
  severity: string;
  message: string;
  artifact_id?: string;
  source_path?: string;
  gate_id?: string;
  verifier?: string;
  status?: string;
}

export interface PromotionReasonGroup {
  key: string;
  label: LocalizedText;
  items: PromotionReason[];
}

const GROUPS = [
  {
    key: "status",
    label: PROMOTION_LABELS.currentStatus,
    codes: ["draft_status", "already_accepted", "not_promotable_status"]
  },
  {
    key: "review",
    label: PROMOTION_LABELS.reviewState,
    codes: ["missing_review"]
  },
  {
    key: "dependencies",
    label: PROMOTION_LABELS.dependencies,
    codes: ["dependency_risk", "private_dependency"]
  },
  {
    key: "source_metadata",
    label: PROMOTION_LABELS.sourceMetadata,
    codes: ["missing_source_metadata"]
  },
  {
    key: "verifier_checks",
    label: PROMOTION_LABELS.verifierChecks,
    codes: ["failed_verifier", "skipped_verifier", "formal_link_policy"]
  },
  {
    key: "gate_checks",
    label: PROMOTION_LABELS.gateChecks,
    codes: ["gate_blocker", "repository_gate_blocker"]
  },
  {
    key: "impact",
    label: PROMOTION_LABELS.impact,
    codes: [
      "checked_counterexample_evidence",
      "strategy_open_blocker",
      "unresolved_failure_memory"
    ]
  }
] as const;

export function promotionReadinessEndpoint(artifactId: string): string {
  return `/api/artifacts/${encodeURIComponent(artifactId)}/promotion-readiness`;
}

export function promotionPreviewEndpoint(artifactId: string): string {
  return `/api/artifacts/${encodeURIComponent(artifactId)}/promotion/preview`;
}

export function buildPromotionPreviewPayload(
  input: PromotionPreviewFormInput
): PromotionPreviewPayload {
  const targetState = input.targetState.trim();
  if (!PROMOTION_TARGET_STATES.includes(targetState as PromotionTargetState)) {
    throw new Error("unsupported promotion target state");
  }
  return {
    artifact_id: input.artifactId.trim(),
    target_state: targetState as PromotionTargetState
  };
}

export function groupPromotionReasons(
  reasons: PromotionReason[]
): PromotionReasonGroup[] {
  const used = new Set<PromotionReason>();
  const groups = GROUPS.map((group) => ({
    key: group.key,
    label: group.label,
    items: reasons.filter((reason) => group.codes.includes(reason.code as never))
  })).filter((group) => group.items.length > 0);
  for (const group of groups) {
    for (const item of group.items) {
      used.add(item);
    }
  }
  const other = reasons.filter((reason) => !used.has(reason));
  if (other.length > 0) {
    groups.push({
      key: "other",
      label: PROMOTION_LABELS.missingRequirements,
      items: other
    });
  }
  return groups;
}
