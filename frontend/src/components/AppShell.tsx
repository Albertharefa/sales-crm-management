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
    <aside className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-[radial-gradient(circle_at_18%_8%,rgba(255,193,7,.34),transparent_22%),radial-gradient(circle_at_78%_28%,rgba(255,94,0,.38),transparent_28%),radial-gradient(circle_at_45%_72%,rgba(220,38,38,.34),transparent_32%),linear-gradient(155deg,#4a0909_0%,#7f1d1d_34%,#c2410c_68%,#8a4b08_100%)] text-white shadow-2xl shadow-slate-950/30 transition-transform duration-200 lg:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`} data-testid="sidebar-navigation">
      <div className="relative flex items-center gap-3 border-b border-white/10 px-5 py-5"><div className="absolute inset-x-5 bottom-0 h-px bg-gradient-to-r from-transparent via-amber-300/50 to-transparent" /><div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-white shadow-lg shadow-black/20 ring-1 ring-white/30"><svg viewBox="0 0 225 225" className="size-10" role="img" aria-label="Wellracom logo"><circle cx="112.5" cy="112.5" r="101.5" fill="#fff" stroke="#111" strokeWidth="6"/><path fill="#ff9800" d="M38 54h20l34 70 20.5-40 20.5 40 34-70h20l-43 91-31.5-61-31.5 61z"/><path fill="#111" d="M87 50h51l-10 20-15.5 23-15.5-23zm12 6 13.5 26 13.5-26z"/><path fill="#111" d="M109.5 92h6v57h-6z"/><path fill="#111" d="M86 151h53l-6 10H92z"/><path fill="#111" d="M101 167h23l-11.5 22z"/></svg></div><div className="min-w-0"><div className="font-heading text-[15px] font-bold tracking-tight text-white">CRM Sales</div><div className="mt-0.5 text-[9px] font-medium tracking-[0.22em] text-amber-200/80">WELLRACOM MANAGEMENT</div></div><button className="ml-auto lg:hidden" onClick={() => setMobileOpen(false)} data-testid="sidebar-close-button"><X className="size-5" /></button></div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">{visibleGroups.map(group => <div key={group.label}><div className="px-3 pb-2 text-[9px] font-bold tracking-[0.2em] text-amber-200/55" data-testid={`nav-group-${group.label.toLowerCase().replaceAll(" ", "-")}`}>{group.label}</div><div className="space-y-1">{group.items.map(item => { const Icon = item.icon; const active = location.pathname === item.to; return <Link key={item.to} to={item.to} onClick={() => setMobileOpen(false)} className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors duration-200 ${active ? "bg-gradient-to-r from-white/20 via-amber-300/15 to-red-500/10 text-white font-bold shadow-lg shadow-black/15 ring-1 ring-white/20" : "text-white font-bold hover:bg-white/10 hover:text-white"}`} data-testid={`sidebar-link-${item.label.toLowerCase().replaceAll(" ", "-")}`}><Icon className="size-4" />{item.label}</Link>; })}</div></div>)}</nav>
      <div className="border-t border-white/10 bg-black/10 px-4 py-4 backdrop-blur-sm"><div className="mb-3 flex items-center gap-3"><div className="flex size-9 items-center justify-center rounded-full bg-blue-600/20 text-sm font-semibold text-blue-200">{user?.name?.slice(0, 1) ?? "A"}</div><div className="min-w-0"><div className="truncate text-sm font-medium" data-testid="current-user-name">{user?.name ?? "Admin"}</div><div className="truncate text-xs text-slate-400" data-testid="current-user-email">{user?.email ?? "admin@crm.co.id"}</div></div></div><div className="mb-3 inline-flex rounded-full bg-white/15 px-2 py-1 text-[10px] font-semibold text-amber-100 ring-1 ring-white/10" data-testid="current-user-role">{user?.role ?? "SUPER_ADMIN"}</div><Button variant="outline" className="w-full border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white" onClick={logout} data-testid="logout-button"><LogOut className="mr-2 size-4" />Logout</Button></div>
    </aside>
    {mobileOpen && <button className="fixed inset-0 z-40 bg-slate-950/60 lg:hidden" onClick={() => setMobileOpen(false)} data-testid="mobile-sidebar-overlay" aria-label="Close navigation" />}
    <div className="lg:pl-64"><header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur-md sm:px-6"><button className="rounded-md p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={() => setMobileOpen(true)} data-testid="mobile-menu-button"><Menu className="size-5" /></button><div className="hidden items-center gap-2 text-sm text-slate-500 lg:flex"><PanelLeft className="size-4" />Operasional Sales</div><div className="ml-auto flex items-center gap-3"><div className="hidden text-right sm:block"><div className="text-sm font-semibold" data-testid="header-user-name">{user?.name ?? "Admin"}</div><div className="text-xs text-slate-500">{user?.role ?? "SUPER_ADMIN"}</div></div><div className="rounded-full bg-slate-100 p-2 text-slate-600" data-testid="notification-indicator"><Bell className="size-4" /></div></div></header><main className="p-4 sm:p-6 lg:p-8">{children}</main></div>
    <AICopilot />
  </div>;
}
