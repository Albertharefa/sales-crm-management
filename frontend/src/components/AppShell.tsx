import { useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { apiGet } from "@/lib/api";
import { endSession } from "@/lib/session";
import type { User } from "@/lib/types";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { BarChart3, Bell, Boxes, ClipboardCheck, FileText, Gauge, LogOut, Menu, PackageCheck, PanelLeft, Settings, ShieldCheck, ShoppingCart, Target, Users, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Toaster } from "@/components/ui/sonner";
import AICopilot from "@/components/AICopilot";

const navGroups = [
  { label: "CRM DATABASE", items: [{ label: "Dashboard", to: "/", icon: Gauge }, { label: "Customers", to: "/customers", icon: Users }, { label: "Sales Pipeline", to: "/pipeline", icon: BarChart3 }, { label: "Aktivitas", to: "/activities", icon: ClipboardCheck }, { label: "Quotations", to: "/quotations", icon: FileText }, { label: "Purchase Orders", to: "/purchase-orders", icon: ShoppingCart }, { label: "Order Monitoring", to: "/order-monitoring", icon: PackageCheck }] },
  { label: "MANAGEMENT", items: [{ label: "Sales Team", to: "/sales-team", icon: Target }, { label: "Audit Log", to: "/audit-log", icon: ShieldCheck }] },
  { label: "ADMINISTRATION", items: [{ label: "Users", to: "/users", icon: Users }, { label: "Products", to: "/products", icon: Boxes }, { label: "Settings", to: "/settings", icon: Settings }] },
];

export function useCurrentUser() {
  return useQuery({ queryKey: ["me"], queryFn: () => apiGet<User>("/me"), retry: false, staleTime: 60_000 });
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: user, error: sessionError, isLoading: sessionLoading, isError: sessionFailed, refetch: refetchSession } = useCurrentUser();
  const [mobileOpen, setMobileOpen] = useState(false);

  async function logout() {
    await endSession();
    queryClient.clear();
    toast.success("Sesi berhasil diakhiri");
    navigate("/login");
  }

  useEffect(() => {
    if (axios.isAxiosError(sessionError) && sessionError.response?.status === 401) {
      queryClient.clear();
      navigate("/login", { replace: true });
    }
  }, [navigate, queryClient, sessionError]);

  if (sessionLoading) return <div className="flex min-h-svh items-center justify-center bg-slate-50" data-testid="session-loading"><div className="text-center"><div className="mx-auto size-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" /><p className="mt-4 text-sm text-slate-500">Memverifikasi sesi CRM...</p></div></div>;
  if (sessionFailed) {
    if (axios.isAxiosError(sessionError) && sessionError.response?.status === 401) {
      return <Navigate to="/login" replace />;
    }
    const status = axios.isAxiosError(sessionError) ? sessionError.response?.status : undefined;
    return <div className="flex min-h-svh items-center justify-center bg-slate-50 p-6" data-testid="session-error"><div className="max-w-sm rounded-xl border border-slate-200 bg-white p-6 text-center shadow-sm"><h1 className="font-heading text-lg font-semibold">Sesi tidak tersedia</h1><p className="mt-2 text-sm text-slate-500">{status ? `Server mengembalikan HTTP ${status}. Pastikan MongoDB dan Railway Variables sudah benar.` : "Kami tidak dapat memverifikasi sesi Anda. Coba lagi atau masuk kembali."}</p><Button className="mt-5" onClick={() => void refetchSession()} data-testid="session-retry-button">Coba lagi</Button></div></div>;
  }
  if (!user) return <Navigate to="/login" replace />;

  const visibleGroups = navGroups.map(group => ({
    ...group,
    items: group.items.filter(item => {
      if (item.label === "Users") return user.role === "SUPER_ADMIN" || user.role === "SALES_MANAGER";
      if (item.label === "Audit Log" || item.label === "Sales Team") return user.role === "SUPER_ADMIN" || user.role === "SALES_MANAGER";
      return true;
    }),
  })).filter(group => group.items.length > 0);

  return <div className="min-h-svh bg-slate-50 text-slate-900" data-testid="crm-app-shell">
    <Toaster position="top-right" richColors />
    <aside className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-[#081126] text-white transition-transform duration-200 lg:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`} data-testid="sidebar-navigation">
      <div className="flex items-center gap-3 px-6 py-5"><div className="flex size-9 items-center justify-center rounded-lg bg-blue-600 font-heading text-lg font-bold">C</div><div><div className="font-heading text-sm font-bold">CRM Sales</div><div className="text-[10px] tracking-[0.18em] text-slate-400">MANAGEMENT</div></div><button className="ml-auto lg:hidden" onClick={() => setMobileOpen(false)} data-testid="sidebar-close-button"><X className="size-5" /></button></div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-3">{visibleGroups.map(group => <div key={group.label}><div className="px-3 pb-2 text-[10px] font-semibold tracking-[0.18em] text-slate-500" data-testid={`nav-group-${group.label.toLowerCase().replaceAll(" ", "-")}`}>{group.label}</div><div className="space-y-1">{group.items.map(item => { const Icon = item.icon; const active = location.pathname === item.to; return <Link key={item.to} to={item.to} onClick={() => setMobileOpen(false)} className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors duration-200 ${active ? "bg-blue-600/20 text-blue-300" : "text-slate-300 hover:bg-white/10 hover:text-white"}`} data-testid={`sidebar-link-${item.label.toLowerCase().replaceAll(" ", "-")}`}><Icon className="size-4" />{item.label}</Link>; })}</div></div>)}</nav>
      <div className="border-t border-white/10 px-4 py-4"><div className="mb-3 flex items-center gap-3"><div className="flex size-9 items-center justify-center rounded-full bg-blue-600/20 text-sm font-semibold text-blue-200">{user?.name?.slice(0, 1) ?? "A"}</div><div className="min-w-0"><div className="truncate text-sm font-medium" data-testid="current-user-name">{user?.name ?? "Admin"}</div><div className="truncate text-xs text-slate-400" data-testid="current-user-email">{user?.email ?? "admin@crm.co.id"}</div></div></div><div className="mb-3 inline-flex rounded-full bg-blue-600/15 px-2 py-1 text-[10px] font-semibold text-blue-300" data-testid="current-user-role">{user?.role ?? "SUPER_ADMIN"}</div><Button variant="outline" className="w-full border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white" onClick={logout} data-testid="logout-button"><LogOut className="mr-2 size-4" />Logout</Button></div>
    </aside>
    {mobileOpen && <button className="fixed inset-0 z-40 bg-slate-950/60 lg:hidden" onClick={() => setMobileOpen(false)} data-testid="mobile-sidebar-overlay" aria-label="Close navigation" />}
    <div className="lg:pl-64"><header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur-md sm:px-6"><button className="rounded-md p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={() => setMobileOpen(true)} data-testid="mobile-menu-button"><Menu className="size-5" /></button><div className="hidden items-center gap-2 text-sm text-slate-500 lg:flex"><PanelLeft className="size-4" />Operasional Sales</div><div className="ml-auto flex items-center gap-3"><div className="hidden text-right sm:block"><div className="text-sm font-semibold" data-testid="header-user-name">{user?.name ?? "Admin"}</div><div className="text-xs text-slate-500">{user?.role ?? "SUPER_ADMIN"}</div></div><div className="rounded-full bg-slate-100 p-2 text-slate-600" data-testid="notification-indicator"><Bell className="size-4" /></div></div></header><main className="p-4 sm:p-6 lg:p-8">{children}</main></div>
    <AICopilot />
  </div>;
}
