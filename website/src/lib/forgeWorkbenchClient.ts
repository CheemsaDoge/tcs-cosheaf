import {
  FORGE_PR_FLOW_ENDPOINTS,
  buildBranchCreatePayload,
  buildCommitCreatePayload,
  buildPrCreatePayload,
  buildPushCreatePayload,
  canCreateBranch,
  canCreatePr,
  canPushBranch,
  extractPrUrl
} from "./forgeWorkbench";

type ForgeAction =
  | "branch-preview"
  | "branch-create"
  | "commit-preview"
  | "commit-create"
  | "push-preview"
  | "push-create"
  | "pr-preview"
  | "pr-create";

function formText(form: HTMLFormElement, name: string): string {
  const value = new FormData(form).get(name);
  return typeof value === "string" ? value : "";
}

function formChecked(form: HTMLFormElement, name: string): boolean {
  const value = form.querySelector<HTMLInputElement>(`[name="${name}"]`);
  return value?.checked ?? false;
}

function setOutput(target: Element | null, data: unknown): void {
  if (!target) {
    return;
  }
  target.textContent =
    typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

function setPrUrl(target: HTMLAnchorElement | null, url: string): void {
  if (!target) {
    return;
  }
  target.hidden = !url;
  target.href = url || "#";
  target.textContent = url;
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

function payloadFor(form: HTMLFormElement, action: ForgeAction): unknown {
  const branch = formText(form, "branch");
  const base = formText(form, "base");
  const head = formText(form, "head") || branch;
  const message = formText(form, "message");
  if (action === "branch-preview") {
    return { branch };
  }
  if (action === "branch-create") {
    if (!canCreateBranch({ branch })) {
      throw new Error("branch is empty or protected");
    }
    return buildBranchCreatePayload({ branch });
  }
  if (action === "commit-preview") {
    return { message };
  }
  if (action === "commit-create") {
    return buildCommitCreatePayload({ message });
  }
  if (action === "push-preview") {
    return { head };
  }
  if (action === "push-create") {
    if (!canPushBranch({ head, confirm: formChecked(form, "confirmPush") })) {
      throw new Error("push confirmation or branch is invalid");
    }
    return buildPushCreatePayload({ head });
  }
  if (action === "pr-preview") {
    return { base, head };
  }
  if (!canCreatePr({ base, head, confirm: formChecked(form, "confirmPr") })) {
    throw new Error("PR confirmation or branch is invalid");
  }
  return buildPrCreatePayload({
    base,
    head,
    draft: formChecked(form, "draft")
  });
}

function endpointFor(action: ForgeAction): string {
  return {
    "branch-preview": FORGE_PR_FLOW_ENDPOINTS.branchPreview,
    "branch-create": FORGE_PR_FLOW_ENDPOINTS.branchCreate,
    "commit-preview": FORGE_PR_FLOW_ENDPOINTS.commitPreview,
    "commit-create": FORGE_PR_FLOW_ENDPOINTS.commitCreate,
    "push-preview": FORGE_PR_FLOW_ENDPOINTS.pushPreview,
    "push-create": FORGE_PR_FLOW_ENDPOINTS.pushCreate,
    "pr-preview": FORGE_PR_FLOW_ENDPOINTS.prPreview,
    "pr-create": FORGE_PR_FLOW_ENDPOINTS.prCreate
  }[action];
}

for (const form of document.querySelectorAll<HTMLFormElement>(
  "[data-forge-pr-flow]"
)) {
  if (form.dataset.mode !== "live-local") {
    continue;
  }
  const apiBase = form.dataset.apiBase ?? "http://127.0.0.1:8765";
  const output = document.querySelector(form.dataset.output ?? "");
  const prUrl = document.querySelector<HTMLAnchorElement>(form.dataset.prUrl ?? "");

  for (const button of form.querySelectorAll<HTMLButtonElement>(
    "[data-forge-action]"
  )) {
    const action = button.dataset.forgeAction as ForgeAction | undefined;
    if (!action) {
      continue;
    }
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        const response = await postJson(
          apiBase,
          endpointFor(action),
          payloadFor(form, action)
        );
        setOutput(output, response);
        setPrUrl(prUrl, extractPrUrl(response));
      } catch (error) {
        setOutput(output, { error: error instanceof Error ? error.message : error });
        setPrUrl(prUrl, "");
      } finally {
        button.disabled = false;
      }
    });
  }
}
