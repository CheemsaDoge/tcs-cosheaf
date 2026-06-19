import {
  REVIEW_PACKET_ENDPOINTS,
  buildReviewPacketPayload
} from "./reviewPacketWorkbench";

function formText(form: HTMLFormElement, name: string): string {
  const value = new FormData(form).get(name);
  return typeof value === "string" ? value : "";
}

function packetPayload(form: HTMLFormElement, confirm = false) {
  return buildReviewPacketPayload(
    {
      issueId: formText(form, "issueId"),
      artifactId: formText(form, "artifactId")
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
  "[data-review-packet-form]"
)) {
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
        REVIEW_PACKET_ENDPOINTS.preview,
        packetPayload(form)
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
        REVIEW_PACKET_ENDPOINTS.create,
        packetPayload(form, true)
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
