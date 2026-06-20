import { type LocalizedText, localized } from "./i18n";

export type RuntimeMode = "static-demo" | "live-local" | "hosted-workspace";

export interface RuntimeModeInput {
  mode?: string;
  dev?: boolean;
  apiBase?: string;
  fallbackReason?: string;
  localActor?: string;
  localActorIsAuth?: boolean;
}

export interface RuntimeMetadata {
  mode: RuntimeMode;
  label: LocalizedText;
  label_en: string;
  label_zh: string;
  api_base: string;
  fallback: boolean;
  fallback_reason?: string;
  local_actor?: string;
  local_actor_is_auth: boolean;
}

export const DEFAULT_API_BASE = "http://127.0.0.1:8765";

const LABELS: Record<RuntimeMode, { en: string; zh: string }> = {
  "static-demo": {
    en: "Sample mode",
    zh: "只读样例"
  },
  "live-local": {
    en: "Live local mode",
    zh: "本地实时模式"
  },
  "hosted-workspace": {
    en: "Hosted workspace mode",
    zh: "托管工作区模式"
  }
};

export function runtimeModeLabel(mode: RuntimeMode): LocalizedText {
  const label = LABELS[mode];
  return localized(label.en, label.zh);
}

export function decideRuntimeMode(input: RuntimeModeInput = {}): RuntimeMetadata {
  const requested = (input.mode ?? "auto").trim().toLowerCase();
  const mode = normalizeMode(requested, Boolean(input.dev));
  const label = LABELS[mode];
  return {
    mode,
    label: runtimeModeLabel(mode),
    label_en: label.en,
    label_zh: label.zh,
    api_base: normalizeApiBase(input.apiBase),
    fallback: Boolean(input.fallbackReason),
    fallback_reason: input.fallbackReason,
    local_actor:
      mode === "live-local" ? normalizeLocalActor(input.localActor) : undefined,
    local_actor_is_auth: mode === "live-local" && Boolean(input.localActorIsAuth)
  };
}

function normalizeMode(value: string, dev: boolean): RuntimeMode {
  if (["static", "static-demo", "fixture", "demo"].includes(value)) {
    return "static-demo";
  }
  if (["live", "live-local", "local"].includes(value)) {
    return "live-local";
  }
  if (["hosted", "hosted-workspace"].includes(value)) {
    return "hosted-workspace";
  }
  return dev ? "live-local" : "static-demo";
}

function normalizeApiBase(value: string | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) {
    return DEFAULT_API_BASE;
  }
  return trimmed.replace(/\/+$/, "");
}

function normalizeLocalActor(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed || undefined;
}
