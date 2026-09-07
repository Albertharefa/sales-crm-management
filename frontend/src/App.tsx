import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';

import AppShell from './components/AppShell';
import Login from './pages/Login';
import Home from './pages/Home';
import Customers from './pages/Customers';
import Pipeline from './pages/Pipeline';
import Quotations from './pages/Quotations';
import PurchaseOrders from './pages/PurchaseOrders';
import OrderMonitoring from './pages/OrderMonitoring';
import Activities from './pages/Activities';
import Products from './pages/Products';
import SalesTeam from './pages/SalesTeam';
import Users from './pages/Users';
import AuditLog from './pages/AuditLog';
import Settings from './pages/Settings';

function Protected({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

export default function App() {
  return (
    <>
      <Toaster position="top-right" richColors />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Protected><Home /></Protected>} />
        <Route path="/customers" element={<Protected><Customers /></Protected>} />
        <Route path="/pipeline" element={<Protected><Pipeline /></Protected>} />
        <Route path="/quotations" element={<Protected><Quotations /></Protected>} />
        <Route path="/purchase-orders" element={<Protected><PurchaseOrders /></Protected>} />
        <Route path="/order-monitoring" element={<Protected><OrderMonitoring /></Protected>} />
        <Route path="/activities" element={<Protected><Activities /></Protected>} />
        <Route path="/products" element={<Protected><Products /></Protected>} />
        <Route path="/sales-team" element={<Protected><SalesTeam /></Protected>} />
        <Route path="/users" element={<Protected><Users /></Protected>} />
        <Route path="/audit-log" element={<Protected><AuditLog /></Protected>} />
        <Route path="/settings" element={<Protected><Settings /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
