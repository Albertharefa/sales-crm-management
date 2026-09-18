import { apiGet } from './lib/api';
import type { Customer, Paginated } from './lib/types';

const PAGE_SIZE = 1000;

function clean(value: unknown) {
  return String(value ?? '').trim();
}

async function addCustomerSourceColumn() {
  if (window.location.pathname !== '/customers') return;

  // customers-page is the wrapper div; the table itself does not carry that data-testid.
  const table = document.querySelector<HTMLTableElement>('[data-testid="customers-page"] table');
  if (!table) return;

  try {
    const response = await apiGet<Paginated<Customer>>(
      `/customers?page=1&page_size=${PAGE_SIZE}`,
    );
    const customers = response?.items ?? [];
    const sourceByCustomerId = new Map(
      customers.map((customer) => [clean(customer.customer_id), clean(customer.source)]),
    );

    const headerRow = table.querySelector('thead tr');
    if (headerRow && !headerRow.querySelector('[data-customer-source-header="true"]')) {
      const headers = Array.from(headerRow.children);
      const industryHeader = headers.find(
        (cell) => clean(cell.textContent).toLowerCase() === 'industri',
      );

      if (industryHeader) {
        const sourceHeader = document.createElement('th');
        sourceHeader.className = industryHeader.className;
        sourceHeader.textContent = 'Sumber';
        sourceHeader.dataset.customerSourceHeader = 'true';
        industryHeader.insertAdjacentElement('afterend', sourceHeader);
      }
    }

    table.querySelectorAll<HTMLTableRowElement>('tbody tr[data-testid^="customer-row-"]').forEach((row) => {
      if (row.querySelector('[data-customer-source-cell="true"]')) return;

      const testId = row.getAttribute('data-testid') ?? '';
      const customerId = testId.replace(/^customer-row-/, '');
      const source = sourceByCustomerId.get(customerId) || '—';
      const cells = Array.from(row.children);
      const industryCell = cells[3];

      if (!industryCell) return;

      const sourceCell = document.createElement('td');
      sourceCell.className = industryCell.className;
      sourceCell.textContent = source;
      sourceCell.dataset.customerSourceCell = 'true';
      industryCell.insertAdjacentElement('afterend', sourceCell);
    });
  } catch {
    // Keep the existing customer table intact if the source lookup fails.
  }
}

let timer: number | undefined;
let observer: MutationObserver | undefined;

function startCustomerSourceColumn() {
  if (timer !== undefined) window.clearInterval(timer);
  observer?.disconnect();

  const run = () => void addCustomerSourceColumn();
  timer = window.setInterval(run, 1500);

  observer = new MutationObserver(() => run());
  observer.observe(document.body, { childList: true, subtree: true });

  run();
}

startCustomerSourceColumn();
