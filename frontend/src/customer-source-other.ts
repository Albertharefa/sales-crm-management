import { api } from "./lib/api";

const CUSTOM_LABEL = "Lainnya";
const SOURCE_TEST_ID = "customer-source-input";
const INDUSTRY_TEST_ID = "customer-industry-input";
const OTHER_SOURCE_INPUT_ID = "customer-source-other-input";
const OTHER_INDUSTRY_INPUT_ID = "customer-industry-other-input";

let customSourceValue = "";
let customIndustryValue = "";
let observerStarted = false;
let apiInterceptorInstalled = false;

function getSelect(testId: string): HTMLSelectElement | null {
  return document.querySelector<HTMLSelectElement>(
    `select[data-testid="${testId}"]`,
  );
}

function getOrCreateOtherInput(
  select: HTMLSelectElement,
  inputId: string,
  placeholder: string,
  value: string,
  onInput: (value: string) => void,
): HTMLInputElement {
  const existing = document.getElementById(inputId) as HTMLInputElement | null;
  if (existing) return existing;

  const input = document.createElement("input");
  input.id = inputId;
  input.type = "text";
  input.placeholder = placeholder;
  input.autocomplete = "off";
  input.className =
    "mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30";
  input.value = value;
  input.addEventListener("input", () => onInput(input.value));

  select.insertAdjacentElement("afterend", input);
  return input;
}

function ensureOtherOption(select: HTMLSelectElement): void {
  const exists = Array.from(select.options).some(
    (option) => option.value === CUSTOM_LABEL,
  );
  if (!exists) {
    const option = document.createElement("option");
    option.value = CUSTOM_LABEL;
    option.textContent = CUSTOM_LABEL;
    select.appendChild(option);
  }
}

function syncOtherField(
  select: HTMLSelectElement | null,
  inputId: string,
  placeholder: string,
  value: string,
  setValue: (next: string) => void,
): void {
  const existing = document.getElementById(inputId);

  if (!select) {
    setValue("");
    existing?.remove();
    return;
  }

  ensureOtherOption(select);

  if (select.value === CUSTOM_LABEL) {
    getOrCreateOtherInput(
      select,
      inputId,
      placeholder,
      value,
      setValue,
    );
  } else {
    setValue("");
    existing?.remove();
  }
}

function syncCustomerCustomFields(): void {
  syncOtherField(
    getSelect(SOURCE_TEST_ID),
    OTHER_SOURCE_INPUT_ID,
    "Tulis sumber lainnya...",
    customSourceValue,
    (next) => {
      customSourceValue = next;
    },
  );

  syncOtherField(
    getSelect(INDUSTRY_TEST_ID),
    OTHER_INDUSTRY_INPUT_ID,
    "Tulis industri lainnya...",
    customIndustryValue,
    (next) => {
      customIndustryValue = next;
    },
  );
}

function rewriteCustomerCreatePayload(data: unknown): unknown {
  if (!data || typeof data !== "object") return data;

  const payload = data as Record<string, unknown>;
  let changed = false;
  const next = { ...payload };

  if (
    next.source === CUSTOM_LABEL &&
    customSourceValue.trim()
  ) {
    next.source = customSourceValue.trim();
    changed = true;
  }

  if (
    next.industry === CUSTOM_LABEL &&
    customIndustryValue.trim()
  ) {
    next.industry = customIndustryValue.trim();
    changed = true;
  }

  return changed ? next : data;
}

function installApiRequestGuard(): void {
  if (apiInterceptorInstalled) return;

  api.interceptors.request.use((config) => {
    const method = String(config.method ?? "get").toUpperCase();
    const url = String(config.url ?? "");

    if (method === "POST" && /(?:^|\/)customers(?:$|\/)/.test(url)) {
      config.data = rewriteCustomerCreatePayload(config.data);
    }

    return config;
  });

  apiInterceptorInstalled = true;
}

function startCustomerCustomFieldEnhancement(): void {
  if (observerStarted) return;
  observerStarted = true;

  // IMPORTANT: use the same axios instance as apiPost/apiPut.
  installApiRequestGuard();
  syncCustomerCustomFields();

  const observer = new MutationObserver(() => {
    syncCustomerCustomFields();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (
      target instanceof HTMLSelectElement &&
      (target.dataset.testid === SOURCE_TEST_ID ||
        target.dataset.testid === INDUSTRY_TEST_ID)
    ) {
      syncCustomerCustomFields();
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener(
    "DOMContentLoaded",
    startCustomerCustomFieldEnhancement,
    { once: true },
  );
} else {
  startCustomerCustomFieldEnhancement();
}

export {};
