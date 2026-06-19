import { CHECK_RUN_ENDPOINTS } from "./gateWorkbench";

type CheckAction = keyof typeof CHECK_RUN_ENDPOINTS;

function setOutput(target: Element | null, data: unknown) {
  if (!target) {
    return;
  }
  target.textContent =
    typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

async function postJson(
  apiBase: string,
  endpoint: string
): Promise<Record<string, unknown>> {
  const response = await fetch(new URL(endpoint, apiBase), { method: "POST" });
  const data = (await response.json()) as Record<string, unknown>;
  if (!response.ok) {
    throw new Error(String(data.message ?? data.code ?? response.status));
  }
  return data;
}

for (const button of document.querySelectorAll<HTMLButtonElement>(
  "[data-check-run]"
)) {
  const action = button.dataset.checkRun as CheckAction | undefined;
  const apiBase = button.dataset.apiBase ?? "http://127.0.0.1:8765";
  const output = document.querySelector(button.dataset.output ?? "");
  if (!action || button.dataset.mode !== "live-local") {
    continue;
  }

  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      setOutput(output, await postJson(apiBase, CHECK_RUN_ENDPOINTS[action]));
    } catch (error) {
      setOutput(output, { error: error instanceof Error ? error.message : error });
    } finally {
      button.disabled = false;
    }
  });
}
