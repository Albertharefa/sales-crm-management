import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, BarChart3, CheckCircle2, CircleDollarSign, Contact, FileText, Flag, PackageCheck, ShoppingCart, Target, TrendingUp, UserPlus, Users, WalletCards } from "lucide-react";

import { ApiError, apiGet } from "@/lib/api";
import type { DashboardMetrics } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const money = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(value);
const compactMoney = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", notation: "compact", maximumFractionDigits: 1 }).format(value);

export default function Home() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: () => apiGet<DashboardMetrics>("/dashboard"), retry: 1, staleTime: 30_000 });
  const data = query.isError ? undefined : query.data;
  const cards = data ? [
    { label: "TOTAL CUSTOMERS", value: data.total_customer.toLocaleString("id-ID"), note: "Customer dalam database", icon: Users },
    { label: "TOTAL CONTACTS", value: data.total_contacts.toLocaleString("id-ID"), note: "Kontak customer", icon: Contact },
    { label: "TOTAL LEADS", value: data.total_leads.toLocaleString("id-ID"), note: "Lead tercatat", icon: UserPlus },
    { label: "OPPORTUNITIES", value: data.total_opportunities.toLocaleString("id-ID"), note: "Total opportunity", icon: BarChart3 },
    { label: "OPEN PIPELINE", value: money(data.open_pipeline), note: "Nilai deal berjalan", icon: TrendingUp },
    { label: "WEIGHTED PIPELINE", value: money(data.weighted_pipeline), note: "Value × probability", icon: WalletCards },
    { label: "WON VALUE", value: money(data.won_value), note: "Opportunity won", icon: CheckCircle2 },
    { label: "LOST VALUE", value: money(data.lost_value), note: "Opportunity lost", icon: AlertTriangle },
    { label: "WIN RATE", value: `${data.win_rate.toFixed(1)}%`, note: "Won ÷ closed deals", icon: Flag },
    { label: "ACTIVE QUOTATIONS", value: data.active_quotations.toLocaleString("id-ID"), note: `${data.total_quotation} quotation total`, icon: FileText },
    { label: "QUOTATION VALUE", value: money(data.quotation_value), note: "Nilai quotation aktif", icon: CircleDollarSign },
    { label: "PURCHASE ORDERS", value: data.total_po.toLocaleString("id-ID"), note: money(data.po_value), icon: ShoppingCart },
    { label: "ORDER MONITORING", value: data.open_orders.toLocaleString("id-ID"), note: `${data.overdue_orders} overdue · ${data.completed_orders} selesai`, icon: PackageCheck },
    { label: "ACTIVITIES", value: data.activities.toLocaleString("id-ID"), note: `${data.overdue_activities} follow-up overdue`, icon: Activity },
    { label: "SALES TARGET", value: money(data.sales_target), note: "Target tahun berjalan", icon: Target },
    { label: "TARGET ACHIEVEMENT", value: `${data.target_achievement.toFixed(1)}%`, note: "PO value ÷ target", icon: TrendingUp },
  ] : [];
  const stageMax = Math.max(...(data?.pipeline_by_stage.map(item => item.value) ?? [1]), 1);
  const salespersonMax = Math.max(...(data?.pipeline_by_salesperson.map(item => item.value) ?? [1]), 1);
  const monthlyMax = Math.max(...(data?.monthly_sales_performance.flatMap(item => [item.actual, item.target]) ?? [1]), 1);
  const errorDetail = query.error instanceof ApiError && query.error.status === 401 ? "Sesi Anda telah berakhir. Silakan masuk kembali." : "Dashboard gagal dihitung dari MongoDB. Coba refresh; jika berlanjut, hubungi administrator.";

  return <div data-testid="dashboard-page">
    <PageHeader title="Dashboard" description="Ringkasan performa sales — dihitung penuh oleh MongoDB aggregation pipeline" onRefresh={() => void query.refetch()} />
    {query.isError && <div className="mb-6 flex flex-col justify-between gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 sm:flex-row sm:items-center" role="alert" data-testid="dashboard-error"><span>{errorDetail}</span><Button variant="outline" size="sm" onClick={() => void query.refetch()} data-testid="dashboard-error-retry">Coba lagi</Button></div>}
    {query.isLoading && <div className="grid grid-cols-2 gap-4 md:grid-cols-4" data-testid="dashboard-loading">{Array.from({ length: 8 }).map((_, index) => <div key={index} className="h-36 animate-pulse rounded-xl border border-slate-200 bg-white" />)}</div>}
    {data && <>
      <div className="mb-3 flex items-center justify-between"><Badge variant="outline" data-testid="dashboard-source-badge">Live MongoDB aggregation</Badge><span className="text-xs text-slate-400" data-testid="dashboard-generated-at">Diperbarui {new Date(data.generated_at).toLocaleString("id-ID")}</span></div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">{cards.map(({ label, value, note, icon: Icon }) => <Card key={label} className="h-full border-slate-200 shadow-sm" data-testid={`dashboard-kpi-${label.toLowerCase().replaceAll(" ", "-")}`}><CardContent className="p-5"><div className="flex items-start justify-between"><div className="text-[10px] font-semibold tracking-wider text-slate-500">{label}</div><Icon className="size-4 text-slate-400" /></div><div className="mt-4 break-words font-heading text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">{value}</div><div className="mt-2 text-xs text-slate-500">{note}</div></CardContent></Card>)}</div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card className="border-slate-200 shadow-sm" data-testid="dashboard-pipeline-stage-card"><CardContent className="p-6"><div className="mb-5"><h2 className="font-heading text-xl font-semibold">Pipeline per Stage</h2><p className="mt-1 text-sm text-slate-500">Nilai dan jumlah deal per tahap</p></div><div className="space-y-4">{data.pipeline_by_stage.map(stage => <div key={stage.name} data-testid={`pipeline-stage-${stage.name.toLowerCase().replaceAll(" ", "-")}`}><div className="mb-1.5 flex justify-between text-sm"><span className="font-medium">{stage.name} <span className="text-slate-400">({stage.count})</span></span><span className="font-mono text-xs text-slate-500">{compactMoney(stage.value)}</span></div><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-blue-600 transition-[width] duration-300" style={{ width: `${Math.max(stage.value ? 4 : 0, stage.value / stageMax * 100)}%` }} /></div></div>)}</div></CardContent></Card>
        <Card className="border-slate-200 shadow-sm" data-testid="dashboard-pipeline-salesperson-card"><CardContent className="p-6"><div className="mb-5"><h2 className="font-heading text-xl font-semibold">Pipeline per Salesperson</h2><p className="mt-1 text-sm text-slate-500">Open pipeline berdasarkan pemilik record</p></div><div className="space-y-4">{data.pipeline_by_salesperson.map(item => <div key={item.name} data-testid={`pipeline-sales-${item.name.toLowerCase().replaceAll(" ", "-")}`}><div className="mb-1.5 flex justify-between text-sm"><span className="font-medium">{item.name} <span className="text-slate-400">({item.count})</span></span><span className="font-mono text-xs text-slate-500">{compactMoney(item.value)}</span></div><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-sky-500" style={{ width: `${Math.max(item.value ? 4 : 0, item.value / salespersonMax * 100)}%` }} /></div></div>)}</div></CardContent></Card>
      </div>

      <Card className="mt-6 border-slate-200 shadow-sm" data-testid="dashboard-monthly-performance"><CardContent className="p-6"><div className="mb-6 flex flex-col justify-between gap-2 sm:flex-row sm:items-end"><div><h2 className="font-heading text-xl font-semibold">Monthly Sales Performance</h2><p className="mt-1 text-sm text-slate-500">Purchase order aktual dibanding target bulanan</p></div><div className="flex gap-4 text-xs"><span className="flex items-center gap-2"><i className="size-2 rounded-full bg-blue-600" />Actual</span><span className="flex items-center gap-2"><i className="size-2 rounded-full bg-slate-300" />Target</span></div></div><div className="grid min-w-[720px] grid-cols-12 gap-3 overflow-hidden">{data.monthly_sales_performance.map(item => <div key={item.month} className="flex flex-col items-center" data-testid={`monthly-sales-${item.month}`}><div className="flex h-40 w-full items-end justify-center gap-1"><div className="w-3 rounded-t bg-blue-600" style={{ height: `${Math.max(item.actual ? 3 : 0, item.actual / monthlyMax * 100)}%` }} title={`Actual ${money(item.actual)}`} /><div className="w-3 rounded-t bg-slate-300" style={{ height: `${Math.max(item.target ? 3 : 0, item.target / monthlyMax * 100)}%` }} title={`Target ${money(item.target)}`} /></div><span className="mt-2 text-[10px] font-medium text-slate-500">{item.label}</span></div>)}</div></CardContent></Card>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card className="border-slate-200 shadow-sm" data-testid="dashboard-recent-activities"><CardContent className="p-6"><div className="mb-4"><h2 className="font-heading text-xl font-semibold">Recent Activities</h2><p className="mt-1 text-sm text-slate-500">Aktivitas sales terbaru dari database</p></div><div className="divide-y divide-slate-100">{data.recent_activities.map(item => <div key={item.id} className="flex items-start justify-between gap-4 py-3" data-testid={`recent-activity-${item.id}`}><div><div className="text-sm font-medium">{item.subject}</div><div className="mt-1 text-xs text-slate-500">{item.customer_name ?? "Tanpa customer"} · {item.sales_name ?? "Unassigned"}</div></div><div className="text-right"><Badge variant="outline">{item.activity_type}</Badge><div className="mt-1 text-[10px] text-slate-400">{item.date ?? "—"}</div></div></div>)}</div></CardContent></Card>
        <Card className="border-slate-200 shadow-sm" data-testid="dashboard-deal-risks"><CardContent className="p-6"><div className="mb-4"><h2 className="font-heading text-xl font-semibold">Deal Risk / Stalled</h2><p className="mt-1 text-sm text-slate-500">Opportunity yang membutuhkan tindakan</p></div><div className="divide-y divide-slate-100">{data.deal_risks.length ? data.deal_risks.map(item => <div key={item.id} className="flex items-start justify-between gap-4 py-3" data-testid={`deal-risk-${item.id}`}><div><div className="text-sm font-medium">{item.name}</div><div className="mt-1 text-xs text-slate-500">{item.customer_name} · {item.stage}</div><div className="mt-1 text-xs font-medium text-amber-700">{item.reason}</div></div><div className="text-right font-mono text-xs">{compactMoney(item.value)}</div></div>) : <div className="py-8 text-center text-sm text-slate-400">Tidak ada deal berisiko</div>}</div></CardContent></Card>
      </div>
    </>}
  </div>;
}