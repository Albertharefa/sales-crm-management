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
  const query = useQuery({
    queryKey: ["order-monitoring"],
    queryFn: () => apiGet<Paginated<PurchaseOrder>>("/purchase-orders/monitoring?page=1&page_size=50"),
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
  const customerByKey = new Map<string, Customer>();
  customers.forEach((customer) => {
    customerByKey.set(customer.id, customer);
    if (customer.customer_id) customerByKey.set(customer.customer_id, customer);
  });
  const customerName = (order: PurchaseOrder) => {
    const customer = customerByKey.get(order.customer_id);
    return customer?.company_name || customer?.name || order.customer_name || "—";
  };

  const stats = [
    { label: "TOTAL", value: items.length },
    ...stages.map((stage) => ({ label: stage.toUpperCase(), value: items.filter((item) => item.status === stage).length })),
  ];

  return (
    <div data-testid="order-monitoring-page">
      <PageHeader title="Order Monitoring" description="PO Diterima → Processing → Indent → Ready Stock → Delivery → Completed" onRefresh={() => void query.refetch()} onExport={() => window.open("/api/exports/purchase-orders", "_blank")} />
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
        items={items}
        loading={query.isLoading || customerQuery.isLoading}
        total={query.data?.total}
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
