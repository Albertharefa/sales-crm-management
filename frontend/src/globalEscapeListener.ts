function isVisible(element: Element) {
  const node = element as HTMLElement;
  return !!(node.offsetWidth || node.offsetHeight || node.getClientRects().length);
}

function closeOpenOverlay() {
  const overlays = Array.from(
    document.querySelectorAll<HTMLElement>(
      '[role="dialog"], [data-radix-dialog-content], [data-radix-alert-dialog-content], [data-state="open"][data-slot="dialog-content"]',
    ),
  ).filter(isVisible);

  if (!overlays.length) return false;

  const overlay = overlays[overlays.length - 1];
  const closeButton = overlay.querySelector<HTMLElement>(
    '[data-radix-dialog-close], [aria-label="Close"], [aria-label="Tutup"], [data-testid*="close"], [data-testid*="cancel"]',
  );

  if (!closeButton) return false;
  closeButton.click();
  return true;
}

function handleGlobalEscape(event: KeyboardEvent) {
  if (event.key !== 'Escape' || event.defaultPrevented) return;

  // First close an open modal/drawer. Component-level Escape handlers remain
  // authoritative when they already prevent the event.
  if (closeOpenOverlay()) {
    event.preventDefault();
    return;
  }

  // Allow native select controls to release their open dropdown first.
  const active = document.activeElement as HTMLElement | null;
  if (active?.tagName === 'SELECT') {
    active.blur();
    event.preventDefault();
    return;
  }

  // Never apply global back behavior on authentication pages.
  const pathname = window.location.pathname;
  if (pathname === '/login' || pathname === '/reset-password') return;

  // Global CRM rule: ESC closes route-based add/edit/detail pages by returning
  // to the page the user came from. It never submits a form.
  event.preventDefault();
  window.history.back();
}

document.addEventListener('keydown', handleGlobalEscape);
