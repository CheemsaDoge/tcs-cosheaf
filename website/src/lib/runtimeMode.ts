export type RuntimeMode = "static-demo" | "live-local" | "hosted-workspace";

export interface RuntimeModeInput {
  mode?: string;
  dev?: boolean;
  apiBase?: string;
  fallbackReason?: string;
}

export interface RuntimeMetadata {
  mode: RuntimeMode;
  label: string;
  label_en: string;
  label_zh: string;
  api_base: string;
  fallback: boolean;
  fallback_reason?: string;
}

export const DEFAULT_API_BASE = "http://127.0.0.1:8765";

const LABELS: Record<RuntimeMode, { en: string; zh: string }> = {
  "static-demo": {
    en: "Static demo mode",
    zh: "静态演示模式"
  },
  "live-local": {
    en: "Live local workspace mode",
    zh: "本地实时工作区模式"
  },
  "hosted-workspace": {
    en: "Hosted workspace mode",
    zh: "托管工作区模式"
  }
};

export function runtimeModeLabel(mode: RuntimeMode): string {
  const label = LABELS[mode];
  return `${label.en} / ${label.zh}`;
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
    fallback_reason: input.fallbackReason
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
