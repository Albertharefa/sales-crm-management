import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import { useCurrentUser } from "@/components/AppShell";

type SalesTarget = { id: string; sales_id: string; sales_name: string; owner_role?: string; sales_status?: string; year: number; target: number };
type TargetSummary = { year: number; personal_target: number; personal_achievement: number; personal_achievement_pct: number };

const money = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(Number(value || 0));

export default function SalesTargetsSalesView() {
  const { data: user } = useCurrentUser();
  const year = new Date().getFullYear();
  const targets = useQuery({ queryKey: ["sales-targets", "self"], queryFn: () => apiGet<SalesTarget[]>("/sales-targets") });
  const summary = useQuery({ queryKey: ["sales-target-summary", "self", year], queryFn: () => apiGet<TargetSummary>(`/sales-targets/summary?year=${year}`), staleTime: 30_000 });
  const target = (targets.data ?? []).find(item => item.sales_id === user?.id && item.year === year) ?? null;
  const pct = summary.data?.personal_achievement_pct ?? 0;
  const tone = pct >= 100 ? "border-emerald-200 bg-emerald-50 text-emerald-700" : pct >= 50 ? "border-blue-200 bg-blue-50 text-blue-700" : pct >= 25 ? "border-amber-200 bg-amber-50 text-amber-700" : "border-rose-200 bg-rose-50 text-rose-700";

  return <div data-testid="sales-targets-self-page">
    <PageHeader title="Target Sales" description="Target personal dan achievement Anda. Target tim hanya dapat dilihat oleh Sales Manager." onRefresh={() => window.location.reload()} />
    <div className="mb-5 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Sales</div>
      <div className="mt-1 text-xl font-semibold text-slate-900">{user?.name ?? "-"}</div>
      <div className="mt-1 text-xs text-slate-500">Tahun {year}</div>
    </div>
    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Target Personal</div><div className="mt-3 font-mono text-2xl font-semibold text-slate-900">{money(summary.data?.personal_target ?? target?.target ?? 0)}</div></div>
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Won / Achievement</div><div className="mt-3 font-mono text-2xl font-semibold text-slate-900">{money(summary.data?.personal_achievement ?? 0)}</div></div>
      <div className={`rounded-lg border p-5 shadow-sm ${tone}`}><div className="text-xs font-semibold uppercase tracking-wider opacity-80">Achievement</div><div className="mt-3 font-mono text-2xl font-semibold">{pct.toFixed(2)}%</div></div>
    </div>
    {targets.isLoading || summary.isLoading ? <div className="mt-5 rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-500">Memuat target...</div> : null}
    {!targets.isLoading && !summary.isLoading && !target && !(summary.data?.personal_target) ? <div className="mt-5 rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">Belum ada target penjualan untuk tahun {year}.</div> : null}
  </div>;
}
