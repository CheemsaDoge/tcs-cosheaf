import { localized } from "./i18n";
import { parseDelimitedList } from "./artifactWorkbench";

export const ARTIFACT_METADATA_ENDPOINTS = {
  previewSource: (id: string) =>
    `/api/artifacts/${encodeURIComponent(id)}/preview-source`,
  source: (id: string) => `/api/artifacts/${encodeURIComponent(id)}/source`,
  previewEvidence: (id: string) =>
    `/api/artifacts/${encodeURIComponent(id)}/preview-evidence`,
  evidence: (id: string) => `/api/artifacts/${encodeURIComponent(id)}/evidence`
} as const;

export const ARTIFACT_METADATA_LABELS = {
  addSource: localized("Add source metadata", "添加来源元数据"),
  addEvidence: localized("Add evidence metadata", "添加证据元数据"),
  preview: localized("Preview changes", "预览变更"),
  confirm: localized("Confirm write", "确认写入"),
  kind: localized("Kind", "类型"),
  title: localized("Title", "标题"),
  authors: localized("Authors", "作者"),
  year: localized("Year", "年份"),
  doi: localized("DOI", "DOI"),
  arxiv: localized("arXiv", "arXiv"),
  url: localized("URL", "URL"),
  theoremNumber: localized("Locator", "定位信息"),
  page: localized("Page", "页码"),
  notes: localized("Notes", "备注"),
  path: localized("Path", "路径"),
  summary: localized("Summary", "摘要"),
  previewOutput: localized("Preview output", "预览输出")
} as const;

export interface SourceFormInput {
  kind: string;
  title: string;
  authors: string;
  year: string;
  doi: string;
  arxiv: string;
  url: string;
  theoremNumber: string;
  page: string;
  notes: string;
}

export interface SourcePayload {
  kind: string;
  title: string;
  authors: string[];
  year: number | null;
  doi: string;
  arxiv: string;
  url: string;
  theorem_number: string;
  page: string;
  notes: string;
  confirm?: true;
}

export interface EvidenceFormInput {
  kind: string;
  path: string;
  summary: string;
}

export interface EvidencePayload {
  kind: string;
  path: string;
  summary: string;
  confirm?: true;
}

export function buildSourcePayload(
  input: SourceFormInput,
  options: { confirm?: true } = {}
): SourcePayload {
  const parsedYear = Number.parseInt(input.year.trim(), 10);
  const payload: SourcePayload = {
    kind: input.kind.trim() || "paper",
    title: input.title.trim(),
    authors: parseDelimitedList(input.authors),
    year: Number.isFinite(parsedYear) ? parsedYear : null,
    doi: input.doi.trim(),
    arxiv: input.arxiv.trim(),
    url: input.url.trim(),
    theorem_number: input.theoremNumber.trim(),
    page: input.page.trim(),
    notes: input.notes.trim()
  };
  if (options.confirm) {
    payload.confirm = true;
  }
  return payload;
}

export function buildEvidencePayload(
  input: EvidenceFormInput,
  options: { confirm?: true } = {}
): EvidencePayload {
  const payload: EvidencePayload = {
    kind: input.kind.trim() || "note",
    path: input.path.trim(),
    summary: input.summary.trim()
  };
  if (options.confirm) {
    payload.confirm = true;
  }
  return payload;
}
