const setEditQuotationPpnDefault = () => {
  const modalTitle = document.querySelector('[data-testid="modal-title"]')?.textContent?.trim();
  if (modalTitle !== "Edit Quotation") return;

  const taxInputs = document.querySelectorAll<HTMLInputElement>('[data-testid^="quotation-tax-input-"]');
  taxInputs.forEach((input) => {
    if (input.value === "11") return;
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    setter?.call(input, "11");
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });
};

document.addEventListener("click", (event) => {
  const target = event.target as Element | null;
  if (!target?.closest('[data-testid^="quotation-edit-"]')) return;
  window.setTimeout(setEditQuotationPpnDefault, 0);
});
