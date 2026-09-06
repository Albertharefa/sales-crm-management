import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';

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

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Toaster position="top-right" richColors />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Home />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/quotations" element={<Quotations />} />
          <Route path="/purchase-orders" element={<PurchaseOrders />} />
          <Route path="/order-monitoring" element={<OrderMonitoring />} />
          <Route path="/activities" element={<Activities />} />
          <Route path="/products" element={<Products />} />
          <Route path="/sales-team" element={<SalesTeam />} />
          <Route path="/users" element={<Users />} />
          <Route path="/audit-log" element={<AuditLog />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}
