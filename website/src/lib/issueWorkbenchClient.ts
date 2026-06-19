import {
  ISSUE_ACTION_ENDPOINTS,
  buildIssueActionPayload
} from "./issueWorkbench";

type IssueFormAction = "create" | "update";

function formText(form: HTMLFormElement, name: string): string {
  const value = new FormData(form).get(name);
  return typeof value === "string" ? value : "";
}

function issuePayload(form: HTMLFormElement, confirm = false) {
  return buildIssueActionPayload(
    {
      issueId: formText(form, "issueId"),
      title: formText(form, "title"),
      summary: formText(form, "summary"),
      scope: formText(form, "scope"),
      labels: formText(form, "labels"),
      relatedArtifacts: formText(form, "relatedArtifacts"),
      relatedSources: formText(form, "relatedSources"),
      authors: formText(form, "authors")
    },
    confirm ? { confirm: true } : {}
  );
}

function endpointFor(
  action: IssueFormAction,
  issueId: string,
  confirm: boolean
): string {
  if (action === "create") {
    return confirm ? ISSUE_ACTION_ENDPOINTS.create : ISSUE_ACTION_ENDPOINTS.previewCreate;
  }
  return confirm
    ? ISSUE_ACTION_ENDPOINTS.update(issueId)
    : ISSUE_ACTION_ENDPOINTS.previewUpdate(issueId);
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
  "[data-issue-workbench-form]"
)) {
  const action = form.dataset.action as IssueFormAction;
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
      const payload = issuePayload(form);
      const preview = await postJson(
        apiBase,
        endpointFor(action, payload.issue_id, false),
        payload
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
    const payload = issuePayload(form, true);
    try {
      const result = await postJson(
        apiBase,
        endpointFor(action, payload.issue_id, true),
        payload
      );
      setOutput(output, result);
      globalThis.location.href =
        redirect ?? `/issues/${encodeURIComponent(payload.issue_id)}/`;
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
      confirmButton?.removeAttribute("disabled");
    }
  });
}

for (const form of document.querySelectorAll<HTMLFormElement>(
  "[data-issue-close-form]"
)) {
  const issueId = form.dataset.issueId ?? "";
  const apiBase = form.dataset.apiBase ?? "http://127.0.0.1:8765";
  const output = document.querySelector(form.dataset.output ?? "");
  const confirmButton = form.querySelector<HTMLButtonElement>("[data-confirm]");
  const previewButton = form.querySelector<HTMLButtonElement>("[data-preview]");
  if (form.dataset.mode !== "live-local") {
    continue;
  }

  previewButton?.addEventListener("click", async () => {
    previewButton.disabled = true;
    confirmButton?.setAttribute("disabled", "true");
    try {
      const preview = await postJson(
        apiBase,
        ISSUE_ACTION_ENDPOINTS.previewClose(issueId),
        { reason: formText(form, "reason") }
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
        ISSUE_ACTION_ENDPOINTS.close(issueId),
        { reason: formText(form, "reason"), confirm: true }
      );
      setOutput(output, result);
      globalThis.location.reload();
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
      confirmButton?.removeAttribute("disabled");
    }
  });
}
