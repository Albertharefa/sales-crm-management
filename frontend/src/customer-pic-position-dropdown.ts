const PIC_POSITION_SELECT_ATTR = 'data-customer-pic-position-select';
const STYLE_ID = 'customer-pic-position-dropdown-style';

const PIC_POSITIONS = [
  'Sales',
  'Marketing',
  'Purchasing',
  'Procurement',
  'Manager',
  'Supervisor',
  'Engineer',
  'Maintenance',
  'Production',
  'Planner',
  'IT',
  'Finance',
  'Director',
];

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
    [${PIC_POSITION_SELECT_ATTR}] {
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
    [${PIC_POSITION_SELECT_ATTR}]:focus {
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

function setupPicPosition() {
  const form = document.querySelector('[data-testid="customer-create-form"]');
  if (!form) return;

  const input = form.querySelector<HTMLInputElement>(
    '[data-testid="customer-pic-position-input"]',
  );
  if (!input) return;

  let select = form.querySelector<HTMLSelectElement>(
    `[${PIC_POSITION_SELECT_ATTR}]`,
  );

  ensureStyle();

  if (!select) {
    select = document.createElement('select');
    select.setAttribute(PIC_POSITION_SELECT_ATTR, 'true');
    select.className = input.className;
    input.insertAdjacentElement('beforebegin', select);

    addOption(select, '', '— Pilih jabatan PIC —');
    PIC_POSITIONS.forEach((position) => addOption(select, position));
    addOption(select, 'OTHER', 'Lainnya');

    select.addEventListener('change', () => {
      if (select?.value === 'OTHER') {
        input.style.display = '';
        setReactInputValue(input, '');
        input.focus();
        return;
      }

      input.style.display = 'none';
      setReactInputValue(input, select?.value ?? '');
    });
  }

  const currentValue = input.value.trim();
  const matched = PIC_POSITIONS.find(
    (position) => position.toLowerCase() === currentValue.toLowerCase(),
  );

  if (!currentValue) {
    select.value = '';
    input.style.display = 'none';
  } else if (matched) {
    select.value = matched;
    input.style.display = 'none';
  } else {
    select.value = 'OTHER';
    input.style.display = '';
  }
}

let queued = false;
function schedule() {
  if (queued) return;
  queued = true;
  window.setTimeout(() => {
    queued = false;
    setupPicPosition();
  }, 0);
}

const observer = new MutationObserver(schedule);
observer.observe(document.body, { childList: true, subtree: true });
schedule();
