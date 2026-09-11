import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch } from "@/lib/api";
import type { Customer, Paginated, PurchaseOrder, SalesTeamMetric } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { selectClass } from "@/components/Field";
import { toast } from "sonner";

const stages = ["Received", "Waiting Order", "Processing", "Indent", "Ready Stock", "Delivery", "Completed", "Cancelled"];
type MonitoringOrder = PurchaseOrder & { is_demo?: boolean };

function monitoringId(order: PurchaseOrder) {
  const match = order.po_number.match(/(\d+)$/);
  return `MON-${match ? match[1].padStart(4, "0") : order.id.slice(0, 4).toUpperCase()}`;
}
function etaIndicator(eta?: string, status?: string) {
  if (status === "Completed") return "Selesai";
  if (!eta) return "Due Soon";
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const etaDate = new Date(`${eta.slice(0, 10)}T00:00:00`);
  const diffDays = Math.ceil((etaDate.getTime() - today.getTime()) / 86400000);
  if (diffDays < 0) return "Overdue";
  return "Due Soon";
}
function isDemoOrder(order: PurchaseOrder) {
  return String(order.customer_id || "").startsWith("DEMO-CUS-") || String(order.po_number || "").startsWith("PO/CUST/DEMO/");
}

export default function OrderMonitoring() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [etaFilter, setEtaFilter] = useState("");
  const [salesFilter, setSalesFilter] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const query = useQuery({ queryKey: ["order-monitoring"], queryFn: () => apiGet<Paginated<MonitoringOrder>>("/order-monitoring?page=1&page_size=100") });
  const customerQuery = useQuery({ queryKey: ["order-monitoring-customers"], queryFn: () => apiGet<Paginated<Customer>>("/customers?page=1&page_size=100"), staleTime: 60_000 });
  const salesQuery = useQuery({ queryKey: ["order-monitoring-sales"], queryFn: () => apiGet<SalesTeamMetric[]>("/sales-team"), staleTime: 60_000 });
  const update = useMutation({ mutationFn: ({ id, status }: { id: string; status: string }) => apiPatch<PurchaseOrder>(`/purchase-orders/${id}/status?status=${encodeURIComponent(status)}`), onSuccess: () => { qc.invalidateQueries({ queryKey: ["order-monitoring"] }); qc.invalidateQueries({ queryKey: ["dashboard"] }); toast.success("Status order diperbarui"); }, onError: () => toast.error("Status order gagal diperbarui") });

  const items = query.data?.items ?? [];
  const customers = customerQuery.data?.items ?? [];
  const customerByKey = useMemo(() => { const map = new Map<string, Customer>(); customers.forEach((customer) => { map.set(customer.id, customer); if (customer.customer_id) map.set(customer.customer_id, customer); }); return map; }, [customers]);
  const linkedItems = useMemo(() => items.filter((item) => !isDemoOrder(item) && customerByKey.has(item.customer_id)), [items, customerByKey]);
  const customerName = (order: PurchaseOrder) => customerByKey.get(order.customer_id)?.name || order.customer_name || "—";
  const salesOptions = useMemo(() => { const fromSalesTeam = (salesQuery.data ?? []).map((item) => item.sales).filter(Boolean); const fromCustomers = customers.map((customer) => customer.sales_name).filter(Boolean) as string[]; const fromOrders = linkedItems.map((item) => item.sales_name).filter(Boolean) as string[]; return Array.from(new Set([...fromSalesTeam, ...fromCustomers, ...fromOrders])).sort(); }, [salesQuery.data, customers, linkedItems]);
  const customerOptions = useMemo(() => Array.from(new Set(customers.map((customer) => customer.name).filter(Boolean))).sort(), [customers]);
  const filteredItems = useMemo(() => { const keyword = search.trim().toLowerCase(); return linkedItems.filter((item) => { const customer = customerName(item); const product = item.items[0]?.description ?? ""; const indicator = etaIndicator(item.eta, item.status); const matchesSearch = !keyword || [item.po_number, product, customer].some((value) => String(value).toLowerCase().includes(keyword)); const matchesStatus = !statusFilter || item.status === statusFilter; const matchesEta = !etaFilter || indicator === etaFilter; const matchesSales = !salesFilter || (item.sales_name ?? "") === salesFilter; const matchesCustomer = !customerFilter || customer === customerFilter; return matchesSearch && matchesStatus && matchesEta && matchesSales && matchesCustomer; }); }, [linkedItems, search, statusFilter, etaFilter, salesFilter, customerFilter, customerByKey]);
  const pagedItems = useMemo(() => { const start = (page - 1) * pageSize; return filteredItems.slice(start, start + pageSize); }, [filteredItems, page, pageSize]);
  const stats = [{ label: "TOTAL", value: filteredItems.length }, ...stages.map((stage) => ({ label: stage.toUpperCase(), value: filteredItems.filter((item) => item.status === stage).length }))];

  return (
    <div data-testid="order-monitoring-page">
      <PageHeader title="Order Monitoring" description="PO Diterima → Processing → Indent → Ready Stock → Delivery → Completed" onRefresh={() => window.location.reload()} onExport={() => window.open("/api/exports/purchase-orders", "_blank")} />
      <div className="mb-4 grid grid-cols-[360px_145px_175px_150px_245px] gap-2 overflow-x-auto border-y border-slate-200 bg-white p-3">
        <div className="relative w-[360px] max-w-full"><span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">⌕</span><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Cari PO / produk / customer..." className="h-10 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm outline-none transition focus:border-blue-400 focus:ring-1 focus:ring-blue-100" /></div>
        <select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1); }} className={`${selectClass} h-10 min-w-0`}><option value="">Semua status</option>{stages.map((stage) => <option key={stage} value={stage}>{stage}</option>)}</select>
        <select value={etaFilter} onChange={(event) => { setEtaFilter(event.target.value); setPage(1); }} className={`${selectClass} h-10 min-w-0`}><option value="">Semua indikator ETA</option><option value="Overdue">Overdue</option><option value="Due Soon">Due Soon</option><option value="Selesai">Selesai</option></select>
        <select value={salesFilter} onChange={(event) => { setSalesFilter(event.target.value); setPage(1); }} className={`${selectClass} h-10 min-w-0`}><option value="">Semua sales</option>{salesOptions.map((sales) => <option key={sales} value={sales}>{sales}</option>)}</select>
        <select value={customerFilter} onChange={(event) => { setCustomerFilter(event.target.value); setPage(1); }} className={`${selectClass} h-10 min-w-0`}><option value="">Semua customer</option>{customerOptions.map((customer) => <option key={customer} value={customer}>{customer}</option>)}</select>
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">{stats.map((stat) => <div key={stat.label} className="rounded-lg border border-slate-200 bg-white p-4" data-testid={`order-stat-${stat.label.toLowerCase().replaceAll(" ", "-")}`}><div className="text-[10px] font-semibold tracking-wider text-slate-500">{stat.label}</div><div className="mt-2 font-mono text-2xl font-semibold">{stat.value}</div></div>)}</div>
      <DataTable testId="order-monitoring-table" items={pagedItems} loading={query.isLoading || customerQuery.isLoading || salesQuery.isLoading} total={filteredItems.length} page={page} pageSize={pageSize} onPage={setPage} onPageSize={size => { setPageSize(size); setPage(1); }} columns={[{ key: "id", label: "Monitoring ID", render: (item) => <span className="font-mono text-[10px] text-slate-500">{monitoringId(item)}</span> }, { key: "po", label: "Nomor PO", render: (item) => <span className="font-medium">{item.po_number}</span> }, { key: "customer", label: "Customer", render: (item) => customerName(item) }, { key: "product", label: "Produk", render: (item) => <div className="w-[420px] max-w-[420px] whitespace-normal break-words leading-5">{item.items[0]?.description ?? "—"}</div> }, { key: "qty", label: "Qty", render: (item) => `${item.items[0]?.quantity ?? 0}` }, { key: "status", label: "Status", render: (item) => <select className={`${selectClass} min-w-36`} value={item.status} onChange={(event) => update.mutate({ id: item.id, status: event.target.value })} data-testid={`order-status-${item.id}`}>{stages.map((stage) => <option key={stage}>{stage}</option>)}</select> }, { key: "supplier", label: "Supplier", render: (item) => item.supplier ?? "—" }, { key: "eta", label: "ETA", render: (item) => item.eta ?? "—" }, { key: "indicator", label: "Indikator", render: (item) => { const indicator = etaIndicator(item.eta, item.status); return <Badge variant={indicator === "Overdue" ? "destructive" : "outline"}>{indicator}</Badge>; } }, { key: "sales", label: "Sales", render: (item) => item.sales_name ?? "—" }]} />
    </div>
  );
}
