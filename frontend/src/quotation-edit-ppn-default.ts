// Set the PPN field to 11% only while the Quotation Edit modal is open.
const applyDefaultPpn = () => {
  const editModal = Array.from(document.querySelectorAll('[role="dialog"]')).find((dialog) =>
    (dialog.textContent || '').includes('Edit Quotation'),
  );
  if (!editModal) return;

  editModal.querySelectorAll<HTMLInputElement>('[data-testid^="quotation-tax-input-"]').forEach((input) => {
    if (input.value !== '11') {
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
      setter?.call(input, '11');
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
};

const observer = new MutationObserver(applyDefaultPpn);
observer.observe(document.body, { childList: true, subtree: true });
applyDefaultPpn();
