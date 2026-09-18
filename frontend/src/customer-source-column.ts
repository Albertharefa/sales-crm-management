import { apiGet } from './lib/api';
import type { Customer, Paginated } from './lib/types';

const PAGE_SIZE = 1000;
const HEADER_ATTR = 'data-customer-source-header';
const CELL_ATTR = 'data-customer-source-cell';

function text(value: unknown) {
  return String(value ?? '').trim();
}

function isCustomersPage() {
  return window.location.pathname.replace(/\/+$/, '') === '/customers';
}

async function getSources() {
  const response = await apiGet<Paginated<Customer>>(
    `/customers?page=1&page_size=${PAGE_SIZE}`,
  );

  return new Map(
    (response?.items ?? []).map((customer) => [
      text(customer.customer_id),
      text(customer.source),
    ]),
  );
}

function findCustomersTable() {
  return document.querySelector<HTMLTableElement>(
    '[data-testid="customers-page"] table',
  );
}

function ensureSourceHeader(table: HTMLTableElement) {
  const headerRow = table.querySelector('thead tr');
  if (!headerRow) return false;

  if (headerRow.querySelector(`[${HEADER_ATTR}]`)) return true;

  const headers = Array.from(headerRow.children) as HTMLElement[];
  const industryHeader = headers.find(
    (cell) => text(cell.textContent).toLowerCase() === 'industri',
  );

  if (!industryHeader) return false;

  const sourceHeader = document.createElement('th');
  sourceHeader.className = industryHeader.className;
  sourceHeader.textContent = 'Sumber';
  sourceHeader.setAttribute(HEADER_ATTR, 'true');
  industryHeader.insertAdjacentElement('afterend', sourceHeader);
  return true;
}

function ensureSourceCells(
  table: HTMLTableElement,
  sourceMap: Map<string, string>,
) {
  const rows = table.querySelectorAll<HTMLTableRowElement>('tbody tr');

  rows.forEach((row) => {
    if (row.querySelector(`[${CELL_ATTR}]`)) return;

    const cells = Array.from(row.children) as HTMLElement[];
    if (cells.length < 4) return;

    const customerId = text(cells[1]?.textContent);
    const industryCell = cells[3];
    if (!industryCell) return;

    const sourceCell = document.createElement('td');
    sourceCell.className = industryCell.className;
    sourceCell.textContent = sourceMap.get(customerId) || '—';
    sourceCell.setAttribute(CELL_ATTR, 'true');
    industryCell.insertAdjacentElement('afterend', sourceCell);
  });
}

async function patchCustomerTable() {
  if (!isCustomersPage()) return;

  const table = findCustomersTable();
  if (!table) return;

  // IMPORTANT: render the column first. The UI must not depend on the
  // secondary source lookup succeeding.
  const headerReady = ensureSourceHeader(table);
  if (!headerReady) return;

  try {
    const sourceMap = await getSources();
    ensureSourceCells(table, sourceMap);
  } catch {
    // Keep the Sumber column visible even if the secondary lookup fails.
    ensureSourceCells(table, new Map());
  }
}

let observer: MutationObserver | undefined;
let timer: number | undefined;
let running = false;
let queued = false;

function schedulePatch() {
  if (queued) return;
  queued = true;
  window.setTimeout(() => {
    queued = false;
    if (running) return;
    running = true;
    void patchCustomerTable().finally(() => {
      running = false;
    });
  }, 50);
}

function start() {
  observer?.disconnect();
  if (timer !== undefined) window.clearInterval(timer);

  observer = new MutationObserver(() => schedulePatch());
  observer.observe(document.body, { childList: true, subtree: true });

  timer = window.setInterval(schedulePatch, 2000);
  schedulePatch();
}

start();
