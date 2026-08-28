import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import AppShell from "@/components/AppShell";
import Customers from "@/pages/Customers";
import Pipeline from "@/pages/Pipeline";
import Activities from "@/pages/Activities";
import Quotations from "@/pages/Quotations";
import PurchaseOrders from "@/pages/PurchaseOrders";
import OrderMonitoring from "@/pages/OrderMonitoring";
import SalesTeam from "@/pages/SalesTeam";
import AuditLog from "@/pages/AuditLog";
import Users from "@/pages/Users";
import Products from "@/pages/Products";
import Settings from "@/pages/Settings";

function Protected({ children }: { children: React.ReactNode }) { return <AppShell>{children}</AppShell>; }

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Home /></Protected>} />
      <Route path="/customers" element={<Protected><Customers /></Protected>} />
      <Route path="/pipeline" element={<Protected><Pipeline /></Protected>} />
      <Route path="/activities" element={<Protected><Activities /></Protected>} />
      <Route path="/quotations" element={<Protected><Quotations /></Protected>} />
      <Route path="/purchase-orders" element={<Protected><PurchaseOrders /></Protected>} />
      <Route path="/order-monitoring" element={<Protected><OrderMonitoring /></Protected>} />
      <Route path="/sales-team" element={<Protected><SalesTeam /></Protected>} />
      <Route path="/audit-log" element={<Protected><AuditLog /></Protected>} />
      <Route path="/users" element={<Protected><Users /></Protected>} />
      <Route path="/products" element={<Protected><Products /></Protected>} />
      <Route path="/settings" element={<Protected><Settings /></Protected>} />
    </Routes>
  );
}
