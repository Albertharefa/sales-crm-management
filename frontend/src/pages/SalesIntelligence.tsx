import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BarChart3, Gauge, RefreshCw, Target, TrendingUp, Trophy } from "lucide-react";
import { apiGet } from "@/lib/api";
import type { DashboardMetrics } from "@/lib/types";
import { Button } from "@/components/ui/button";

const money = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(value);
const compact = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", notation: "compact", maximumFractionDigits: 1 }).format(value).replace("IDR", "Rp");
const percent = (value: number) => `${Math.max(0, value).toFixed(1)}%`;

function Metric({ label, value, note, icon: Icon, tone = "blue" }: { label: string; value: string; note: string; icon: typeof Target; tone?: "blue" | "green" | "amber" | "slate" }) {
  const tones = { blue: "bg-blue-50 text-blue-600", green: "bg-emerald-50 text-emerald-600", amber: "bg-amber-50 text-amber-600", slate: "bg-slate-100 text-slate-600" };
  return <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-[10px] font-bold tracking-[.14em] text-slate-500">{label}</span><div className={`rounded-xl p-2 ${tones[tone]}`}><Icon className="size-5" /></div></div><div className="mt-4 font-heading text-2xl font-bold text-slate-950">{value}</div><div className="mt-2 text-xs text-slate-500">{note}</div></div>;
}

function Empty({ text }: { text: string }) { return <div className="p-6 text-sm text-slate-500">{text}</div>; }

export default function SalesIntelligence() {
  const query = useQuery({ queryKey: ["sales-intelligence"], queryFn: () => apiGet<DashboardMetrics>("/dashboard"), staleTime: 30_000, refetchInterval: 300_000, retry: 1 });
  const data = query.data;
  if (query.isLoading) return <div className="space-y-5"><div className="h-28 animate-pulse rounded-xl bg-slate-200" /><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-36 animate-pulse rounded-xl bg-white border border-slate-200" />)}</div></div>;
  if (query.isError || !data) return <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800"><div className="font-semibold">Sales Intelligence gagal mengambil data Dashboard.</div><Button variant="outline" size="sm" className="mt-3" onClick={() => query.refetch()}><RefreshCw className="mr-2 size-4" />Coba lagi</Button></div>;

  const target = Number(data.sales_target) || 0;
  const won = Number(data.won_value) || 0;
  const open = Number(data.open_pipeline) || 0;
  const weighted = Number(data.weighted_pipeline) || 0;
  const forecast = won + weighted;
  const coverage = target > 0 ? open / target : 0;
  const achievement = target > 0 ? (won / target) * 100 : Number(data.target_achievement) || 0;
  const winRate = Number(data.win_rate) || 0;
  const gap = Math.max(0, target - forecast);
  const forecastAchievement = target > 0 ? (forecast / target) * 100 : 0;
  const riskCount = data.deal_risks.length;
  const maxStage = Math.max(...data.pipeline_by_stage.map(row => Number(row.value) || 0), 1);
  const maxSales = Math.max(...data.pipeline_by_salesperson.map(row => Number(row.value) || 0), 1);

  return <div className="space-y-6" data-testid="sales-intelligence-page">
    <div className="rounded-2xl bg-gradient-to-r from-[#071126] via-[#101e42] to-[#172a58] p-7 text-white shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="text-xs font-semibold uppercase tracking-[.18em] text-blue-300">SALES MANAGEMENT INTELLIGENCE</div><h1 className="mt-2 font-heading text-3xl font-bold tracking-tight">Sales Intelligence</h1><p className="mt-2 max-w-3xl text-sm text-slate-300">Ringkasan target, forecast, pipeline coverage, win rate, dan risiko opportunity berdasarkan data CRM yang sedang aktif.</p><div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-slate-300"><span className="rounded-full bg-white/10 px-2.5 py-1">Auto-refresh setiap 5 menit</span>{query.isFetching ? <span className="flex items-center gap-1 rounded-full bg-white/10 px-2.5 py-1"><RefreshCw className="size-3 animate-spin" />Memperbarui data...</span> : data.generated_at ? <span className="rounded-full bg-white/10 px-2.5 py-1">Data: {new Date(data.generated_at).toLocaleString("id-ID")}</span> : null}</div></div><Button variant="secondary" size="sm" onClick={() => query.refetch()} disabled={query.isFetching} className="shrink-0 bg-white/10 text-white hover:bg-white/20"><RefreshCw className={`mr-2 size-4 ${query.isFetching ? "animate-spin" : ""}`} />Refresh</Button></div></div>

    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <Metric label="TARGET" value={compact(target)} note="Target dalam scope user" icon={Target} />
      <Metric label="ACHIEVEMENT" value={percent(achievement)} note={`${money(won)} won`} icon={Trophy} tone="green" />
      <Metric label="FORECAST" value={compact(forecast)} note={`${percent(forecastAchievement)} dari target`} icon={TrendingUp} tone="blue" />
      <Metric label="PIPELINE COVERAGE" value={`${coverage.toFixed(1)}x`} note={`${compact(open)} open pipeline`} icon={Gauge} tone="amber" />
      <Metric label="WIN RATE" value={percent(winRate)} note={`${data.total_opportunities} opportunities`} icon={Trophy} tone="slate" />
    </div>

    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="text-[10px] font-bold tracking-[.14em] text-slate-500">FORECAST GAP</div><div className="mt-2 text-xl font-bold text-slate-950">{compact(gap)}</div><div className="mt-1 text-xs text-slate-500">Remaining gap after weighted pipeline</div></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="text-[10px] font-bold tracking-[.14em] text-slate-500">OPEN OPPORTUNITIES</div><div className="mt-2 text-xl font-bold text-slate-950">{data.pipeline_by_stage.reduce((sum, row) => sum + Number(row.count || 0), 0)}</div><div className="mt-1 text-xs text-slate-500">Across current sales scope</div></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="text-[10px] font-bold tracking-[.14em] text-slate-500">RISK WATCHLIST</div><div className="mt-2 text-xl font-bold text-slate-950">{riskCount}</div><div className="mt-1 text-xs text-slate-500">Opportunities flagged for follow-up</div></div>
    </div>

    <div className="grid gap-5 xl:grid-cols-[1.2fr_1fr]">
      <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><div className="flex items-center gap-2"><BarChart3 className="size-5 text-blue-600" /><h2 className="font-heading text-lg font-semibold">Pipeline by Stage</h2></div><p className="text-xs text-slate-500">Value and opportunity count by current stage</p></div><div className="space-y-4 p-6">{data.pipeline_by_stage.length === 0 ? <Empty text="Belum ada pipeline." /> : data.pipeline_by_stage.map((row) => <div key={row.name}><div className="mb-1 flex items-center justify-between gap-4 text-sm"><span className="font-medium text-slate-800">{row.name}</span><span className="font-semibold text-slate-900">{compact(Number(row.value) || 0)} <span className="font-normal text-slate-400">· {row.count}</span></span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-600" style={{ width: `${Math.min(100, ((Number(row.value) || 0) / maxStage) * 100)}%` }} /></div></div>)}</div></section>
      <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><h2 className="font-heading text-lg font-semibold">Sales Performance</h2><p className="text-xs text-slate-500">Open pipeline per salesperson dalam scope Anda</p></div><div className="space-y-4 p-6">{data.pipeline_by_salesperson.length === 0 ? <Empty text="Belum ada open pipeline." /> : data.pipeline_by_salesperson.map((row) => <div key={row.name}><div className="mb-1 flex items-center justify-between gap-4"><div className="min-w-0"><div className="truncate text-sm font-semibold text-slate-900">{row.name}</div><div className="text-xs text-slate-500">{row.count} open opportunity</div></div><div className="text-right text-sm font-semibold text-slate-900">{compact(row.value)}</div></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-800" style={{ width: `${Math.min(100, ((Number(row.value) || 0) / maxSales) * 100)}%` }} /></div></div>)}</div></section>
    </div>

    <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
      <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><h2 className="font-heading text-lg font-semibold">Management Forecast</h2><p className="text-xs text-slate-500">Forecast sederhana untuk review mingguan sales management</p></div><div className="grid gap-4 p-6 md:grid-cols-3"><div className="rounded-xl bg-slate-50 p-5"><div className="text-xs text-slate-500">Won</div><div className="mt-2 text-xl font-bold">{compact(won)}</div></div><div className="rounded-xl bg-slate-50 p-5"><div className="text-xs text-slate-500">Weighted Pipeline</div><div className="mt-2 text-xl font-bold">{compact(weighted)}</div></div><div className="rounded-xl bg-blue-50 p-5"><div className="text-xs text-blue-700">Forecast</div><div className="mt-2 text-xl font-bold text-blue-950">{compact(forecast)}</div></div></div></section>
      <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><h2 className="font-heading text-lg font-semibold">Recent Activities</h2><p className="text-xs text-slate-500">Latest sales execution signals</p></div><div className="divide-y divide-slate-100">{data.recent_activities.length === 0 ? <Empty text="Belum ada aktivitas." /> : data.recent_activities.slice(0, 6).map((item) => <div key={item.id} className="px-6 py-3"><div className="truncate text-sm font-medium text-slate-900">{item.subject}</div><div className="mt-1 truncate text-xs text-slate-500">{item.customer_name || "No customer"} · {item.sales_name || "Unassigned"}</div></div>)}</div></section>
    </div>

    <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><div className="flex items-center gap-2"><AlertTriangle className="size-5 text-amber-500" /><h2 className="font-heading text-lg font-semibold">Opportunity Risks</h2></div><p className="text-xs text-slate-500">Prioritas follow-up berdasarkan risk engine CRM</p></div><div className="divide-y divide-slate-100">{data.deal_risks.length === 0 ? <Empty text="Tidak ada opportunity berisiko." /> : data.deal_risks.slice(0, 8).map((risk) => <div key={risk.id} className="flex items-start gap-3 px-6 py-4"><AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" /><div className="min-w-0 flex-1"><div className="truncate text-sm font-semibold text-slate-900">{risk.name}</div><div className="mt-1 text-xs text-slate-500">{risk.customer_name} · {risk.sales_name || "Unassigned"} · {risk.stage}</div><div className="mt-1 text-xs font-medium text-amber-700">{risk.reason}</div></div><div className="whitespace-nowrap text-xs font-semibold text-slate-700">{compact(risk.value)}</div></div>)}</div></section>

    <div className="text-right text-[11px] text-slate-400">Data generated: {data.generated_at ? new Date(data.generated_at).toLocaleString("id-ID") : "-"}</div>
  </div>;
}
