import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { SalesTeamMetric } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";

const money = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", notation: "compact", maximumFractionDigits: 1 }).format(value);
const percent = (value: number) => `${Number(value || 0).toFixed(1)}%`;
const multiple = (value: number) => `${Number(value || 0).toFixed(1)}x`;
type TeamRow = SalesTeamMetric & { id: string };

export default function SalesTeam() {
  const query = useQuery({ queryKey: ["sales-team"], queryFn: () => apiGet<SalesTeamMetric[]>("/sales-team") });
  const rows: TeamRow[] = (query.data ?? []).map((item, index) => ({ ...item, id: `${index}-${item.sales}` }));
  const totals = rows.reduce((sum, item) => ({
    target: sum.target + item.target,
    won: sum.won + item.won,
    open: sum.open + item.open_pipeline,
    weighted: sum.weighted + item.weighted,
    po: sum.po + item.po,
    poValue: sum.poValue + item.po_value,
    activities: sum.activities + item.activities,
    overdueActivities: sum.overdueActivities + item.overdue_activities,
    indent: sum.indent + item.indent,
    overdue: sum.overdue + item.overdue,
  }), { target: 0, won: 0, open: 0, weighted: 0, po: 0, poValue: 0, activities: 0, overdueActivities: 0, indent: 0, overdue: 0 });
  const totalGap = Math.max(0, totals.target - totals.won);
  const totalAchievement = totals.target ? totals.won / totals.target * 100 : 0;
  const totalCoverage = totalGap ? totals.open / totalGap : 0;
  const totalWonCount = rows.reduce((sum, item) => sum + item.won_count, 0);
  const totalLostCount = rows.reduce((sum, item) => sum + item.lost_count, 0);
  const totalWinRate = totalWonCount + totalLostCount ? totalWonCount / (totalWonCount + totalLostCount) * 100 : 0;

  return (
    <div data-testid="sales-team-page">
      <PageHeader title="Sales Team & KPI" description="Performance sales berdasarkan target, pipeline, closing, aktivitas, dan purchase order" onRefresh={() => window.location.reload()} onExport={() => window.open("/api/v1/exports/sales-team", "_blank")} />
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-8">
        {[
          ["Target", money(totals.target)],
          ["Won", money(totals.won)],
          ["Achievement", percent(totalAchievement)],
          ["Gap", money(totalGap)],
          ["Open Pipeline", money(totals.open)],
          ["Coverage", multiple(totalCoverage)],
          ["Win Rate", percent(totalWinRate)],
          ["PO Value", money(totals.poValue)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</div>
            <div className="mt-2 font-mono text-lg font-semibold text-slate-900">{value}</div>
          </div>
        ))}
      </div>
      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="font-heading text-sm font-semibold text-slate-900">Team Activity & Order Health</h2>
            <p className="text-xs text-slate-500">Indikator tambahan untuk coaching dan follow-up management</p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <Badge variant="outline">Aktivitas {totals.activities}</Badge>
            <Badge variant={totals.overdueActivities > 0 ? "destructive" : "outline"}>Overdue Activity {totals.overdueActivities}</Badge>
            <Badge variant="outline">Indent {totals.indent}</Badge>
            <Badge variant={totals.overdue > 0 ? "destructive" : "outline"}>Overdue PO {totals.overdue}</Badge>
          </div>
        </div>
      </div>
      <DataTable testId="sales-team-table" items={rows} loading={query.isLoading} columns={[
        { key: "sales", label: "Sales", render: i => <span className="font-medium">{i.sales}</span> },
        { key: "role", label: "Peran", render: i => <Badge variant="outline">{i.role}</Badge> },
        { key: "manager", label: "Manager", render: i => i.manager },
        { key: "target", label: "Target", render: i => money(i.target) },
        { key: "won", label: "Won", render: i => money(i.won) },
        { key: "achievement", label: "Achievement", render: i => <span className={i.achievement >= 100 ? "font-semibold text-emerald-600" : i.achievement > 0 ? "font-medium" : "text-slate-400"}>{percent(i.achievement)}</span> },
        { key: "gap", label: "Gap", render: i => money(i.gap_to_target) },
        { key: "open", label: "Open Pipeline", render: i => money(i.open_pipeline) },
        { key: "weighted", label: "Weighted", render: i => money(i.weighted) },
        { key: "coverage", label: "Coverage", render: i => multiple(i.coverage) },
        { key: "winRate", label: "Win Rate", render: i => percent(i.win_rate) },
        { key: "po", label: "PO", render: i => i.po },
        { key: "value", label: "PO Value", render: i => money(i.po_value) },
        { key: "activities", label: "Aktivitas", render: i => i.activities },
        { key: "overdueActivities", label: "Overdue Activity", render: i => i.overdue_activities },
        { key: "indent", label: "Indent", render: i => i.indent },
        { key: "overdue", label: "Overdue PO", render: i => i.overdue },
      ]} />
    </div>
  );
}
