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

const clean = (value: unknown) => String(value ?? '').trim();

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

async function syncCustomerCustomOptions() {
  if (window.location.pathname !== '/customers') return;

  const industrySelect = document.querySelector<HTMLSelectElement>(
    '[data-testid="customer-industry-input"]',
  );
  const sourceSelect = document.querySelector<HTMLSelectElement>(
    '[data-testid="customer-source-input"]',
  );

  if (!industrySelect && !sourceSelect) return;

  try {
    const response = await apiGet<CustomerOptionResponse>('/customers?page=1&page_size=100');
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

    if (industrySelect) appendMissingOptions(industrySelect, industries);
    if (sourceSelect) appendMissingOptions(sourceSelect, sources);
  } catch {
    // Keep the normal static options if the custom-option lookup fails.
  }
}

let timer: number | undefined;

function startCustomerOptionSync() {
  if (timer !== undefined) window.clearInterval(timer);
  timer = window.setInterval(() => {
    void syncCustomerCustomOptions();
  }, 1500);
  void syncCustomerCustomOptions();
}

startCustomerOptionSync();
