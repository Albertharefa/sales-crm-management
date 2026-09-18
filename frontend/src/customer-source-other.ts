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

function findSelectByOptions(optionValues: string[]): HTMLSelectElement | null {
  const selects = Array.from(document.querySelectorAll<HTMLSelectElement>("select"));
  return (
    selects.find((select) => {
      const values = Array.from(select.options).map((option) => option.value);
      return optionValues.every((value) => values.includes(value));
    }) ?? null
  );
}

function getSelect(testId: string): HTMLSelectElement | null {
  const byTestId = document.querySelector<HTMLSelectElement>(
    `select[data-testid="${testId}"]`,
  );
  if (byTestId) return byTestId;

  if (testId === SOURCE_TEST_ID) {
    return findSelectByOptions(["Referral", "Website", "Pameran", "Cold Call", "Partner"]);
  }

  return findSelectByOptions(["Manufacturing", "Oil & Gas", "Mining"]);
}

function getOtherInput(inputId: string): HTMLInputElement | null {
  return document.getElementById(inputId) as HTMLInputElement | null;
}

function getOrCreateOtherInput(
  select: HTMLSelectElement,
  inputId: string,
  placeholder: string,
  value: string,
  onInput: (value: string) => void,
): HTMLInputElement {
  const existing = getOtherInput(inputId);
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
  const existing = getOtherInput(inputId);

  if (!select) {
    setValue("");
    existing?.remove();
    return;
  }

  ensureOtherOption(select);

  if (select.value === CUSTOM_LABEL) {
    const input = getOrCreateOtherInput(
      select,
      inputId,
      placeholder,
      value,
      setValue,
    );

    if (input.value !== value) setValue(input.value);
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

function rewriteCustomerPayload(data: unknown): unknown {
  if (!data || typeof data !== "object") return data;

  const payload = data as Record<string, unknown>;
  const next = { ...payload };

  const sourceSelect = getSelect(SOURCE_TEST_ID);
  const industrySelect = getSelect(INDUSTRY_TEST_ID);
  const sourceInput = getOtherInput(OTHER_SOURCE_INPUT_ID);
  const industryInput = getOtherInput(OTHER_INDUSTRY_INPUT_ID);

  const sourceValue =
    sourceSelect?.value === CUSTOM_LABEL
      ? (sourceInput?.value.trim() || customSourceValue.trim())
      : String(next.source ?? "").trim();

  const industryValue =
    industrySelect?.value === CUSTOM_LABEL
      ? (industryInput?.value.trim() || customIndustryValue.trim())
      : String(next.industry ?? "").trim();

  if (sourceSelect?.value === CUSTOM_LABEL && sourceValue) {
    next.source = sourceValue;
  }

  if (industrySelect?.value === CUSTOM_LABEL && industryValue) {
    next.industry = industryValue;
  }

  return next;
}

function installApiRequestGuard(): void {
  if (apiInterceptorInstalled) return;

  api.interceptors.request.use((config) => {
    const method = String(config.method ?? "get").toUpperCase();
    const url = String(config.url ?? "");

    if (
      (method === "POST" || method === "PUT" || method === "PATCH") &&
      /(?:^|\/)customers(?:$|\/)/.test(url)
    ) {
      config.data = rewriteCustomerPayload(config.data);
    }

    return config;
  });

  apiInterceptorInstalled = true;
}

function startCustomerCustomFieldEnhancement(): void {
  if (observerStarted) return;
  observerStarted = true;

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
    if (target instanceof HTMLSelectElement) {
      const source = getSelect(SOURCE_TEST_ID);
      const industry = getSelect(INDUSTRY_TEST_ID);
      if (target === source || target === industry) {
        syncCustomerCustomFields();
      }
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
