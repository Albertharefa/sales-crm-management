import { apiGet } from './lib/api';

type CustomerOptionRow = {
  industry?: string | null;
  source?: string | null;
};

type CustomerOptionResponse = {
  items?: CustomerOptionRow[];
};

const BASE_INDUSTRIES = [
  'Manufacturing',
  'Oil & Gas',
  'Mining',
  'Otomotif',
  'FMCG',
  'Telekomunikasi',
  'Konstruksi',
  'EPC',
  'Power Generation',
  'Lainnya',
];

const BASE_SOURCES = [
  'Referral',
  'Website',
  'Pameran',
  'Cold Call',
  'Partner',
  'Lainnya',
];

const SYNC_ATTR = 'data-customer-options-synced';
const clean = (value: unknown) => String(value ?? '').trim();

let syncPromise: Promise<CustomerOptionResponse> | null = null;
const syncedElements = new WeakSet<HTMLSelectElement>();

function loadCustomerOptions() {
  if (!syncPromise) {
    syncPromise = apiGet<CustomerOptionResponse>('/customers?page=1&page_size=100')
      .finally(() => {
        syncPromise = null;
      });
  }
  return syncPromise;
}

function appendMissingOptions(select: HTMLSelectElement, values: string[]) {
  const existing = new Set(
    Array.from(select.options).map((option) => clean(option.value || option.textContent)),
  );

  for (const value of values) {
    if (!value || existing.has(value)) continue;
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
    existing.add(value);
  }
}

async function syncCustomerCustomOptions(
  industrySelect: HTMLSelectElement | null,
  sourceSelect: HTMLSelectElement | null,
) {
  if (!industrySelect && !sourceSelect) return;

  const targets = [industrySelect, sourceSelect].filter(
    (select): select is HTMLSelectElement => Boolean(select),
  );

  if (targets.length > 0 && targets.every((select) => syncedElements.has(select))) return;

  try {
    const response = await loadCustomerOptions();
    const rows = response?.items ?? [];

    const industries = [...BASE_INDUSTRIES];
    const sources = [...BASE_SOURCES];

    for (const row of rows) {
      const industry = clean(row.industry);
      const source = clean(row.source);
      if (industry && !industries.includes(industry) && industry.toLowerCase() !== 'lainnya') {
        industries.push(industry);
      }
      if (source && !sources.includes(source) && source.toLowerCase() !== 'lainnya') {
        sources.push(source);
      }
    }

    if (industrySelect) {
      appendMissingOptions(industrySelect, industries);
      industrySelect.setAttribute(SYNC_ATTR, 'true');
      syncedElements.add(industrySelect);
    }

    if (sourceSelect) {
      appendMissingOptions(sourceSelect, sources);
      sourceSelect.setAttribute(SYNC_ATTR, 'true');
      syncedElements.add(sourceSelect);
    }
  } catch {
    // Keep the normal static options if the custom-option lookup fails.
  }
}

function findCustomerOptionSelects() {
  if (window.location.pathname !== '/customers') return;

  const industrySelect = document.querySelector<HTMLSelectElement>(
    '[data-testid="customer-industry-input"]',
  );
  const sourceSelect = document.querySelector<HTMLSelectElement>(
    '[data-testid="customer-source-input"]',
  );

  if (!industrySelect && !sourceSelect) return;

  void syncCustomerCustomOptions(industrySelect, sourceSelect);
}

let observer: MutationObserver | undefined;

function startCustomerOptionSync() {
  observer?.disconnect();
  observer = new MutationObserver(() => findCustomerOptionSelects());
  observer.observe(document.body, { childList: true, subtree: true });

  findCustomerOptionSelects();
}

startCustomerOptionSync();
