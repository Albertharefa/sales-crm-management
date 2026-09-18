import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import AppShell from './components/AppShell';
import Login from './pages/LoginProduction';
import ResetPassword from './pages/ResetPassword';
import Home from './pages/Home';
import Customers from './pages/Customers';
import CustomerDetail from './pages/CustomerDetail';
import Pipeline from './pages/Pipeline';
import Quotations from './pages/Quotations';
import QuotationPrint from './pages/QuotationPrint';
import PurchaseOrders from './pages/PurchaseOrders';
import PurchaseOrderDetail from './pages/PurchaseOrderDetail';
import OrderMonitoring from './pages/OrderMonitoring';
import Activities from './pages/Activities';
import Products from './pages/Products';
import SalesTeam from './pages/SalesTeam';
import SalesTargets from './pages/SalesTargets';
import Users from './pages/Users';
import AuditLog from './pages/AuditLog';
import Settings from './pages/Settings';

function Protected({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

/**
 * Customer > Tambah Customer enhancement:
 * when Industri = Lainnya, expose a free-text field and pass the typed
 * industry value through the existing controlled form state before submit.
 * This is scoped strictly to the customer-create form.
 */
function CustomerIndustryOtherEnhancer() {
  useEffect(() => {
    let activeForm: HTMLFormElement | null = null;
    let cleanupForm: (() => void) | null = null;

    const setup = () => {
      const form = document.querySelector<HTMLFormElement>(
        '[data-testid="customer-create-form"]',
      );

      if (!form || form === activeForm) return;

      cleanupForm?.();
      activeForm = form;

      const select = form.querySelector<HTMLSelectElement>(
        '[data-testid="customer-industry-input"]',
      );
      if (!select) return;

      if (![...select.options].some((option) => option.value === 'Lainnya')) {
        const otherOption = document.createElement('option');
        otherOption.value = 'Lainnya';
        otherOption.textContent = 'Lainnya';
        select.appendChild(otherOption);
      }

      const input = document.createElement('input');
      input.type = 'text';
      input.placeholder = 'Tulis industri lainnya...';
      input.className = select.className;
      input.style.marginTop = '6px';
      input.style.display = select.value === 'Lainnya' ? 'block' : 'none';
      input.setAttribute('data-testid', 'customer-industry-other-input');

      select.insertAdjacentElement('afterend', input);

      const syncVisibility = () => {
        input.style.display = select.value === 'Lainnya' ? 'block' : 'none';
        if (select.value !== 'Lainnya') input.value = '';
      };

      const submitHandler = () => {
        if (select.value !== 'Lainnya') return;

        const customIndustry = input.value.trim();
        if (!customIndustry) return;

        let customOption = [...select.options].find(
          (option) => option.dataset.customerIndustryCustom === 'true',
        );

        if (!customOption) {
          customOption = document.createElement('option');
          customOption.dataset.customerIndustryCustom = 'true';
          select.appendChild(customOption);
        }

        customOption.value = customIndustry;
        customOption.textContent = customIndustry;
        select.value = customIndustry;

        select.dispatchEvent(new Event('change', { bubbles: true }));
      };

      select.addEventListener('change', syncVisibility);
      form.addEventListener('submit', submitHandler, true);

      cleanupForm = () => {
        select.removeEventListener('change', syncVisibility);
        form.removeEventListener('submit', submitHandler, true);
        input.remove();
        activeForm = null;
        cleanupForm = null;
      };
    };

    const observer = new MutationObserver(setup);
    observer.observe(document.body, { childList: true, subtree: true });
    setup();

    return () => {
      observer.disconnect();
      cleanupForm?.();
    };
  }, []);

  return null;
}

export default function App() {
  return (
    <>
      <Toaster position="top-right" richColors />
      <CustomerIndustryOtherEnhancer />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/" element={<Protected><Home /></Protected>} />
        <Route path="/customers" element={<Protected><Customers /></Protected>} />
        <Route path="/customers/:customerId" element={<Protected><CustomerDetail /></Protected>} />
        <Route path="/pipeline" element={<Protected><Pipeline /></Protected>} />
        <Route path="/quotations" element={<Protected><Quotations /></Protected>} />
        <Route path="/quotations/:quotationId/print" element={<QuotationPrint />} />
        <Route path="/purchase-orders" element={<Protected><PurchaseOrders /></Protected>} />
        <Route path="/purchase-orders/:orderId" element={<Protected><PurchaseOrderDetail /></Protected>} />
        <Route path="/order-monitoring" element={<Protected><OrderMonitoring /></Protected>} />
        <Route path="/activities" element={<Protected><Activities /></Protected>} />
        <Route path="/products" element={<Protected><Products /></Protected>} />
        <Route path="/sales-team" element={<Protected><SalesTeam /></Protected>} />
        <Route path="/sales-targets" element={<Protected><SalesTargets /></Protected>} />
        <Route path="/users" element={<Protected><Users /></Protected>} />
        <Route path="/audit-log" element={<Protected><AuditLog /></Protected>} />
        <Route path="/settings" element={<Protected><Settings /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
