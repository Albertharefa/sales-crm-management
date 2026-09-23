import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { useCurrentUser } from "@/components/AppShell";

type SalesTarget = { id: string; sales_id: string; sales_name: string; owner_role?: string; sales_status?: string; year: number; target: number };
type TargetSummary = { year: number; personal_target: number; personal_achievement: number; personal_achievement_pct: number; team_target?: number; team_achievement?: number; team_achievement_pct?: number };
type DashboardMetrics = {
  open_pipeline: number;
  weighted_pipeline: number;
  won_value: number;
  lost_value?: number;
  win_rate?: number;
  total_po: number;
  po_value: number;
  open_orders?: number;
  completed_orders?: number;
  overdue_orders?: number;
  activities: number;
  overdue_activities: number;
};

type DetailRow = {
  id: string;
  sales: string;
  target: number;
  won: number;
  achievement: number;
  gap: number;
  open_pipeline: number;
  weighted: number;
  coverage: number;
  win_rate: number;
  po: number;
  po_value: number;
  activities: number;
  overdue_activities: number;
  open_orders: number;
  completed_orders: number;
  overdue: number;
};

const money = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", notation: "compact", maximumFractionDigits: 1 }).format(Number(value || 0));
const percent = (value: number) => `${Number(value || 0).toFixed(1)}%`;
const multiple = (value: number) => `${Number(value || 0).toFixed(1)}x`;

export default function SalesTargetsSalesView() {
  const { data: user } = useCurrentUser();
  const year = new Date().getFullYear();
  const targets = useQuery({ queryKey: ["sales-targets", "self"], queryFn: () => apiGet<SalesTarget[]>("/sales-targets") });
  const summary = useQuery({ queryKey: ["sales-target-summary", "self", year], queryFn: () => apiGet<TargetSummary>(`/sales-targets/summary?year=${year}`), staleTime: 30_000 });
  const dashboard = useQuery({ queryKey: ["sales-target-self-dashboard", year], queryFn: () => apiGet<DashboardMetrics>("/dashboard"), staleTime: 30_000 });

  const target = (targets.data ?? []).find(item => item.sales_id === user?.id && item.year === year) ?? null;
  const targetValue = summary.data?.personal_target ?? target?.target ?? 0;
  const achievementValue = dashboard.data?.po_value ?? summary.data?.personal_achievement ?? 0;
  const pct = targetValue > 0 ? achievementValue / targetValue * 100 : 0;
  const tone = pct >= 100 ? "border-emerald-200 bg-emerald-50 text-emerald-700" : pct >= 50 ? "border-blue-200 bg-blue-50 text-blue-700" : pct >= 25 ? "border-amber-200 bg-amber-50 text-amber-700" : "border-rose-200 bg-rose-50 text-rose-700";
  const gap = Math.max(0, targetValue - achievementValue);
  const winRate = dashboard.data?.win_rate ?? 0;
  const coverage = gap > 0 ? (dashboard.data?.open_pipeline ?? 0) / gap : 0;
  const detailRow: DetailRow = {
    id: user?.id ?? "self",
    sales: user?.name ?? "-",
    target: targetValue,
    won: dashboard.data?.won_value ?? 0,
    achievement: pct,
    gap,
    open_pipeline: dashboard.data?.open_pipeline ?? 0,
    weighted: dashboard.data?.weighted_pipeline ?? 0,
    coverage,
    win_rate: winRate,
    po: dashboard.data?.total_po ?? 0,
    po_value: dashboard.data?.po_value ?? 0,
    activities: dashboard.data?.activities ?? 0,
    overdue_activities: dashboard.data?.overdue_activities ?? 0,
    open_orders: dashboard.data?.open_orders ?? 0,
    completed_orders: dashboard.data?.completed_orders ?? 0,
    overdue: dashboard.data?.overdue_orders ?? 0,
  };

  return <div data-testid="sales-targets-self-page">
    <PageHeader title="Target Sales" description="Target personal dan achievement Anda. Target tim hanya dapat dilihat oleh Sales Manager." onRefresh={() => window.location.reload()} />
    <div className="mb-5 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Sales</div>
      <div className="mt-1 text-xl font-semibold text-slate-900">{user?.name ?? "-"}</div>
      <div className="mt-1 text-xs text-slate-500">Tahun {year}</div>
    </div>
    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Target Personal</div><div className="mt-3 font-mono text-2xl font-semibold text-slate-900">{money(targetValue)}</div></div>
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"><div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Won / Achievement</div><div className="mt-3 font-mono text-2xl font-semibold text-slate-900">{money(achievementValue)}</div></div>
      <div className={`rounded-lg border p-5 shadow-sm ${tone}`}><div className="text-xs font-semibold uppercase tracking-wider opacity-80">Achievement</div><div className="mt-3 font-mono text-2xl font-semibold">{pct.toFixed(2)}%</div></div>
    </div>

    <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="sales-target-self-performance">
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-blue-600">PERFORMANCE DETAIL</div>
          <h2 className="mt-1 font-heading text-lg font-semibold text-slate-900">Pencapaian Sales</h2>
          <p className="text-xs text-slate-500">Detail KPI personal Anda untuk {year}. Data mengikuti scope user login dan tidak menampilkan sales lain.</p>
        </div>
        <Badge variant="outline">Personal</Badge>
      </div>
      <DataTable
        testId="sales-target-self-performance-table"
        items={dashboard.isLoading || summary.isLoading ? [] : [detailRow]}
        loading={dashboard.isLoading || summary.isLoading}
        total={1}
        page={1}
        pageSize={1}
        onPage={() => undefined}
        onPageSize={() => undefined}
        columns={[
          { key: "sales", label: "Sales", render: i => <span className="font-medium">{i.sales}</span> },
          { key: "target", label: "Target", render: i => money(i.target) },
          { key: "won", label: "Won", render: i => money(i.won) },
          { key: "achievement", label: "Achievement", render: i => <span className={i.achievement >= 100 ? "font-semibold text-emerald-600" : i.achievement >= 50 ? "font-semibold text-blue-600" : i.achievement >= 25 ? "font-semibold text-amber-600" : "font-medium text-rose-600"}>{percent(i.achievement)}</span> },
          { key: "gap", label: "Gap", render: i => money(i.gap) },
          { key: "open_pipeline", label: "Open Pipeline", render: i => money(i.open_pipeline) },
          { key: "weighted", label: "Weighted", render: i => money(i.weighted) },
          { key: "coverage", label: "Coverage", render: i => multiple(i.coverage) },
          { key: "win_rate", label: "Win Rate", render: i => percent(i.win_rate) },
          { key: "po", label: "PO", render: i => i.po },
          { key: "po_value", label: "PO Value", render: i => money(i.po_value) },
          { key: "activities", label: "Aktivitas", render: i => i.activities },
          { key: "overdue_activities", label: "Overdue Activity", render: i => i.overdue_activities },
          { key: "open_orders", label: "Open Orders", render: i => i.open_orders },
          { key: "completed_orders", label: "Completed", render: i => i.completed_orders },
          { key: "overdue", label: "Overdue PO", render: i => i.overdue },
        ]}
      />
    </section>

    {targets.isLoading || summary.isLoading || dashboard.isLoading ? <div className="mt-5 rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-500">Memuat target dan pencapaian...</div> : null}
    {!targets.isLoading && !summary.isLoading && !dashboard.isLoading && !target && !(summary.data?.personal_target) ? <div className="mt-5 rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">Belum ada target penjualan untuk tahun {year}.</div> : null}
  </div>;
}
