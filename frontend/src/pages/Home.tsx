import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  ClipboardList,
  FileText,
  Gauge,
  PackageCheck,
  ShoppingCart,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";

import { apiGet } from "@/lib/api";
import type { Customer, DashboardMetrics, Paginated } from "@/lib/types";
import { Button } from "@/components/ui/button";

const money = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);

const compactMoney = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    notation: "compact",
    maximumFractionDigits: 1,
  })
    .format(value)
    .replace("IDR", "Rp");

const stageColors: Record<string, string> = {
  Lead: "#64748b",
  Qualification: "#0ea5e9",
  Proposal: "#2563eb",
  Negotiation: "#7c3aed",
  Won: "#10b981",
  Lost: "#f43f5e",
};

const normalizeDashboardMetrics = (input: DashboardMetrics): DashboardMetrics => {
  const numeric = (value: unknown) => (typeof value === "number" && Number.isFinite(value) ? value : Number(value) || 0);
  const array = <T,>(value: unknown): T[] => (Array.isArray(value) ? value as T[] : []);

  return {
    ...input,
    total_customer: numeric(input.total_customer),
    total_contacts: numeric(input.total_contacts),
    total_leads: numeric(input.total_leads),
    total_opportunities: numeric(input.total_opportunities),
    open_pipeline: numeric(input.open_pipeline),
    weighted_pipeline: numeric(input.weighted_pipeline),
    won_value: numeric(input.won_value),
    lost_value: numeric(input.lost_value),
    win_rate: numeric(input.win_rate),
    total_quotation: numeric(input.total_quotation),
    active_quotations: numeric(input.active_quotations),
    quotation_value: numeric(input.quotation_value),
    total_po: numeric(input.total_po),
    po_value: numeric(input.po_value),
    open_orders: numeric(input.open_orders),
    completed_orders: numeric(input.completed_orders),
    overdue_orders: numeric(input.overdue_orders),
    activities: numeric(input.activities),
    overdue_activities: numeric(input.overdue_activities),
    sales_target: numeric(input.sales_target),
    target_achievement: numeric(input.target_achievement),
    pipeline_by_stage: array<DashboardMetrics["pipeline_by_stage"][number]>(input.pipeline_by_stage),
    pipeline_by_salesperson: array<DashboardMetrics["pipeline_by_salesperson"][number]>(input.pipeline_by_salesperson),
    monthly_sales_performance: array<DashboardMetrics["monthly_sales_performance"][number]>(input.monthly_sales_performance),
    recent_activities: array<DashboardMetrics["recent_activities"][number]>(input.recent_activities),
    deal_risks: array<DashboardMetrics["deal_risks"][number]>(input.deal_risks),
    generated_at: input.generated_at || new Date().toISOString(),
  };
};

function KpiCard({
  label,
  value,
  note,
  icon: Icon,
  tone = "slate",
}: {
  label: string;
  value: string;
  note?: string;
  icon: typeof Users;
  tone?: "slate" | "blue" | "green" | "red";
}) {
  const toneClass = {
    slate: "bg-slate-100 text-slate-500",
    blue: "bg-blue-50 text-blue-600",
    green: "bg-emerald-50 text-emerald-600",
    red: "bg-rose-50 text-rose-600",
  }[tone];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="text-[10px] font-semibold tracking-[0.14em] text-slate-500">{label}</div>
        <div className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${toneClass}`}>
          <Icon className="size-5" />
        </div>
      </div>
      <div className="mt-4 break-words font-heading text-[28px] font-bold leading-none tracking-tight text-slate-950">
        {value}
      </div>
      {note && <div className="mt-2 text-xs text-slate-500">{note}</div>}
    </div>
  );
}

export default function Home() {
  const [period, setPeriod] = useState("Semua periode");
  const [sales, setSales] = useState("Semua sales");
  const [stage, setStage] = useState("Semua stage");
  const [customer, setCustomer] = useState("Semua customer");

  const query = useQuery({
    queryKey: ["dashboard", "20260908"],
    queryFn: async () => normalizeDashboardMetrics(await apiGet<DashboardMetrics>("/dashboard?client_version=20260908")),
    retry: 1,
    staleTime: 30_000,
    refetchOnMount: "always",
  });

  const customersQuery = useQuery({
    queryKey: ["dashboard-customers"],
    queryFn: () => apiGet<Paginated<Customer>>("/customers?page=1&page_size=100"),
    retry: 1,
    staleTime: 60_000,
  });

  const data = query.isError ? undefined : query.data;

  const dummySales = [
    "Admin",
    "Ahmad Ihwal Fadilah",
    "Aripin",
    "Albert Wellkomputindo",
    "Fery",
    "Paulus",
  ];

  const salesOptions = useMemo(
    () => [
      "Semua sales",
      ...Array.from(
        new Set([
          ...dummySales,
          ...(data?.pipeline_by_salesperson.map((item) => item.name) ?? []),
        ]),
      ).filter(Boolean),
    ],
    [data],
  );

  const customerOptions = useMemo(
    () => [
      "Semua customer",
      ...(customersQuery.data?.items
        ?.map((item) => item.name || item.company_name || item.company || "")
        .filter(Boolean) ?? []),
    ],
    [customersQuery.data],
  );

  const stageRows = useMemo(
    () => data?.pipeline_by_stage.filter((item) => ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"].includes(item.name)) ?? [],
    [data],
  );

  const stageMix = useMemo(() => {
    const total = stageRows.reduce((sum, item) => sum + item.value, 0);
    return stageRows.map((item) => ({
      ...item,
      percentage: total ? (item.value / total) * 100 : 0,
    }));
  }, [stageRows]);

  const donutGradient = useMemo(() => {
    let cursor = 0;
    const stops = stageMix.map((item) => {
      const start = cursor;
      cursor += item.percentage;
      return `${stageColors[item.name] ?? "#94a3b8"} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`;
    });
    return `conic-gradient(${stops.join(", ")})`;
  }, [stageMix]);

  const stageMax = Math.max(...stageRows.map((item) => item.value), 1);
  const totalPipelineValue = stageRows.reduce((sum, item) => sum + item.value, 0);

  const errorDetail =
    axios.isAxiosError(query.error) && query.error.response?.status === 401
      ? "Sesi Anda telah berakhir. Silakan masuk kembali."
      : "Dashboard gagal dihitung dari database. Coba refresh.";

  if (query.isLoading) {
    return (
      <div className="space-y-6" data-testid="dashboard-page">
        <div className="h-20 animate-pulse rounded-xl bg-slate-200" />
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          {Array.from({ length: 11 }).map((_, index) => (
            <div key={index} className="h-36 animate-pulse rounded-xl border border-slate-200 bg-white" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-blue-600">CRM SALES MANAGEMENT</div>
          <h1 className="mt-1 font-heading text-3xl font-bold tracking-tight text-slate-950">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">Pantau performa sales, pipeline, quotation, dan order dalam satu tampilan.</p>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:min-w-[760px]">
          {[
            { value: period, set: setPeriod, options: ["Semua periode", "30 hari terakhir", "90 hari terakhir", "1 tahun terakhir"] },
            { value: sales, set: setSales, options: salesOptions },
            { value: stage, set: setStage, options: ["Semua stage", "Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"] },
            { value: customer, set: setCustomer, options: customerOptions },
          ].map((filter, index) => (
            <select
              key={index}
              value={filter.value}
              onChange={(event) => filter.set(event.target.value)}
              className="h-10 min-w-0 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              aria-label={["Periode", "Sales", "Stage", "Customer"][index]}
            >
              {filter.options.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          ))}
        </div>
      </div>

      {query.isError && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert" data-testid="dashboard-error">
          <span>{errorDetail}</span>
          <Button variant="outline" size="sm" onClick={() => window.location.reload()}>Refresh</Button>
        </div>
      )}

      {data && (
        <>
          <section className="overflow-hidden rounded-2xl bg-gradient-to-r from-[#071126] via-[#101e42] to-[#172a58] px-7 py-7 text-white shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">↗ SALES OVERVIEW</div>
            <h2 className="mt-3 font-heading text-3xl font-bold tracking-tight sm:text-4xl">Business performance at a glance</h2>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">Lihat peluang terbesar, nilai pipeline, dan kondisi order secara cepat dari dashboard CRM.</p>
          </section>

          <section>
            <div className="mb-3">
              <h2 className="font-heading text-lg font-semibold text-slate-900">Business Snapshot</h2>
              <p className="text-sm text-slate-500">Metrik utama penjualan</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <KpiCard label="TOTAL CUSTOMER" value={data.total_customer.toLocaleString("id-ID")} icon={Users} />
              <KpiCard label="OPEN PIPELINE" value={compactMoney(data.open_pipeline)} note="Deal yang masih berjalan" icon={TrendingUp} tone="blue" />
              <KpiCard label="WEIGHTED PIPELINE" value={compactMoney(data.weighted_pipeline)} note="Value × probability" icon={Gauge} />
              <KpiCard label="WON VALUE" value={compactMoney(data.won_value)} note={`${data.open_pipeline ? Math.round((data.won_value / Math.max(data.open_pipeline, 1)) * 100) : 0}% dari pipeline`} icon={CheckCircle2} tone="green" />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
              <KpiCard label="QUOTATION" value={data.total_quotation.toLocaleString("id-ID")} icon={FileText} />
              <KpiCard label="TOTAL PO" value={data.total_po.toLocaleString("id-ID")} icon={ShoppingCart} />
              <KpiCard label="PO VALUE" value={compactMoney(data.po_value)} icon={CircleDollarSign} tone="blue" />
              <KpiCard label="AKTIVITAS" value={data.activities.toLocaleString("id-ID")} icon={CalendarDays} />
              <KpiCard label="OPEN ORDERS" value={data.open_orders.toLocaleString("id-ID")} icon={PackageCheck} tone="blue" />
              <KpiCard label="COMPLETED" value={data.completed_orders.toLocaleString("id-ID")} icon={CheckCircle2} tone="green" />
              <KpiCard label="OVERDUE" value={data.overdue_orders.toLocaleString("id-ID")} note="Belum selesai" icon={AlertTriangle} tone="red" />
            </div>
          </section>

          <section className="grid gap-5 xl:grid-cols-[2fr_1fr]">
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Target className="size-5" /></div>
                  <div>
                    <h2 className="font-heading text-lg font-semibold">Sales Pipeline</h2>
                    <p className="text-xs text-slate-500">Visualisasi value berdasarkan stage</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">TOTAL VALUE</div>
                  <div className="font-mono text-lg font-semibold text-slate-900">{compactMoney(totalPipelineValue)}</div>
                </div>
              </div>
              <div className="p-6">
                <div className="grid h-[260px] grid-cols-6 items-end gap-4 border-b border-dashed border-slate-200">
                  {stageRows.map((item) => (
                    <div key={item.name} className="flex h-full flex-col items-center justify-end gap-2">
                      <div className="text-[11px] font-medium text-slate-500">{compactMoney(item.value)}</div>
                      <div
                        className="w-full max-w-20 rounded-t-lg transition-all"
                        style={{
                          height: `${Math.max(item.value ? (item.value / stageMax) * 185 : 2, item.value ? 8 : 2)}px`,
                          background: stageColors[item.name] ?? "#94a3b8",
                        }}
                        title={`${item.name}: ${money(item.value)}`}
                      />
                      <div className="text-center text-[11px] font-medium text-slate-500">{item.name}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-heading text-lg font-semibold">Stage Mix</h2>
                  <p className="text-xs text-slate-500">Komposisi pipeline</p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-[10px] font-semibold text-slate-500">LIVE</span>
              </div>

              <div className="mt-6 flex justify-center">
                <div className="relative flex size-48 items-center justify-center rounded-full" style={{ background: donutGradient }}>
                  <div className="flex size-28 flex-col items-center justify-center rounded-full bg-white">
                    <span className="font-heading text-2xl font-bold">{data.total_opportunities}</span>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">DEALS</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-x-6 gap-y-3">
                {stageMix.map((item) => (
                  <div key={item.name} className="flex items-center justify-between gap-2 text-xs">
                    <span className="flex items-center gap-2 text-slate-500">
                      <i className="size-2.5 rounded-full" style={{ background: stageColors[item.name] ?? "#94a3b8" }} />
                      {item.name}
                    </span>
                    <span className="font-semibold text-slate-600">{Math.round(item.percentage)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-5 xl:grid-cols-[2fr_1fr]">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6">
                <h2 className="font-heading text-lg font-semibold">Pipeline Detail</h2>
                <p className="text-sm text-slate-500">Ranking stage berdasarkan nilai opportunity</p>
              </div>
              <div className="space-y-4">
                {[...stageRows].sort((a, b) => b.value - a.value).map((item, index) => (
                  <div key={item.name}>
                    <div className="mb-2 flex items-center gap-3">
                      <span className="flex size-7 items-center justify-center rounded-lg bg-slate-100 text-xs font-semibold text-slate-500">{index + 1}</span>
                      <span className="text-sm font-medium text-slate-700">{item.name} <span className="text-xs text-slate-400">{item.count} deal</span></span>
                      <span className="ml-auto font-mono text-xs font-semibold text-slate-600">{compactMoney(item.value)} <span className="text-blue-600">{Math.round(totalPipelineValue ? item.value / totalPipelineValue * 100 : 0)}%</span></span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${totalPipelineValue ? (item.value / totalPipelineValue) * 100 : 0}%`,
                          background: stageColors[item.name] ?? "#64748b",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl bg-[#050a1c] p-7 text-white shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex size-11 items-center justify-center rounded-xl bg-white/10 text-blue-300"><TrendingUp className="size-5" /></div>
                <div>
                  <h2 className="font-heading text-lg font-semibold">Pipeline Summary</h2>
                  <p className="text-xs text-slate-400">Ringkasan performa saat ini</p>
                </div>
              </div>

              <div className="mt-8 space-y-6">
                <div className="border-b border-white/10 pb-5">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">OPEN PIPELINE</div>
                  <div className="mt-2 font-mono text-3xl font-bold">{compactMoney(data.open_pipeline)}</div>
                </div>
                <div className="border-b border-white/10 pb-5">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">WEIGHTED PIPELINE</div>
                  <div className="mt-2 font-mono text-3xl font-bold text-blue-300">{compactMoney(data.weighted_pipeline)}</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">WON VALUE</div>
                  <div className="mt-2 font-mono text-3xl font-bold text-emerald-400">{compactMoney(data.won_value)}</div>
                  <div className="mt-5 rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between text-xs text-slate-300">
                      <span>Win contribution</span>
                      <strong className="text-white">{data.win_rate.toFixed(0)}%</strong>
                    </div>
                    <div className="mt-3 h-2 rounded-full bg-white/10">
                      <div className="h-2 rounded-full bg-emerald-400" style={{ width: `${Math.min(data.win_rate, 100)}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><PackageCheck className="size-5" /></div>
                <div>
                  <h2 className="font-heading text-lg font-semibold">Order Health</h2>
                  <p className="text-sm text-slate-500">Kondisi order berdasarkan status penyelesaian</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="min-w-24 rounded-xl bg-blue-50 px-5 py-3"><div className="text-[10px] font-semibold uppercase text-blue-600">OPEN</div><div className="mt-1 text-2xl font-bold text-blue-700">{data.open_orders}</div></div>
                <div className="min-w-24 rounded-xl bg-emerald-50 px-5 py-3"><div className="text-[10px] font-semibold uppercase text-emerald-600">COMPLETED</div><div className="mt-1 text-2xl font-bold text-emerald-700">{data.completed_orders}</div></div>
                <div className="min-w-24 rounded-xl bg-rose-50 px-5 py-3"><div className="text-[10px] font-semibold uppercase text-rose-600">OVERDUE</div><div className="mt-1 text-2xl font-bold text-rose-700">{data.overdue_orders}</div></div>
              </div>
            </div>
          </section>

          <section className="grid gap-5 xl:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-3"><Activity className="size-5 text-blue-600" /><div><h2 className="font-heading text-lg font-semibold">Recent Activities</h2><p className="text-xs text-slate-500">Aktivitas sales terbaru dari database</p></div></div>
              <div className="divide-y divide-slate-100">
                {data.recent_activities.slice(0, 6).map((item) => (
                  <div key={item.id} className="flex items-start justify-between gap-4 py-3">
                    <div><div className="text-sm font-medium">{item.subject}</div><div className="mt-1 text-xs text-slate-500">{item.customer_name ?? "Tanpa customer"} · {item.sales_name ?? "Unassigned"}</div></div>
                    <div className="text-right text-xs text-slate-400">{item.date ?? "—"}</div>
                  </div>
                ))}
                {!data.recent_activities.length && <div className="py-8 text-center text-sm text-slate-400">Belum ada aktivitas.</div>}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-3"><ClipboardList className="size-5 text-amber-600" /><div><h2 className="font-heading text-lg font-semibold">Deal Risk / Stalled</h2><p className="text-xs text-slate-500">Opportunity yang membutuhkan tindakan</p></div></div>
              <div className="divide-y divide-slate-100">
                {data.deal_risks.slice(0, 6).map((item) => (
                  <div key={item.id} className="flex items-start justify-between gap-4 py-3">
                    <div><div className="text-sm font-medium">{item.name}</div><div className="mt-1 text-xs text-slate-500">{item.customer_name} · {item.stage}</div><div className="mt-1 text-xs font-medium text-amber-700">{item.reason}</div></div>
                    <div className="font-mono text-xs text-slate-600">{compactMoney(item.value)}</div>
                  </div>
                ))}
                {!data.deal_risks.length && <div className="py-8 text-center text-sm text-slate-400">Tidak ada deal berisiko.</div>}
              </div>
            </div>
          </section>

          <div className="flex items-center justify-between border-t border-slate-200 pt-4 text-xs text-slate-400">
            <span>Live MongoDB aggregation · Diperbarui {new Date(data.generated_at).toLocaleString("id-ID")}</span>
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}><Gauge className="mr-2 size-4" />Refresh dashboard</Button>
          </div>
        </>
      )}
    </div>
  );
}
