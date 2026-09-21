type Province = { id: number; value: string };
type Region = { id: number; province_id: number; type: string; value: string };

const PROVINCES_URL = 'https://ihsaninh.github.io/wilayah-indonesia/provinces.json';
const REGIONS_URL = (provinceId: number) =>
  `https://ihsaninh.github.io/wilayah-indonesia/${provinceId}/regencies.json`;

const PROVINCE_SELECT_ATTR = 'data-customer-location-province-select';
const CITY_SELECT_ATTR = 'data-customer-location-city-select';
const STYLE_ID = 'customer-location-dropdown-style';

let provincesPromise: Promise<Province[]> | null = null;
const regionsCache = new Map<number, Promise<Region[]>>();

function text(value: unknown) {
  return String(value ?? '').trim();
}

function isCreateForm() {
  return !!document.querySelector('[data-testid="customer-create-form"]');
}

function fetchProvinces() {
  if (!provincesPromise) {
    provincesPromise = fetch(PROVINCES_URL)
      .then((response) => {
        if (!response.ok) throw new Error('Gagal memuat provinsi');
        return response.json() as Promise<Province[]>;
      })
      .then((items) => items.filter((item) => item?.id && item?.value));
  }
  return provincesPromise;
}

function fetchRegions(provinceId: number) {
  const cached = regionsCache.get(provinceId);
  if (cached) return cached;

  const request = fetch(REGIONS_URL(provinceId))
    .then((response) => {
      if (!response.ok) throw new Error('Gagal memuat kota');
      return response.json() as Promise<Region[]>;
    })
    .then((items) => items.filter((item) => item?.id && item?.value));

  regionsCache.set(provinceId, request);
  return request;
}

function setReactInputValue(input: HTMLInputElement, value: string) {
  const descriptor = Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype,
    'value',
  );
  descriptor?.set?.call(input, value);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

function ensureStyle() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    [${PROVINCE_SELECT_ATTR}], [${CITY_SELECT_ATTR}] {
      width: 100%;
      min-height: 38px;
      border: 1px solid rgb(226 232 240);
      border-radius: 0.5rem;
      background: white;
      padding: 0.5rem 0.75rem;
      font-size: 0.875rem;
      color: rgb(15 23 42);
      outline: none;
    }
    [${PROVINCE_SELECT_ATTR}]:focus, [${CITY_SELECT_ATTR}]:focus {
      border-color: rgb(59 130 246);
      box-shadow: 0 0 0 1px rgb(59 130 246);
    }
  `;
  document.head.appendChild(style);
}

function addOption(select: HTMLSelectElement, value: string, label = value) {
  const option = document.createElement('option');
  option.value = value;
  option.textContent = label;
  select.appendChild(option);
}

function showInput(input: HTMLInputElement, show: boolean) {
  input.style.display = show ? '' : 'none';
}

function createSelect(input: HTMLInputElement, attr: string) {
  const existing = input.parentElement?.querySelector<HTMLSelectElement>(`[${attr}]`);
  if (existing) return existing;

  const select = document.createElement('select');
  select.setAttribute(attr, 'true');
  select.className = input.className;
  input.insertAdjacentElement('beforebegin', select);
  return select;
}

async function setupLocationFields() {
  if (!isCreateForm()) return;

  const provinceInput = document.querySelector<HTMLInputElement>(
    '[data-testid="customer-province-input"]',
  );
  const cityInput = document.querySelector<HTMLInputElement>(
    '[data-testid="customer-city-input"]',
  );
  if (!provinceInput || !cityInput) return;

  ensureStyle();

  const provinceSelect = createSelect(
    provinceInput,
    PROVINCE_SELECT_ATTR,
  );
  const citySelect = createSelect(cityInput, CITY_SELECT_ATTR);

  if (!provinceSelect || !citySelect) return;

  if (!provinceSelect.dataset.initialized) {
    provinceSelect.dataset.initialized = 'true';
    citySelect.dataset.initialized = 'true';

    provinceSelect.innerHTML = '';
    addOption(provinceSelect, '', '— Pilih provinsi —');

    try {
      const provinces = await fetchProvinces();
      provinces.forEach((province) =>
        addOption(provinceSelect, String(province.id), province.value),
      );
      addOption(provinceSelect, 'OTHER', 'Lainnya');
    } catch {
      addOption(provinceSelect, 'OTHER', 'Lainnya');
    }

    citySelect.innerHTML = '';
    addOption(citySelect, '', '— Pilih kota/kabupaten —');
    addOption(citySelect, 'OTHER', 'Lainnya');
    citySelect.disabled = true;

    provinceSelect.addEventListener('change', async () => {
      const selectedId = provinceSelect.value;
      const selectedLabel =
        provinceSelect.options[provinceSelect.selectedIndex]?.textContent ?? '';

      if (selectedId === 'OTHER') {
        showInput(provinceInput, true);
        setReactInputValue(provinceInput, '');
        showInput(cityInput, true);
        citySelect.style.display = 'none';
        return;
      }

      showInput(provinceInput, false);
      citySelect.style.display = '';
      setReactInputValue(provinceInput, selectedLabel);

      citySelect.innerHTML = '';
      addOption(citySelect, '', '— Memuat kota/kabupaten —');
      citySelect.disabled = true;
      setReactInputValue(cityInput, '');

      if (!selectedId) return;

      try {
        const regions = await fetchRegions(Number(selectedId));
        citySelect.innerHTML = '';
        addOption(citySelect, '', '— Pilih kota/kabupaten —');
        regions
          .sort((a, b) => a.value.localeCompare(b.value, 'id'))
          .forEach((region) => addOption(citySelect, region.value, region.value));
        addOption(citySelect, 'OTHER', 'Lainnya');
        citySelect.disabled = false;
      } catch {
        citySelect.innerHTML = '';
        addOption(citySelect, 'OTHER', 'Lainnya');
        citySelect.value = 'OTHER';
        citySelect.disabled = false;
        showInput(cityInput, true);
        citySelect.style.display = 'none';
      }
    });

    citySelect.addEventListener('change', () => {
      if (citySelect.value === 'OTHER') {
        citySelect.style.display = 'none';
        showInput(cityInput, true);
        setReactInputValue(cityInput, '');
        cityInput.focus();
        return;
      }

      citySelect.style.display = '';
      showInput(cityInput, false);
      setReactInputValue(cityInput, citySelect.value);
    });

    // Preserve the existing Customer form default of Jakarta while making the
    // province explicit. This runs only when the Add Customer form is opened.
    if (!text(provinceInput.value) && text(cityInput.value).toLowerCase() === 'jakarta') {
      const jakarta = Array.from(provinceSelect.options).find((option) =>
        option.textContent?.toLowerCase() === 'dki jakarta',
      );
      if (jakarta) {
        provinceSelect.value = jakarta.value;
        provinceSelect.dispatchEvent(new Event('change', { bubbles: true }));
      }
    } else if (text(provinceInput.value)) {
      const existing = Array.from(provinceSelect.options).find(
        (option) => option.textContent?.toLowerCase() === text(provinceInput.value).toLowerCase(),
      );
      if (existing) {
        provinceSelect.value = existing.value;
        provinceSelect.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        provinceSelect.value = 'OTHER';
        showInput(provinceInput, true);
        citySelect.style.display = 'none';
      }
    }
  }
}

let queued = false;
function schedule() {
  if (queued) return;
  queued = true;
  window.setTimeout(() => {
    queued = false;
    void setupLocationFields();
  }, 0);
}

const observer = new MutationObserver(schedule);
observer.observe(document.body, { childList: true, subtree: true });
schedule();
