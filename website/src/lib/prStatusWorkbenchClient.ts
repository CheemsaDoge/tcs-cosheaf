import {
  PR_STATUS_LABELS,
  buildPrStatusUrl,
  checklistSummary,
  hasPrSelector,
  statusTone,
  textValue,
  type PrStatusInput,
  type PrStatusPayload
} from "./prStatusWorkbench";

function language(): "en" | "zh" {
  return document.documentElement.dataset.lang === "en" ? "en" : "zh";
}

function label(key: keyof typeof PR_STATUS_LABELS): string {
  return PR_STATUS_LABELS[key][language()];
}

function formText(form: HTMLFormElement, name: string): string {
  const value = new FormData(form).get(name);
  return typeof value === "string" ? value : "";
}

function setText(selector: string | undefined, value: string): void {
  const target = selector ? document.querySelector(selector) : null;
  if (target) {
    target.textContent = value;
  }
}

function setLink(selector: string | undefined, url: string): void {
  const target = selector
    ? document.querySelector<HTMLAnchorElement>(selector)
    : null;
  if (!target) {
    return;
  }
  target.hidden = !url;
  target.href = url || "#";
  target.textContent = url ? label("viewGithub") : "";
}

function clearElement(selector: string | undefined): Element | null {
  const target = selector ? document.querySelector(selector) : null;
  if (target) {
    target.textContent = "";
  }
  return target;
}

function appendBadge(target: Element | null, labelText: string, status: string): void {
  if (!target) {
    return;
  }
  const badge = document.createElement("span");
  badge.className = `status-badge tone-${statusTone(status)}`;
  badge.textContent = `${labelText}: ${status || "unknown"}`;
  target.appendChild(badge);
}

function renderChecklist(selector: string | undefined, payload: PrStatusPayload): void {
  const target = clearElement(selector);
  if (!target) {
    return;
  }
  const items = payload.pr_status?.checklist?.items ?? [];
  if (items.length === 0) {
    target.textContent = label("noChecklist");
    return;
  }
  for (const item of items.slice(0, 5)) {
    const row = document.createElement("li");
    row.textContent = `${item.checked ? "[x]" : "[ ]"} ${item.text ?? ""}`;
    target.appendChild(row);
  }
}

function renderComments(selector: string | undefined, payload: PrStatusPayload): void {
  const target = clearElement(selector);
  if (!target) {
    return;
  }
  const comments = payload.pr_status?.review_comments ?? [];
  if (comments.length === 0) {
    target.textContent = label("noComments");
    return;
  }
  for (const comment of comments.slice(0, 3)) {
    const row = document.createElement("li");
    const author = textValue(comment.author, "GitHub");
    row.textContent = `${author}: ${textValue(comment.body, "")}`;
    target.appendChild(row);
  }
}

function renderWarnings(selector: string | undefined, payload: PrStatusPayload): void {
  const target = clearElement(selector);
  if (!target) {
    return;
  }
  const warnings = payload.pr_status?.warnings ?? [];
  for (const warning of warnings) {
    const row = document.createElement("li");
    row.textContent = warning;
    target.appendChild(row);
  }
}

function renderPayload(form: HTMLFormElement, payload: PrStatusPayload): void {
  const status = payload.pr_status;
  const pr = status?.pr ?? {};
  const ciStatus = textValue(status?.ci?.status, "unknown");
  const gateStatus = textValue(status?.gate?.status, "unknown");
  const cosheafReview = textValue(
    status?.cosheaf_review?.status,
    "not_imported"
  );
  const githubReviews = status?.github_reviews?.length ?? 0;
  const title = textValue(pr.title, textValue(pr.head, label("notSynced")));
  const state = textValue(pr.state, "unknown");

  setText(form.dataset.prTitle, title);
  setText(form.dataset.prUpdated, `${label("updated")}: ${status?.updated_at ?? ""}`);
  setText(
    form.dataset.prChecklistSummary,
    `${label("checklist")}: ${checklistSummary(status?.checklist)}`
  );
  setLink(form.dataset.prLink, textValue(pr.url, ""));

  const badges = clearElement(form.dataset.prBadges);
  appendBadge(badges, "PR", state);
  appendBadge(badges, label("ci"), ciStatus);
  appendBadge(badges, label("gate"), gateStatus);
  appendBadge(badges, label("cosheafReview"), cosheafReview);
  appendBadge(
    badges,
    label("githubCollaboration"),
    githubReviews > 0 ? `${githubReviews}` : "0"
  );

  renderChecklist(form.dataset.prChecklistItems, payload);
  renderComments(form.dataset.prComments, payload);
  renderWarnings(form.dataset.prWarnings, payload);
  setText(form.dataset.prRaw, JSON.stringify(payload, null, 2));
}

async function fetchPrStatus(
  apiBase: string,
  input: PrStatusInput
): Promise<PrStatusPayload> {
  const response = await fetch(buildPrStatusUrl(apiBase, input));
  const payload = (await response.json()) as PrStatusPayload;
  if (!response.ok) {
    throw new Error(
      textValue((payload as Record<string, unknown>).message, response.statusText)
    );
  }
  return payload;
}

for (const form of document.querySelectorAll<HTMLFormElement>(
  "[data-pr-status-workbench]"
)) {
  const apiBase = form.dataset.apiBase ?? "http://127.0.0.1:8765";
  const button = form.querySelector<HTMLButtonElement>("[data-pr-status-sync]");

  button?.addEventListener("click", async () => {
    const input = {
      number: formText(form, "number"),
      base: formText(form, "base"),
      head: formText(form, "head")
    };
    if (!hasPrSelector(input)) {
      setText(form.dataset.prTitle, label("notSynced"));
      return;
    }
    button.disabled = true;
    try {
      renderPayload(form, await fetchPrStatus(apiBase, input));
    } catch (error) {
      setText(
        form.dataset.prTitle,
        error instanceof Error ? error.message : label("githubDisconnected")
      );
      setLink(form.dataset.prLink, "");
    } finally {
      button.disabled = false;
    }
  });
}
