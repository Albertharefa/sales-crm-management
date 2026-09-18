import axios from "axios";

const CUSTOM_SOURCE_LABEL = "Lainnya";
const SOURCE_TEST_ID = "customer-source-input";
const OTHER_SOURCE_INPUT_ID = "customer-source-other-input";

let customSourceValue = "";
let observerStarted = false;
let axiosInterceptorInstalled = false;

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

function rewriteCustomerCreateBody(body: unknown): unknown {
  if (!customSourceValue.trim()) return body;

  try {
    if (typeof body === "string") {
      const payload = JSON.parse(body) as Record<string, unknown>;
      if (payload.source === CUSTOM_SOURCE_LABEL) {
        payload.source = customSourceValue.trim();
        return JSON.stringify(payload);
      }
    }

    if (body && typeof body === "object" && "source" in body) {
      const payload = body as Record<string, unknown>;
      if (payload.source === CUSTOM_SOURCE_LABEL) {
        payload.source = customSourceValue.trim();
      }
    }
  } catch {
    // Leave non-JSON requests untouched.
  }

  return body;
}

function installAxiosRequestGuard(): void {
  if (axiosInterceptorInstalled) return;

  axios.interceptors.request.use((config) => {
    const method = String(config.method ?? "get").toUpperCase();
    const url = String(config.url ?? "");

    if (method === "POST" && /(?:^|\/)customers(?:$|\/)/.test(url)) {
      const rewritten = rewriteCustomerCreateBody(config.data);
      if (rewritten !== config.data) {
        config.data = rewritten;
      }
    }

    return config;
  });

  axiosInterceptorInstalled = true;
}

function installBrowserRequestGuards(): void {
  if (window.__wellracomCustomerSourceRequestGuard) return;

  const originalFetch = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const requestUrl =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    const method = (
      init?.method ?? (input instanceof Request ? input.method : "GET")
    ).toUpperCase();

    if (method === "POST" && requestUrl.includes("/customers")) {
      const originalBody = init?.body ?? null;
      const rewrittenBody = rewriteCustomerCreateBody(originalBody);
      if (rewrittenBody !== originalBody) {
        return originalFetch(input, { ...init, body: rewrittenBody as BodyInit });
      }
    }

    return originalFetch(input, init);
  };

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;
  const requestMeta = new WeakMap<XMLHttpRequest, { method: string; url: string }>();

  XMLHttpRequest.prototype.open = function (
    method: string,
    url: string | URL,
    async?: boolean,
    username?: string | null,
    password?: string | null,
  ) {
    requestMeta.set(this, { method: method.toUpperCase(), url: String(url) });
    return originalOpen.call(
      this,
      method,
      url,
      async ?? true,
      username ?? null,
      password ?? null,
    );
  };

  XMLHttpRequest.prototype.send = function (
    body?: Document | XMLHttpRequestBodyInit | null,
  ) {
    const meta = requestMeta.get(this);
    if (meta?.method === "POST" && meta.url.includes("/customers")) {
      body = rewriteCustomerCreateBody(body) as Document | XMLHttpRequestBodyInit | null;
    }
    return originalSend.call(this, body);
  };

  window.__wellracomCustomerSourceRequestGuard = true;
}

declare global {
  interface Window {
    __wellracomCustomerSourceRequestGuard?: boolean;
  }
}

function startCustomerSourceEnhancement(): void {
  if (observerStarted) return;
  observerStarted = true;

  installAxiosRequestGuard();
  installBrowserRequestGuards();
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
    if (
      target instanceof HTMLSelectElement &&
      target.dataset.testid === SOURCE_TEST_ID
    ) {
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
