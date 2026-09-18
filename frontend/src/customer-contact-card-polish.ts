const SECTION_ATTR = 'data-crm-contact-section';
const CARD_ATTR = 'data-crm-contact-card';
const LABEL_ATTR = 'data-crm-contact-label';

function text(value: unknown) {
  return String(value ?? '').trim();
}

function ensureContactLabels(card: HTMLElement) {
  if (card.hasAttribute(CARD_ATTR)) return;
  const fields = Array.from(card.children) as HTMLElement[];
  if (fields.length < 3) return;

  const addLabel = (target: HTMLElement, label: string) => {
    const el = document.createElement('div');
    el.textContent = label;
    el.setAttribute(LABEL_ATTR, label);
    target.insertAdjacentElement('beforebegin', el);
  };

  addLabel(fields[0], 'NAMA PIC');
  addLabel(fields[1], 'JABATAN');

  const details = fields[2];
  const rows = Array.from(details.children) as HTMLElement[];
  if (rows[0]) addLabel(rows[0], 'TELEPON');
  if (rows[1]) addLabel(rows[1], 'EMAIL');

  card.setAttribute(CARD_ATTR, 'true');
}

function patch() {
  const root = document.querySelector<HTMLElement>('[data-testid="customer-detail-page"]');
  if (!root) return;

  const sections = Array.from(root.querySelectorAll('section')) as HTMLElement[];
  const section = sections.find((item) => text(item.querySelector('h2')?.textContent).toLowerCase() === 'contacts');
  if (!section) return;

  section.setAttribute(SECTION_ATTR, 'true');
  section.querySelectorAll<HTMLElement>(':scope > div').forEach((container) => {
    container.querySelectorAll<HTMLElement>(':scope > div').forEach((card) => {
      const children = Array.from(card.children);
      if (children.length >= 3) ensureContactLabels(card);
    });
  });
}

let queued = false;
function schedule() {
  if (queued) return;
  queued = true;
  window.setTimeout(() => {
    queued = false;
    patch();
  }, 0);
}

const observer = new MutationObserver(schedule);
observer.observe(document.body, { childList: true, subtree: true });
schedule();
