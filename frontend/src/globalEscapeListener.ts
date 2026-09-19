function isVisible(element: Element) {
  const node = element as HTMLElement;
  return !!(node.offsetWidth || node.offsetHeight || node.getClientRects().length);
}

const CRM_MENU_ROOTS = [
  '/customers',
  '/pipeline',
  '/quotations',
  '/purchase-orders',
  '/activities',
  '/order-monitoring',
  '/products',
  '/sales-team',
  '/sales-targets',
  '/users',
  '/audit-log',
  '/settings',
];

function isScopedCrmMenu(pathname: string) {
  return CRM_MENU_ROOTS.some(
    (root) => pathname === root || pathname.startsWith(`${root}/`),
  );
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

function getParentMenu(pathname: string) {
  if (/^\/customers\/[^/]+$/.test(pathname)) return '/customers';
  if (/^\/purchase-orders\/[^/]+$/.test(pathname)) return '/purchase-orders';
  if (/^\/quotations\/[^/]+\/print$/.test(pathname)) return '/quotations';
  return null;
}

function handleGlobalEscape(event: KeyboardEvent) {
  if (event.key !== 'Escape' || event.defaultPrevented) return;

  const pathname = window.location.pathname;

  // ESC is intentionally scoped to CRM menu areas only.
  // Dashboard, login, reset-password and any page outside these menus are untouched.
  if (!isScopedCrmMenu(pathname)) return;

  // First close an open modal/drawer. This covers Add/Edit/Detail forms that
  // are implemented as overlays and keeps the user on the current menu.
  if (closeOpenOverlay()) {
    event.preventDefault();
    return;
  }

  // Let native select controls release their open dropdown first.
  const active = document.activeElement as HTMLElement | null;
  if (active?.tagName === 'SELECT') {
    active.blur();
    event.preventDefault();
    return;
  }

  // Never interfere with text editing. The user can press Escape to blur the
  // field, but it must not navigate away from the form.
  const isEditingText = !!active && (
    active.tagName === 'INPUT' ||
    active.tagName === 'TEXTAREA' ||
    active.isContentEditable
  );

  if (isEditingText) {
    active.blur();
    event.preventDefault();
    return;
  }

  // Route-based child pages return directly to their owning CRM menu.
  // We intentionally do NOT use history.back(), preventing ESC from behaving
  // like an Undo Page and walking through unrelated browser history.
  const parentMenu = getParentMenu(pathname);
  if (parentMenu) {
    event.preventDefault();
    window.history.replaceState({}, '', parentMenu);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }

  // On a CRM menu root there is no parent action: ESC does nothing.
}

document.addEventListener('keydown', handleGlobalEscape);
