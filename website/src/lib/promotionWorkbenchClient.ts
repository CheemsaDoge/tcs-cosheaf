import {
  buildPromotionConfirmPayload,
  buildPromotionPreviewPayload,
  canConfirmPromotion,
  promotionConfirmEndpoint,
  promotionPreviewEndpoint,
  promotionReadinessEndpoint,
  requiredPromotionConfirmation
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
  const requiredPhrase = document.querySelector(
    form.dataset.requiredConfirmation ?? ""
  );
  const previewButton = form.querySelector<HTMLButtonElement>("[data-preview]");
  const confirmButton = form.querySelector<HTMLButtonElement>("[data-confirm]");
  const targetInput = form.querySelector<HTMLSelectElement>("[name=targetState]");
  let previewLoaded = false;
  let promotionBlocked = true;
  if (form.dataset.mode !== "live-local") {
    continue;
  }

  function refreshConfirmState(): void {
    const targetState = formText(form, "targetState");
    try {
      if (requiredPhrase) {
        requiredPhrase.textContent = requiredPromotionConfirmation(targetState);
      }
      if (confirmButton) {
        confirmButton.disabled = !canConfirmPromotion({
          actor: formText(form, "actor"),
          targetState,
          typedConfirmation: formText(form, "typedConfirmation"),
          promotionBlocked,
          previewLoaded
        });
      }
    } catch {
      if (confirmButton) {
        confirmButton.disabled = true;
      }
    }
  }

  targetInput?.addEventListener("change", () => {
    previewLoaded = false;
    promotionBlocked = true;
    refreshConfirmState();
  });
  form.addEventListener("input", refreshConfirmState);
  refreshConfirmState();

  getJson(apiBase, promotionReadinessEndpoint(artifactId))
    .then((readiness) => setOutput(output, readiness))
    .catch((error) => {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    });

  previewButton?.addEventListener("click", async () => {
    previewButton.disabled = true;
    previewLoaded = false;
    promotionBlocked = true;
    refreshConfirmState();
    try {
      const preview = await postJson(
        apiBase,
        promotionPreviewEndpoint(artifactId),
        buildPromotionPreviewPayload({
          artifactId,
          targetState: formText(form, "targetState"),
          actor: formText(form, "actor")
        })
      );
      previewLoaded = true;
      promotionBlocked = preview.promotion_blocked === true;
      setOutput(output, preview);
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      previewButton.disabled = false;
      refreshConfirmState();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (
      !canConfirmPromotion({
        actor: formText(form, "actor"),
        targetState: formText(form, "targetState"),
        typedConfirmation: formText(form, "typedConfirmation"),
        promotionBlocked,
        previewLoaded
      })
    ) {
      refreshConfirmState();
      return;
    }
    if (confirmButton) {
      confirmButton.disabled = true;
    }
    try {
      const confirmed = await postJson(
        apiBase,
        promotionConfirmEndpoint(artifactId),
        buildPromotionConfirmPayload({
          artifactId,
          targetState: formText(form, "targetState"),
          actor: formText(form, "actor"),
          typedConfirmation: formText(form, "typedConfirmation")
        })
      );
      setOutput(output, confirmed);
      previewLoaded = false;
      promotionBlocked = true;
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      refreshConfirmState();
    }
  });
}
