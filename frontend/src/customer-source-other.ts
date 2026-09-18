const CUSTOM_SOURCE_LABEL = "Lainnya";
const SOURCE_TEST_ID = "customer-source-input";
const OTHER_SOURCE_INPUT_ID = "customer-source-other-input";

let customSourceValue = "";
let observerStarted = false;

function getSourceSelect(): HTMLSelectElement | null {
  return document.querySelector<HTMLSelectElement>(
    `select[data-testid="${SOURCE_TEST_ID}"]`,
  );
}

function getOrCreateOtherInput(select: HTMLSelectElement): HTMLInputElement {
  const existing = document.getElementById(
    OTHER_SOURCE_INPUT_ID,
  ) as HTMLInputElement | null;
  if (existing) return existing;

  const input = document.createElement("input");
  input.id = OTHER_SOURCE_INPUT_ID;
  input.type = "text";
  input.placeholder = "Tulis sumber lainnya...";
  input.autocomplete = "off";
  input.className =
    "mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30";
  input.value = customSourceValue;

  input.addEventListener("input", () => {
    customSourceValue = input.value;
  });

  select.insertAdjacentElement("afterend", input);
  return input;
}

function syncOtherSourceField(): void {
  const select = getSourceSelect();
  const existing = document.getElementById(OTHER_SOURCE_INPUT_ID);

  if (!select) {
    customSourceValue = "";
    existing?.remove();
    return;
  }

  const otherOption = Array.from(select.options).find(
    (option) => option.value === CUSTOM_SOURCE_LABEL,
  );

  if (!otherOption) {
    const option = document.createElement("option");
    option.value = CUSTOM_SOURCE_LABEL;
    option.textContent = CUSTOM_SOURCE_LABEL;
    select.appendChild(option);
  }

  if (select.value === CUSTOM_SOURCE_LABEL) {
    getOrCreateOtherInput(select);
  } else {
    customSourceValue = "";
    existing?.remove();
  }
}

function installFetchGuard(): void {
  if (window.__wellracomCustomerSourceFetchGuard) return;

  const originalFetch = window.fetch.bind(window);

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const requestUrl =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;

    const method = (init?.method ?? (input instanceof Request ? input.method : "GET"))
      .toUpperCase();

    if (
      method === "POST" &&
      requestUrl.includes("/customers") &&
      customSourceValue.trim()
    ) {
      const body = init?.body;

      if (typeof body === "string") {
        try {
          const payload = JSON.parse(body) as Record<string, unknown>;
          if (payload.source === CUSTOM_SOURCE_LABEL) {
            payload.source = customSourceValue.trim();
            return originalFetch(input, {
              ...init,
              body: JSON.stringify(payload),
            });
          }
        } catch {
          // Leave non-JSON requests untouched.
        }
      }
    }

    return originalFetch(input, init);
  };

  window.__wellracomCustomerSourceFetchGuard = true;
}

declare global {
  interface Window {
    __wellracomCustomerSourceFetchGuard?: boolean;
  }
}

function startCustomerSourceEnhancement(): void {
  if (observerStarted) return;
  observerStarted = true;

  installFetchGuard();
  syncOtherSourceField();

  const observer = new MutationObserver(() => {
    syncOtherSourceField();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (target instanceof HTMLSelectElement && target.dataset.testid === SOURCE_TEST_ID) {
      syncOtherSourceField();
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", startCustomerSourceEnhancement, {
    once: true,
  });
} else {
  startCustomerSourceEnhancement();
}

export {};
