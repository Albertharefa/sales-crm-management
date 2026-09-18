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

async function patchCustomerTable() {
  if (!isCustomersPage()) return;

  const table = document.querySelector<HTMLTableElement>('[data-testid="customers-page"] table');
  if (!table) return;

  const headerRow = table.querySelector('thead tr');
  if (!headerRow) return;

  let sourceMap: Map<string, string>;
  try {
    sourceMap = await getSources();
  } catch {
    return;
  }

  const headers = Array.from(headerRow.children) as HTMLElement[];
  const industryHeader = headers.find(
    (cell) => text(cell.textContent).toLowerCase() === 'industri',
  );

  if (industryHeader && !headerRow.querySelector(`[${HEADER_ATTR}]`)) {
    const sourceHeader = document.createElement('th');
    sourceHeader.className = industryHeader.className;
    sourceHeader.textContent = 'Sumber';
    sourceHeader.setAttribute(HEADER_ATTR, 'true');
    industryHeader.insertAdjacentElement('afterend', sourceHeader);
  }

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
