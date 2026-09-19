import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

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

  if (closeButton) {
    closeButton.click();
    return true;
  }

  return false;
}

export function useGlobalEscape() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || event.defaultPrevented) return;

      // Let browser/select and component-level Escape behavior run first.
      if (closeOpenOverlay()) {
        event.preventDefault();
        return;
      }

      // For route-based add/edit/detail pages, Escape returns to the previous page.
      // Never submit a form and never interfere with normal text input.
      const active = document.activeElement as HTMLElement | null;
      const isEditingText = !!active && (
        active.tagName === "INPUT" ||
        active.tagName === "TEXTAREA" ||
        active.isContentEditable
      );

      if (isEditingText) {
        active.blur();
        event.preventDefault();
        return;
      }

      if (location.pathname !== "/login" && location.pathname !== "/reset-password") {
        event.preventDefault();
        navigate(-1);
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [location.pathname, navigate]);
}
