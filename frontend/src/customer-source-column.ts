import { apiGet } from './lib/api';
import type { Customer, Paginated } from './lib/types';

// Backend /customers currently accepts a maximum page_size of 100.
// Keep this lookup within the API contract so the Sumber column reads the
// real customer.source values.
const PAGE_SIZE = 100;
const HEADER_ATTR = 'data-customer-source-header';
const CELL_ATTR = 'data-customer-source-cell';

function text(value: unknown) {
  return String(value ?? '').trim();
}

function isCustomersPage() {
  return window.location.pathname.replace(/\/+$/, '') === '/customers';
}

let sourceMapCache: Map<string, string> | null = null;
let sourceMapPromise: Promise<Map<string, string>> | null = null;

async function getSources() {
  if (sourceMapCache) return sourceMapCache;

  if (!sourceMapPromise) {
    sourceMapPromise = apiGet<Paginated<Customer>>(
      `/customers?page=1&page_size=${PAGE_SIZE}`,
    )
      .then((response) => {
        sourceMapCache = new Map(
          (response?.items ?? []).map((customer) => [
            text(customer.customer_id),
            text(customer.source),
          ]),
        );
        return sourceMapCache;
      })
      .finally(() => {
        sourceMapPromise = null;
      });
  }

  return sourceMapPromise;
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

  // IMPORTANT: load the real Sumber data BEFORE modifying the DOM.
  // This prevents the existing Kota cell from ever appearing under Sumber.
  try {
    const sourceMap = await getSources();
    const headerReady = ensureSourceHeader(table);
    if (!headerReady) return;
    ensureSourceCells(table, sourceMap);
  } catch {
    // Do not inject a misleading/empty Sumber column when the source lookup fails.
    // The existing Customers table remains untouched in that case.
  }
}

let observer: MutationObserver | undefined;
let queued = false;
let running = false;

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
  }, 0);
}

function start() {
  observer?.disconnect();

  observer = new MutationObserver(() => schedulePatch());
  observer.observe(document.body, { childList: true, subtree: true });

  schedulePatch();
}

start();
