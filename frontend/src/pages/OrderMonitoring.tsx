import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch } from "@/lib/api";
import type { Customer, Paginated, PurchaseOrder } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import DataTable from "@/components/DataTable";
import { Badge } from "@/components/ui/badge";
import { selectClass } from "@/components/Field";
import { toast } from "sonner";

const stages = ["Received", "Processing", "Indent", "Ready Stock", "Delivery", "Completed"];

export default function OrderMonitoring() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [etaFilter, setEtaFilter] = useState("");
  const [salesFilter, setSalesFilter] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");

  const query = useQuery({
    queryKey: ["order-monitoring"],
    queryFn: () => apiGet<Paginated<PurchaseOrder>>("/purchase-orders?page=1&page_size=50"),
  });
  const customerQuery = useQuery({
    queryKey: ["order-monitoring-customers"],
    queryFn: () => apiGet<Paginated<Customer>>("/customers?page=1&page_size=100"),
    staleTime: 60_000,
  });
  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => apiPatch<PurchaseOrder>(`/purchase-orders/${id}/status?status=${encodeURIComponent(status)}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order-monitoring"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Status order diperbarui");
    },
    onError: () => toast.error("Status order gagal diperbarui"),
  });

  const items = query.data?.items ?? [];
  const customers = customerQuery.data?.items ?? [];
  const customerByKey = useMemo(() => {
    const map = new Map<string, Customer>();
    customers.forEach((customer) => {
      map.set(customer.id, customer);
      if (customer.customer_id) map.set(customer.customer_id, customer);
    });
    return map;
  }, [customers]);
  const customerName = (order: PurchaseOrder) => {
    const customer = customerByKey.get(order.customer_id);
    return customer?.company_name || customer?.name || order.customer_name || "—";
  };
  const salesOptions = useMemo(() => Array.from(new Set(items.map((item) => item.sales_name).filter(Boolean))).sort(), [items]);
  const customerOptions = useMemo(() => Array.from(new Set(items.map((item) => customerName(item)).filter((name) => name !== "—"))).sort(), [items, customerByKey]);

  const filteredItems = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return items.filter((item) => {
      const customer = customerName(item);
      const product = item.items[0]?.description ?? "";
      const matchesSearch = !keyword || [item.po_number, product, customer].some((value) => String(value).toLowerCase().includes(keyword));
      const matchesStatus = !statusFilter || item.status === statusFilter;
      const matchesEta = !etaFilter || (etaFilter === "available" ? Boolean(item.eta) : !item.eta);
      const matchesSales = !salesFilter || (item.sales_name ?? "") === salesFilter;
      const matchesCustomer = !customerFilter || customer === customerFilter;
      return matchesSearch && matchesStatus && matchesEta && matchesSales && matchesCustomer;
    });
  }, [items, search, statusFilter, etaFilter, salesFilter, customerFilter, customerByKey]);

  const stats = [
    { label: "TOTAL", value: filteredItems.length },
    ...stages.map((stage) => ({ label: stage.toUpperCase(), value: filteredItems.filter((item) => item.status === stage).length })),
  ];

  return (
    <div data-testid="order-monitoring-page">
      <PageHeader title="Order Monitoring" description="PO Diterima → Processing → Indent → Ready Stock → Delivery → Completed" onRefresh={() => void query.refetch()} onExport={() => window.open("/api/exports/purchase-orders", "_blank")} />
      <div className="mb-4 grid grid-cols-[minmax(280px,1fr)_145px_175px_150px_245px] gap-2 overflow-x-auto border-y border-slate-200 bg-white p-3">
        <div className="relative min-w-0">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">⌕</span>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cari PO / produk / customer..." className="h-9 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm outline-none transition focus:border-blue-400 focus:ring-1 focus:ring-blue-100" />
        </div>
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className={`${selectClass} h-9 min-w-0`}>
          <option value="">Semua status</option>
          {stages.map((stage) => <option key={stage} value={stage}>{stage}</option>)}
        </select>
        <select value={etaFilter} onChange={(event) => setEtaFilter(event.target.value)} className={`${selectClass} h-9 min-w-0`}>
          <option value="">Semua indikator ETA</option>
          <option value="available">ETA tersedia</option>
          <option value="empty">ETA belum diisi</option>
        </select>
        <select value={salesFilter} onChange={(event) => setSalesFilter(event.target.value)} className={`${selectClass} h-9 min-w-0`}>
          <option value="">Semua sales</option>
          {salesOptions.map((sales) => <option key={sales} value={sales}>{sales}</option>)}
        </select>
        <select value={customerFilter} onChange={(event) => setCustomerFilter(event.target.value)} className={`${selectClass} h-9 min-w-0`}>
          <option value="">Semua customer</option>
          {customerOptions.map((customer) => <option key={customer} value={customer}>{customer}</option>)}
        </select>
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-slate-200 bg-white p-4" data-testid={`order-stat-${stat.label.toLowerCase().replaceAll(" ", "-")}`}>
            <div className="text-[10px] font-semibold tracking-wider text-slate-500">{stat.label}</div>
            <div className="mt-2 font-mono text-2xl font-semibold">{stat.value}</div>
          </div>
        ))}
      </div>
      <DataTable
        testId="order-monitoring-table"
        items={filteredItems}
        loading={query.isLoading || customerQuery.isLoading}
        total={filteredItems.length}
        columns={[
          { key: "id", label: "Monitoring ID", render: (item) => <span className="font-mono text-[10px] text-slate-500">{item.id.slice(0, 8).toUpperCase()}</span> },
          { key: "po", label: "Nomor PO", render: (item) => <span className="font-medium">{item.po_number}</span> },
          { key: "customer", label: "Customer", render: (item) => customerName(item) },
          { key: "product", label: "Produk", render: (item) => item.items[0]?.description ?? "—" },
          { key: "qty", label: "Qty", render: (item) => `${item.items[0]?.quantity ?? 0}` },
          { key: "status", label: "Status", render: (item) => <select className={`${selectClass} min-w-36`} value={item.status} onChange={(event) => update.mutate({ id: item.id, status: event.target.value })} data-testid={`order-status-${item.id}`}>{stages.map((stage) => <option key={stage}>{stage}</option>)}</select> },
          { key: "supplier", label: "Supplier", render: (item) => item.supplier ?? "—" },
          { key: "eta", label: "ETA", render: (item) => item.eta ?? "—" },
          { key: "indicator", label: "Indikator", render: (item) => <Badge variant={item.status === "Completed" ? "default" : "outline"}>{item.status === "Completed" ? "Selesai" : "Berjalan"}</Badge> },
          { key: "sales", label: "Sales", render: (item) => item.sales_name ?? "—" },
        ]}
      />
    </div>
  );
}
