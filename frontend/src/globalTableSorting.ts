type SortDirection = 'asc' | 'desc';

type SortState = { index: number; direction: SortDirection };

const states = new WeakMap<HTMLTableElement, SortState>();

function normalize(value: string) {
  return value.replace(/\s+/g, ' ').trim();
}

function numericValue(value: string): number | null {
  const text = normalize(value).replace(/Rp|IDR|%/gi, '').trim();
  if (!text) return null;
  const cleaned = text.replace(/[^0-9,.-]/g, '');
  if (!cleaned || !/[0-9]/.test(cleaned)) return null;
  if (/^-?\d{1,3}(\.\d{3})+(,\d+)?$/.test(cleaned)) {
    const parsed = Number(cleaned.replace(/\./g, '').replace(',', '.'));
    return Number.isFinite(parsed) ? parsed : null;
  }
  const parsed = Number(cleaned.replace(/,/g, ''));
  return Number.isFinite(parsed) ? parsed : null;
}

function dateValue(value: string): number | null {
  const text = normalize(value);
  if (!text || !/[0-9]/.test(text)) return null;
  const timestamp = Date.parse(text);
  return Number.isNaN(timestamp) ? null : timestamp;
}

function compareValues(a: string, b: string) {
  const aNumeric = numericValue(a);
  const bNumeric = numericValue(b);
  if (aNumeric !== null && bNumeric !== null) return aNumeric - bNumeric;

  const aDate = dateValue(a);
  const bDate = dateValue(b);
  if (aDate !== null && bDate !== null) return aDate - bDate;

  return a.localeCompare(b, 'id-ID', { numeric: true, sensitivity: 'base' });
}

function isExcludedHeader(label: string) {
  return /^(no|aksi|action|actions)$/i.test(normalize(label));
}

function renumberRows(table: HTMLTableElement) {
  const firstHeader = table.tHead?.rows[0]?.cells[0];
  if (!firstHeader || !/^no$/i.test(normalize(firstHeader.textContent ?? ''))) return;

  const rows = Array.from(table.tBodies[0]?.rows ?? []).filter(
    row => !row.querySelector('[data-global-sort-skeleton]'),
  );

  rows.forEach((row, index) => {
    const numberCell = row.cells[0];
    if (!numberCell) return;

    // Keep the No column as a visual row index: 1, 2, 3... after every sort.
    numberCell.textContent = String(index + 1);
  });
}

function updateHeaderIndicators(table: HTMLTableElement, activeIndex: number, direction: SortDirection) {
  Array.from(table.tHead?.rows[0]?.cells ?? []).forEach((cell, index) => {
    const button = cell.querySelector<HTMLElement>('[data-global-sort-button]');
    if (!button) return;
    const indicator = button.querySelector<HTMLElement>('[data-global-sort-indicator]');
    if (!indicator) return;
    indicator.textContent = index === activeIndex ? (direction === 'asc' ? ' ↑' : ' ↓') : ' ↕';
  });
}

function sortTable(table: HTMLTableElement, columnIndex: number) {
  const header = table.tHead?.rows[0]?.cells[columnIndex];
  if (!header || isExcludedHeader(header.textContent ?? '')) return;

  const previous = states.get(table);
  const direction: SortDirection = previous?.index === columnIndex && previous.direction === 'asc' ? 'desc' : 'asc';
  states.set(table, { index: columnIndex, direction });

  const tbody = table.tBodies[0];
  if (!tbody) return;
  const rows = Array.from(tbody.rows).filter(row => !row.querySelector('[data-global-sort-skeleton]'));
  const indexed = rows.map((row, originalIndex) => ({ row, originalIndex }));

  indexed.sort((left, right) => {
    const a = normalize(left.row.cells[columnIndex]?.textContent ?? '');
    const b = normalize(right.row.cells[columnIndex]?.textContent ?? '');
    const result = compareValues(a, b);
    return result === 0 ? left.originalIndex - right.originalIndex : direction === 'asc' ? result : -result;
  });

  const fragment = document.createDocumentFragment();
  indexed.forEach(({ row }) => fragment.appendChild(row));
  tbody.appendChild(fragment);

  // No is never sorted with the other columns. It always reflects the
  // current visible row order: 1, 2, 3... after sorting.
  renumberRows(table);
  updateHeaderIndicators(table, columnIndex, direction);
}

function enhanceHeader(table: HTMLTableElement) {
  const headerCells = table.tHead?.rows[0]?.cells;
  if (!headerCells) return;

  Array.from(headerCells).forEach((cell, index) => {
    if (cell.dataset.globalSortReady === 'true') return;
    const label = normalize(cell.textContent ?? '');
    if (isExcludedHeader(label)) return;

    const original = cell.textContent ?? '';
    cell.textContent = '';
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.globalSortButton = 'true';
    button.className = 'crm-global-sort-button';
    button.title = 'Klik untuk mengurutkan';
    button.setAttribute('aria-label', `Urutkan ${label}`);

    const text = document.createElement('span');
    text.textContent = original;
    const indicator = document.createElement('span');
    indicator.dataset.globalSortIndicator = 'true';
    indicator.textContent = ' ↕';
    indicator.setAttribute('aria-hidden', 'true');

    button.append(text, indicator);
    cell.appendChild(button);
    cell.dataset.globalSortReady = 'true';
    button.addEventListener('click', () => sortTable(table, index));
  });

  // Normalize the initial No column as well, without changing any data values.
  renumberRows(table);
}

function enhanceAllTables() {
  document.querySelectorAll<HTMLTableElement>('table').forEach(enhanceHeader);
}

// Lightweight global enhancement: no MutationObserver, polling, or API/data changes.
let scheduled = false;
function scheduleEnhance() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => {
    scheduled = false;
    enhanceAllTables();
  });
}

document.addEventListener('click', (event) => {
  const target = event.target as HTMLElement | null;
  if (target?.closest('a,button,[role="button"]')) {
    requestAnimationFrame(scheduleEnhance);
  }
}, true);

window.addEventListener('popstate', scheduleEnhance);
window.addEventListener('hashchange', scheduleEnhance);

enhanceAllTables();
