import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { apiGet } from "@/lib/api";
import type { PurchaseOrder } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Printer, Truck } from "lucide-react";

const money = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value || 0);

const dateText = (value?: string | null) => {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

export default function PurchaseOrderDetail() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();

  const query = useQuery({
    queryKey: ["purchase-order-detail-page", orderId],
    queryFn: () => apiGet<PurchaseOrder>(`/purchase-orders/${orderId}`),
    enabled: !!orderId,
  });

  const order = query.data;

  if (query.isLoading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center text-slate-500">
        Memuat detail Purchase Order...
      </div>
    );
  }

  if (query.isError || !order) {
    return (
      <div className="space-y-4">
        <Button variant="outline" onClick={() => navigate("/purchase-orders")}>
          <ArrowLeft className="mr-2 size-4" />
          Kembali ke daftar
        </Button>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-600">
          Gagal mengambil detail Purchase Order.
        </div>
      </div>
    );
  }

  return (
    <div className="po-print-sheet min-h-full space-y-6 pb-10" data-testid="purchase-order-detail-page">
      <div className="po-print-actions flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => navigate("/purchase-orders")}
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="size-4" />
          Kembali ke daftar
        </button>

        <div className="flex items-center gap-2">
          <Badge
            variant="secondary"
            className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-amber-700"
          >
            {order.status}
          </Badge>
          <Button
            type="button"
            variant="outline"
            onClick={() => window.print()}
            data-testid="purchase-order-print-button"
          >
            <Printer className="mr-2 size-4" />
            Cetak
          </Button>
          <Button
            type="button"
            onClick={() => navigate("/order-monitoring")}
            data-testid="purchase-order-monitoring-button"
          >
            <Truck className="mr-2 size-4" />
            Buat Order Monitoring
          </Button>
        </div>
      </div>

      <div className="border-b border-slate-200 pb-5">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-heading text-4xl font-semibold tracking-tight text-slate-900">
              PO Customer {order.po_number}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Diterima dari: <span className="font-medium text-slate-700">{order.customer_name}</span>
            </p>
          </div>
          <div className="text-sm text-slate-400">
            Purchase Order Customer
          </div>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-x-10 gap-y-5 sm:grid-cols-2 lg:grid-cols-4">
          <Info label="No PO Customer" value={order.po_number} mono />
          <Info label="Tanggal PO" value={dateText(order.date)} />
          <Info label="Quotation" value={order.quotation_number} mono />
          <Info label="Sales" value={order.sales_name} />
          <Info label="Payment Term" value="30 hari setelah invoice" />
          <Info label="Alamat Kirim" value="—" />
          <Info label="Customer ID" value={order.customer_id} mono />
          <Info label="Nilai PO" value={money(order.total)} strong />
        </div>

        <div className="mt-5 border-t border-slate-200 pt-5">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Status Purchase Order
          </div>
          <div className="mt-2">
            <Badge variant="secondary">{order.status}</Badge>
          </div>
        </div>
      </section>

      <section className="po-print-items overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-4">
          <h2 className="text-base font-semibold text-slate-900">Item PO</h2>
        </div>

        {order.items?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3 w-12">#</th>
                  <th className="px-6 py-3">Deskripsi</th>
                  <th className="px-6 py-3 text-right">Qty</th>
                  <th className="px-6 py-3">Unit</th>
                  <th className="px-6 py-3 text-right">Harga</th>
                  <th className="px-6 py-3 text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {order.items.map((item, index) => (
                  <tr key={`${order.id}-item-${index}`}>
                    <td className="px-6 py-4 text-slate-500">{index + 1}</td>
                    <td className="px-6 py-4 font-medium text-slate-800">
                      {item.description || "—"}
                    </td>
                    <td className="px-6 py-4 text-right">{item.quantity}</td>
                    <td className="px-6 py-4 text-slate-500">Unit</td>
                    <td className="px-6 py-4 text-right font-mono text-xs">
                      {money(item.unit_price)}
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-xs font-semibold">
                      {money(item.quantity * item.unit_price)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-slate-200 bg-slate-50">
                  <td colSpan={5} className="px-6 py-4 text-right font-semibold text-slate-700">
                    Total PO
                  </td>
                  <td className="px-6 py-4 text-right font-mono font-semibold text-slate-900">
                    {money(order.total)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-sm text-slate-400">
            Belum ada item pada Purchase Order ini.
          </div>
        )}
      </section>

      <div className="text-sm text-slate-500">
        {order.quotation_number ? (
          <>
            Dikonversi dari{" "}
            <span className="font-mono font-medium text-slate-700">
              {order.quotation_number}
            </span>
          </>
        ) : (
          "Purchase Order tidak terhubung dengan quotation."
        )}
      </div>
    </div>
  );
}

function Info({
  label,
  value,
  mono = false,
  strong = false,
}: {
  label: string;
  value?: string | null;
  mono?: boolean;
  strong?: boolean;
}) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </div>
      <div
        className={[
          "mt-1 text-sm text-slate-800",
          mono ? "font-mono" : "",
          strong ? "font-semibold" : "",
        ].join(" ")}
      >
        {value || "—"}
      </div>
    </div>
  );
}
