import {
  REVIEW_DECISION_ENDPOINTS,
  type HumanReviewDecision,
  buildReviewDecisionPayload,
  canConfirmReviewDecision
} from "./reviewDecisionWorkbench";

function formText(form: HTMLFormElement, name: string): string {
  const value = new FormData(form).get(name);
  return typeof value === "string" ? value : "";
}

function formChecked(form: HTMLFormElement, name: string): boolean {
  return form.querySelector<HTMLInputElement>(`[name="${name}"]`)?.checked ?? false;
}

function decisionPayload(form: HTMLFormElement, confirm = false) {
  return buildReviewDecisionPayload(
    {
      artifactId: formText(form, "artifactId"),
      reviewer: formText(form, "reviewer"),
      decision: formText(form, "decision") as HumanReviewDecision,
      reviewNotes: formText(form, "reviewNotes"),
      scope: formText(form, "scope"),
      limitations: formText(form, "limitations"),
      dependenciesChecked: formChecked(form, "dependenciesChecked"),
      sourcesChecked: formChecked(form, "sourcesChecked"),
      evidenceChecked: formChecked(form, "evidenceChecked"),
      gateStateAcknowledged: formChecked(form, "gateStateAcknowledged"),
      explicitHumanConfirmation: formChecked(form, "explicitHumanConfirmation")
    },
    confirm ? { confirm: true } : {}
  );
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
  "[data-review-decision-form]"
)) {
  const apiBase = form.dataset.apiBase ?? "http://127.0.0.1:8765";
  const output = document.querySelector(form.dataset.output ?? "");
  const confirmButton = form.querySelector<HTMLButtonElement>("[data-confirm]");
  const previewButton = form.querySelector<HTMLButtonElement>("[data-preview]");
  const redirect = form.dataset.redirect;
  let previewLoaded = false;
  if (form.dataset.mode !== "live-local") {
    continue;
  }

  function refreshConfirmState(): void {
    if (confirmButton) {
      confirmButton.disabled = !canConfirmReviewDecision({
        previewLoaded,
        reviewer: formText(form, "reviewer"),
        reviewNotes: formText(form, "reviewNotes"),
        explicitHumanConfirmation: formChecked(form, "explicitHumanConfirmation")
      });
    }
  }

  previewButton?.addEventListener("click", async () => {
    previewButton.disabled = true;
    previewLoaded = false;
    refreshConfirmState();
    try {
      const preview = await postJson(
        apiBase,
        REVIEW_DECISION_ENDPOINTS.preview,
        decisionPayload(form)
      );
      setOutput(output, preview);
      previewLoaded = true;
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      previewButton.disabled = false;
      refreshConfirmState();
    }
  });

  form.addEventListener("input", refreshConfirmState);
  refreshConfirmState();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (
      !canConfirmReviewDecision({
        previewLoaded,
        reviewer: formText(form, "reviewer"),
        reviewNotes: formText(form, "reviewNotes"),
        explicitHumanConfirmation: formChecked(form, "explicitHumanConfirmation")
      })
    ) {
      refreshConfirmState();
      return;
    }
    confirmButton?.setAttribute("disabled", "true");
    try {
      const result = await postJson(
        apiBase,
        REVIEW_DECISION_ENDPOINTS.create,
        decisionPayload(form, true)
      );
      setOutput(output, result);
      if (redirect) {
        globalThis.location.href = redirect;
      }
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
      confirmButton?.removeAttribute("disabled");
    }
  });
}
