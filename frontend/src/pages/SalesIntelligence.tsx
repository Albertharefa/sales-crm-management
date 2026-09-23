import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Gauge, Target, TrendingUp, Trophy } from "lucide-react";
import { apiGet } from "@/lib/api";
import type { DashboardMetrics } from "@/lib/types";

const money = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(value);
const compact = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", notation: "compact", maximumFractionDigits: 1 }).format(value).replace("IDR", "Rp");

function Metric({ label, value, note, icon: Icon }: { label: string; value: string; note: string; icon: typeof Target }) {
  return <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-[10px] font-bold tracking-[.14em] text-slate-500">{label}</span><div className="rounded-xl bg-blue-50 p-2 text-blue-600"><Icon className="size-5" /></div></div><div className="mt-4 font-heading text-2xl font-bold text-slate-950">{value}</div><div className="mt-2 text-xs text-slate-500">{note}</div></div>;
}

export default function SalesIntelligence() {
  const query = useQuery({ queryKey: ["sales-intelligence"], queryFn: () => apiGet<DashboardMetrics>("/dashboard"), staleTime: 30_000, retry: 1 });
  const data = query.data;
  if (query.isLoading) return <div className="space-y-5"><div className="h-24 animate-pulse rounded-xl bg-slate-200" /><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-36 animate-pulse rounded-xl bg-white border border-slate-200" />)}</div></div>;
  if (query.isError || !data) return <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">Sales Intelligence gagal mengambil data Dashboard. Silakan refresh.</div>;

  const target = Number(data.sales_target) || 0;
  const won = Number(data.won_value) || 0;
  const open = Number(data.open_pipeline) || 0;
  const weighted = Number(data.weighted_pipeline) || 0;
  const forecast = won + weighted;
  const coverage = target > 0 ? open / target : 0;
  const achievement = target > 0 ? (won / target) * 100 : Number(data.target_achievement) || 0;
  const winRate = Number(data.win_rate) || 0;

  return <div className="space-y-6" data-testid="sales-intelligence-page">
    <div className="rounded-2xl bg-gradient-to-r from-[#071126] via-[#101e42] to-[#172a58] p-7 text-white shadow-sm"><div className="text-xs font-semibold uppercase tracking-[.18em] text-blue-300">SALES MANAGEMENT INTELLIGENCE</div><h1 className="mt-2 font-heading text-3xl font-bold tracking-tight">Sales Intelligence</h1><p className="mt-2 max-w-3xl text-sm text-slate-300">Ringkasan target, forecast, pipeline coverage, win rate, dan risiko opportunity berdasarkan data CRM yang sedang aktif.</p></div>

    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <Metric label="TARGET" value={compact(target)} note="Target dalam scope user" icon={Target} />
      <Metric label="ACHIEVEMENT" value={`${achievement.toFixed(1)}%`} note={`${money(won)} won`} icon={Trophy} />
      <Metric label="FORECAST" value={compact(forecast)} note="Won + weighted pipeline" icon={TrendingUp} />
      <Metric label="PIPELINE COVERAGE" value={`${coverage.toFixed(1)}x`} note={`${compact(open)} open pipeline`} icon={Gauge} />
      <Metric label="WIN RATE" value={`${winRate.toFixed(1)}%`} note={`${data.total_opportunities} opportunities`} icon={Trophy} />
    </div>

    <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
      <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><h2 className="font-heading text-lg font-semibold">Sales Performance</h2><p className="text-xs text-slate-500">Open pipeline per salesperson dalam scope Anda</p></div><div className="divide-y divide-slate-100">{data.pipeline_by_salesperson.length === 0 ? <div className="p-6 text-sm text-slate-500">Belum ada open pipeline.</div> : data.pipeline_by_salesperson.map((row) => <div key={row.name} className="flex items-center justify-between gap-4 px-6 py-4"><div className="min-w-0"><div className="truncate text-sm font-semibold text-slate-900">{row.name}</div><div className="text-xs text-slate-500">{row.count} open opportunity</div></div><div className="text-right font-semibold text-slate-900">{compact(row.value)}</div></div>)}</div></section>
      <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><h2 className="font-heading text-lg font-semibold">Opportunity Risks</h2><p className="text-xs text-slate-500">Prioritas follow-up berdasarkan risk engine CRM</p></div><div className="divide-y divide-slate-100">{data.deal_risks.length === 0 ? <div className="p-6 text-sm text-slate-500">Tidak ada opportunity berisiko.</div> : data.deal_risks.slice(0, 8).map((risk) => <div key={risk.id} className="px-6 py-4"><div className="flex items-start gap-3"><AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" /><div className="min-w-0"><div className="truncate text-sm font-semibold text-slate-900">{risk.name}</div><div className="mt-1 text-xs text-slate-500">{risk.customer_name} · {risk.sales_name || "Unassigned"}</div><div className="mt-1 text-xs font-medium text-amber-700">{risk.reason}</div></div><div className="ml-auto whitespace-nowrap text-xs font-semibold text-slate-700">{compact(risk.value)}</div></div></div>)}</div></section>
    </div>

    <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><h2 className="font-heading text-lg font-semibold">Management Forecast</h2><p className="text-xs text-slate-500">Forecast sederhana untuk membantu review mingguan sales management</p></div><div className="grid gap-4 p-6 md:grid-cols-3"><div className="rounded-xl bg-slate-50 p-5"><div className="text-xs text-slate-500">Won</div><div className="mt-2 text-xl font-bold">{compact(won)}</div></div><div className="rounded-xl bg-slate-50 p-5"><div className="text-xs text-slate-500">Weighted Pipeline</div><div className="mt-2 text-xl font-bold">{compact(weighted)}</div></div><div className="rounded-xl bg-blue-50 p-5"><div className="text-xs text-blue-700">Forecast</div><div className="mt-2 text-xl font-bold text-blue-950">{compact(forecast)}</div></div></div></section>
  </div>;
}
