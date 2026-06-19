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
  const diffOutput = document.querySelector(form.dataset.diffOutput ?? "");
  const requiredPhrase = document.querySelector(
    form.dataset.requiredConfirmation ?? ""
  );
  const previewButton = form.querySelector<HTMLButtonElement>("[data-preview]");
  const confirmButton = form.querySelector<HTMLButtonElement>("[data-confirm]");
  const modal = form.querySelector<HTMLElement>("[data-confirmation-modal]");
  const modalTargetState = form.querySelector("[data-modal-target-state]");
  const modalRequiredPhrase = form.querySelector("[data-modal-required-phrase]");
  const modalCancel = form.querySelector<HTMLButtonElement>("[data-modal-cancel]");
  const modalConfirm = form.querySelector<HTMLButtonElement>(
    "[data-modal-confirm]"
  );
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
      if (modalTargetState) {
        modalTargetState.textContent = targetState;
      }
      if (modalRequiredPhrase) {
        modalRequiredPhrase.textContent = requiredPromotionConfirmation(targetState);
      }
      if (confirmButton) {
        confirmButton.disabled =
          !previewLoaded ||
          promotionBlocked ||
          !formText(form, "actor").trim() ||
          formText(form, "typedConfirmation").trim() !==
            requiredPromotionConfirmation(targetState);
      }
      if (modalConfirm) {
        modalConfirm.disabled = !canConfirmPromotion({
          actor: formText(form, "actor"),
          targetState,
          typedConfirmation: formText(form, "typedConfirmation"),
          promotionJustification: formText(form, "promotionJustification"),
          promotionBlocked,
          previewLoaded
        });
      }
    } catch {
      if (confirmButton) {
        confirmButton.disabled = true;
      }
      if (modalConfirm) {
        modalConfirm.disabled = true;
      }
    }
  }

  function closeModal(): void {
    modal?.setAttribute("hidden", "true");
  }

  function openModal(): void {
    refreshConfirmState();
    if (confirmButton?.disabled) {
      return;
    }
    modal?.removeAttribute("hidden");
    form.querySelector<HTMLTextAreaElement>("[name=promotionJustification]")?.focus();
  }

  targetInput?.addEventListener("change", () => {
    previewLoaded = false;
    promotionBlocked = true;
    closeModal();
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
      if (diffOutput) {
        diffOutput.textContent =
          typeof preview.yaml_diff === "string" && preview.yaml_diff
            ? preview.yaml_diff
            : "preview did not return a diff";
      }
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      previewButton.disabled = false;
      refreshConfirmState();
    }
  });

  confirmButton?.addEventListener("click", openModal);
  modalCancel?.addEventListener("click", closeModal);
  form.addEventListener("submit", (event) => event.preventDefault());

  modalConfirm?.addEventListener("click", async () => {
    if (
      !canConfirmPromotion({
        actor: formText(form, "actor"),
        targetState: formText(form, "targetState"),
        typedConfirmation: formText(form, "typedConfirmation"),
        promotionJustification: formText(form, "promotionJustification"),
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
          typedConfirmation: formText(form, "typedConfirmation"),
          promotionJustification: formText(form, "promotionJustification")
        })
      );
      setOutput(output, confirmed);
      previewLoaded = false;
      promotionBlocked = true;
      closeModal();
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      refreshConfirmState();
    }
  });
}
