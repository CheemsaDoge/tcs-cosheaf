import {
  ARTIFACT_METADATA_ENDPOINTS,
  buildEvidencePayload,
  buildSourcePayload
} from "./artifactMetadataWorkbench";

type MetadataAction = "source" | "evidence";

function formText(form: HTMLFormElement, name: string): string {
  const value = new FormData(form).get(name);
  return typeof value === "string" ? value : "";
}

function metadataPayload(form: HTMLFormElement, confirm = false) {
  if (form.dataset.action === "source") {
    return buildSourcePayload(
      {
        kind: formText(form, "kind"),
        title: formText(form, "title"),
        authors: formText(form, "authors"),
        year: formText(form, "year"),
        doi: formText(form, "doi"),
        arxiv: formText(form, "arxiv"),
        url: formText(form, "url"),
        theoremNumber: formText(form, "theoremNumber"),
        page: formText(form, "page"),
        notes: formText(form, "notes")
      },
      confirm ? { confirm: true } : {}
    );
  }
  return buildEvidencePayload(
    {
      kind: formText(form, "kind"),
      path: formText(form, "path"),
      summary: formText(form, "summary")
    },
    confirm ? { confirm: true } : {}
  );
}

function endpointFor(
  action: MetadataAction,
  artifactId: string,
  confirm: boolean
): string {
  if (action === "source") {
    return confirm
      ? ARTIFACT_METADATA_ENDPOINTS.source(artifactId)
      : ARTIFACT_METADATA_ENDPOINTS.previewSource(artifactId);
  }
  return confirm
    ? ARTIFACT_METADATA_ENDPOINTS.evidence(artifactId)
    : ARTIFACT_METADATA_ENDPOINTS.previewEvidence(artifactId);
}

function setOutput(target: Element | null, payload: unknown): void {
  if (target) {
    target.textContent = JSON.stringify(payload, null, 2);
  }
}

async function postJson(
  apiBase: string,
  endpoint: string,
  payload: unknown
): Promise<Record<string, unknown>> {
  const response = await fetch(new URL(endpoint, apiBase), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = (await response.json()) as Record<string, unknown>;
  if (!response.ok) {
    throw new Error(String(data.message ?? data.code ?? response.status));
  }
  return data;
}

for (const form of document.querySelectorAll<HTMLFormElement>(
  "[data-artifact-metadata-form]"
)) {
  const action = form.dataset.action as MetadataAction;
  const artifactId = form.dataset.artifactId ?? "";
  const apiBase = form.dataset.apiBase ?? "http://127.0.0.1:8765";
  const output = document.querySelector(form.dataset.output ?? "");
  const confirmButton = form.querySelector<HTMLButtonElement>("[data-confirm]");
  const previewButton = form.querySelector<HTMLButtonElement>("[data-preview]");
  const redirect = form.dataset.redirect;
  if (form.dataset.mode !== "live-local") {
    continue;
  }

  previewButton?.addEventListener("click", async () => {
    previewButton.disabled = true;
    confirmButton?.setAttribute("disabled", "true");
    try {
      const preview = await postJson(
        apiBase,
        endpointFor(action, artifactId, false),
        metadataPayload(form)
      );
      setOutput(output, preview);
      confirmButton?.removeAttribute("disabled");
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      previewButton.disabled = false;
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (confirmButton?.disabled) {
      return;
    }
    confirmButton?.setAttribute("disabled", "true");
    try {
      const result = await postJson(
        apiBase,
        endpointFor(action, artifactId, true),
        metadataPayload(form, true)
      );
      setOutput(output, result);
      globalThis.location.href =
        redirect ?? `/artifacts/${encodeURIComponent(artifactId)}/`;
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
      confirmButton?.removeAttribute("disabled");
    }
  });
}
