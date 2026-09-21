const ACCOUNT_NAME_SELECTORS = [
  '[data-testid="customer-company-input"]',
  '[data-testid="customer-edit-company-input"]',
];

const NAME_SELECTORS = [
  '[data-testid="customer-name-input"]',
  '[data-testid="customer-edit-name-input"]',
];

function setNativeValue(input: HTMLInputElement, value: string) {
  const setter = Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype,
    "value",
  )?.set;
  setter?.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

function hideCompanyField(input: HTMLInputElement) {
  const field = input.closest("div")?.parentElement;
  if (field instanceof HTMLElement) {
    field.dataset.customerCompanyHidden = "true";
    field.style.display = "none";
  }
}

function syncAccountName() {
  const nameInput = NAME_SELECTORS
    .map((selector) => document.querySelector<HTMLInputElement>(selector))
    .find(Boolean);

  const companyInput = ACCOUNT_NAME_SELECTORS
    .map((selector) => document.querySelector<HTMLInputElement>(selector))
    .find(Boolean);

  if (!companyInput) return;

  hideCompanyField(companyInput);

  if (!nameInput) return;

  const sync = () => {
    if (companyInput.value !== nameInput.value) {
      setNativeValue(companyInput, nameInput.value);
    }
  };

  sync();
  nameInput.addEventListener("input", sync);
  nameInput.addEventListener("change", sync);
}

function installSubmitSync() {
  document.addEventListener(
    "submit",
    (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;

      const nameInput = form.querySelector<HTMLInputElement>(
        '[data-testid="customer-name-input"], [data-testid="customer-edit-name-input"]',
      );
      const companyInput = form.querySelector<HTMLInputElement>(
        '[data-testid="customer-company-input"], [data-testid="customer-edit-company-input"]',
      );

      if (nameInput && companyInput) {
        setNativeValue(companyInput, nameInput.value);
      }
    },
    true,
  );
}

function install() {
  syncAccountName();
  installSubmitSync();

  const observer = new MutationObserver(() => syncAccountName());
  observer.observe(document.body, { childList: true, subtree: true });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", install, { once: true });
} else {
  install();
}

export {};