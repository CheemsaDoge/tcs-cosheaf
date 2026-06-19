import {
  buildPromotionPreviewPayload,
  promotionPreviewEndpoint,
  promotionReadinessEndpoint
} from "./promotionWorkbench";

function formText(form: HTMLFormElement, name: string): string {
  const value = new FormData(form).get(name);
  return typeof value === "string" ? value : "";
}

function setOutput(target: Element | null, payload: unknown): void {
  if (target) {
    target.textContent = JSON.stringify(payload, null, 2);
  }
}

async function getJson(
  apiBase: string,
  endpoint: string
): Promise<Record<string, unknown>> {
  const response = await fetch(new URL(endpoint, apiBase));
  const data = (await response.json()) as Record<string, unknown>;
  if (!response.ok) {
    throw new Error(String(data.message ?? data.code ?? response.status));
  }
  return data;
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
  "[data-promotion-workbench-form]"
)) {
  const apiBase = form.dataset.apiBase ?? "http://127.0.0.1:8765";
  const artifactId = form.dataset.artifactId ?? formText(form, "artifactId");
  const output = document.querySelector(form.dataset.output ?? "");
  const previewButton = form.querySelector<HTMLButtonElement>("[data-preview]");
  if (form.dataset.mode !== "live-local") {
    continue;
  }

  getJson(apiBase, promotionReadinessEndpoint(artifactId))
    .then((readiness) => setOutput(output, readiness))
    .catch((error) => {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    });

  previewButton?.addEventListener("click", async () => {
    previewButton.disabled = true;
    try {
      const preview = await postJson(
        apiBase,
        promotionPreviewEndpoint(artifactId),
        buildPromotionPreviewPayload({
          artifactId,
          targetState: formText(form, "targetState")
        })
      );
      setOutput(output, preview);
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      previewButton.disabled = false;
    }
  });
}
