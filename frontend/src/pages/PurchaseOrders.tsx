import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from "@/lib/api";
import type { Customer, Paginated, Product, PurchaseOrder } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import DataTable from "@/components/DataTable";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Eye, Pencil, Trash2, Search, Plus, X } from "lucide-react";

interface POItemForm {
  product_id: string;
  description: string;
  quantity: string;
  unit_price: string;
}

interface POForm {
  po_number: string;
  customer_id: string;
  sales_id: string;
  date: string;
  status: string;
  eta: string;
  supplier: string;
  shipping_address: string;
}

const STATUS_OPTIONS = ["Draft", "Received", "Confirmed", "Processing", "Completed", "Cancelled"];

const money = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);

const emptyItem = (): POItemForm => ({
  product_id: "",
  description: "",
  quantity: "1",
  unit_price: "0",
});

const emptyForm = (): POForm => ({
  po_number: "",
  customer_id: "",
  sales_id: "",
  date: new Date().toISOString().slice(0, 10),
  status: "Received",
  eta: "",
  supplier: "",
  shipping_address: "",
});

export default function PurchaseOrders() {
  const [modal, setModal] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [salesFilter, setSalesFilter] = useState("");
  const [viewOrder, setViewOrder] = useState<PurchaseOrder | null>(null);
  const [editing, setEditing] = useState<PurchaseOrder | null>(null);
  const [form, setForm] = useState<POForm>(emptyForm());
  const [items, setItems] = useState<POItemForm[]>([emptyItem()]);
  const qc = useQueryClient();

  const list = useQuery({
    queryKey: ["purchase-orders", search, statusFilter, salesFilter],
    queryFn: () =>
      apiGet<Paginated<PurchaseOrder>>(
        `/purchase-orders?page=1&page_size=25&search=${encodeURIComponent(search)}&status=${encodeURIComponent(statusFilter)}&sales=${encodeURIComponent(salesFilter)}`,
      ),
  });

  const customerOptions = useQuery({
    queryKey: ["purchase-order-customers"],
    queryFn: () => apiGet<Paginated<Customer>>("/customers?page=1&page_size=100"),
    staleTime: 60_000,
  });

  const salesOptions = useQuery({
    queryKey: ["purchase-order-sales-options"],
    queryFn: () => apiGet<{ id: string; name: string }[]>("/customers/sales-options"),
    staleTime: 60_000,
  });

  const productOptions = useQuery({
    queryKey: ["purchase-order-products"],
    queryFn: () => apiGet<Paginated<Product>>("/products?page=1&page_size=100"),
    staleTime: 60_000,
  });

  const customers = customerOptions.data?.items ?? [];
  const products = productOptions.data?.items ?? [];
  const sales = salesOptions.data ?? [];

  const total = items.reduce(
    (sum, item) => sum + Math.max(0, Number(item.quantity || 0) * Number(item.unit_price || 0)),
    0,
  );

  const saveOrder = useMutation({
    mutationFn: async () => {
      const payload = {
        po_number: form.po_number,
        customer_id: form.customer_id,
        sales_id: form.sales_id || null,
        date: form.date,
        status: form.status,
        eta: form.eta || null,
        supplier: form.supplier || null,
        shipping_address: form.shipping_address || null,
        document_name: editing?.document_name ?? null,
        items: items.map((item) => ({
          product_id: item.product_id || null,
          description: item.description,
          quantity: Number(item.quantity),
          unit_price: Number(item.unit_price),
        })),
      };

      return editing
        ? apiPut<PurchaseOrder>(`/purchase-orders/${editing.id}`, payload)
        : apiPost<PurchaseOrder>("/purchase-orders", payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["purchase-orders"] });
      closeForm();
      toast.success(editing ? "Purchase Order berhasil diperbarui" : "Purchase Order berhasil disimpan");
    },
    onError: () => toast.error("Purchase Order gagal disimpan"),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      apiPatch<PurchaseOrder>(`/purchase-orders/${id}/status?status=${encodeURIComponent(status)}`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["purchase-orders"] });
      toast.success("Status PO diperbarui");
    },
    onError: () => toast.error("Status PO gagal diperbarui"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => apiDelete(`/purchase-orders/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["purchase-orders"] });
      setViewOrder(null);
      toast.success("Purchase Order dihapus");
    },
    onError: () => toast.error("Purchase Order gagal dihapus"),
  });

  function closeForm() {
    setModal(false);
    setEditing(null);
    setForm(emptyForm());
    setItems([emptyItem()]);
  }

  function openCreate() {
    setEditing(null);
    setForm(emptyForm());
    setItems([emptyItem()]);
    setModal(true);
  }

  function openEdit(order: PurchaseOrder) {
    setEditing(order);
    setForm({
      po_number: order.po_number,
      customer_id: order.customer_id,
      sales_id: "",
      date: order.date,
      status: order.status,
      eta: order.eta ?? "",
      supplier: order.supplier ?? "",
      shipping_address: "",
    });
    setItems(
      order.items?.length
        ? order.items.map((item) => ({
            product_id: item.product_id ?? "",
            description: item.description ?? "",
            quantity: String(item.quantity ?? 1),
            unit_price: String(item.unit_price ?? 0),
          }))
        : [emptyItem()],
    );
    setModal(true);
  }

  function updateItem(index: number, key: keyof POItemForm, value: string) {
    setItems((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index ? { ...item, [key]: value } : item,
      ),
    );
  }

  function selectProduct(index: number, productId: string) {
    const product = products.find((item) => item.id === productId);
    setItems((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              product_id: productId,
              description: product?.name ?? item.description,
              unit_price:
                product?.default_price !== undefined
                  ? String(product.default_price)
                  : item.unit_price,
            }
          : item,
      ),
    );
  }

  return (
    <div data-testid="purchase-orders-page">
      <PageHeader
        title="Purchase Order Customer"
        description="Nomor PO berasal dari customer dan tersimpan bersama dokumen pendukung"
        action={{ label: "Input PO Customer", onClick: openCreate }}
        onRefresh={() => void list.refetch()}
        onExport={() => window.open("/api/v1/exports/purchase-orders", "_blank")}
      />

      <div className="mb-5 grid grid-cols-1 gap-3 md:grid-cols-[minmax(360px,1fr)_220px_260px]">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari nomor PO / customer..."
            className="h-10 w-full pl-9"
            data-testid="purchase-orders-search-input"
          />
        </div>
        <select
          className={selectClass + " h-10"}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          data-testid="purchase-orders-status-filter"
        >
          <option value="">Semua status</option>
          {STATUS_OPTIONS.map((status) => <option key={status}>{status}</option>)}
        </select>
        <select
          className={selectClass + " h-10"}
          value={salesFilter}
          onChange={(e) => setSalesFilter(e.target.value)}
          data-testid="purchase-orders-sales-filter"
        >
          <option value="">Semua sales</option>
          {sales.map((item) => <option key={item.id} value={item.name}>{item.name}</option>)}
        </select>
      </div>

      <DataTable
        testId="purchase-orders-table"
        items={list.data?.items ?? []}
        loading={list.isLoading}
        total={list.data?.total}
        columns={[
          { key: "number", label: "No PO Customer", render: (item) => <a href={`/purchase-orders/${item.id}`} className="font-mono text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline">{item.po_number}</a> },
          { key: "date", label: "Tanggal", render: (item) => item.date },
          { key: "customer", label: "Customer", render: (item) => <span className="font-medium">{item.customer_name}</span> },
          { key: "quotation", label: "Quotation", render: (item) => item.quotation_number ?? "Manual order" },
          { key: "sales", label: "Sales", render: (item) => item.sales_name ?? "—" },
          { key: "value", label: "Nilai PO", render: (item) => <span className="font-mono text-xs">{money(item.total)}</span> },
          {
            key: "status",
            label: "Status",
            render: (item) => (
              <select
                className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm"
                value={item.status}
                onChange={(e) => updateStatus.mutate({ id: item.id, status: e.target.value })}
              >
                {STATUS_OPTIONS.map((status) => <option key={status}>{status}</option>)}
              </select>
            ),
          },
          {
            key: "actions",
            label: "Aksi",
            render: (item) => (
              <div className="flex items-center justify-end gap-4 whitespace-nowrap">
                <button type="button" title="View" className="text-slate-600 hover:text-blue-600" onClick={() => setViewOrder(item)}>
                  <Eye className="h-4 w-4" />
                </button>
                <button type="button" title="Edit" className="inline-flex items-center gap-1 text-sm font-medium text-slate-700 hover:text-blue-600" onClick={() => openEdit(item)}>
                  <Pencil className="h-4 w-4" />Edit
                </button>
                <button type="button" title="Delete" className="text-red-500 hover:text-red-700" onClick={() => { if (window.confirm("Hapus PO " + item.po_number + "?")) remove.mutate(item.id); }}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ),
          },
        ]}
      />

      {viewOrder && (
        <Modal title={"Detail PO " + viewOrder.po_number} onClose={() => setViewOrder(null)} size="landscape">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-3 rounded-lg border border-slate-200 p-5">
              <div><span className="text-xs text-slate-500">NO PO CUSTOMER</span><div className="font-mono font-semibold">{viewOrder.po_number}</div></div>
              <div><span className="text-xs text-slate-500">CUSTOMER</span><div>{viewOrder.customer_name}</div></div>
              <div><span className="text-xs text-slate-500">TANGGAL</span><div>{viewOrder.date}</div></div>
              <div><span className="text-xs text-slate-500">SALES</span><div>{viewOrder.sales_name ?? "—"}</div></div>
            </div>
            <div className="space-y-3 rounded-lg border border-slate-200 p-5">
              <div><span className="text-xs text-slate-500">STATUS</span><div><Badge>{viewOrder.status}</Badge></div></div>
              <div><span className="text-xs text-slate-500">NILAI PO</span><div className="font-mono font-semibold">{money(viewOrder.total)}</div></div>
              <div><span className="text-xs text-slate-500">ETA</span><div>{viewOrder.eta ?? "—"}</div></div>
              <div><span className="text-xs text-slate-500">SUPPLIER</span><div>{viewOrder.supplier ?? "—"}</div></div>
            </div>
          </div>
          <div className="mt-5 rounded-lg border border-slate-200 p-5">
            <h3 className="mb-3 font-semibold">Item PO</h3>
            {viewOrder.items?.map((item, index) => (
              <div key={index} className="grid gap-3 border-t py-3 sm:grid-cols-4">
                <div className="sm:col-span-2">{item.description}</div>
                <div>Qty: {item.quantity}</div>
                <div>{money(item.quantity * item.unit_price)}</div>
              </div>
            ))}
          </div>
        </Modal>
      )}

      {modal && (
        <Modal
          title={editing ? "Edit Purchase Order Customer" : "Input Purchase Order dari Customer"}
          onClose={closeForm}
          size="landscape"
        >
          <form
            className="space-y-5"
            onSubmit={(event) => {
              event.preventDefault();
              if (!form.customer_id || !form.sales_id || !form.po_number || items.length === 0) {
                toast.error("Customer, Sales, No PO, dan minimal 1 item wajib diisi");
                return;
              }
              if (items.some((item) => !item.description.trim() || Number(item.quantity) < 1)) {
                toast.error("Deskripsi item dan Qty wajib diisi");
                return;
              }
              saveOrder.mutate();
            }}
            data-testid="purchase-order-create-form"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="No PO Customer" required>
                <Input value={form.po_number} onChange={(e) => setForm({ ...form, po_number: e.target.value })} placeholder="PO/ELSI/2026/0088" data-testid="purchase-order-number-input" />
              </Field>
              <Field label="Customer" required>
                <select className={selectClass} value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} data-testid="purchase-order-customer-input">
                  <option value="">— Pilih customer —</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.company_name || customer.name || customer.customer_id}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Tanggal PO">
                <Input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} data-testid="purchase-order-date-input" />
              </Field>
              <Field label="Sales" required>
                <select className={selectClass} value={form.sales_id} onChange={(e) => setForm({ ...form, sales_id: e.target.value })} data-testid="purchase-order-sales-input">
                  <option value="">— Pilih sales —</option>
                  {sales.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </Field>
              <Field label="Status">
                <select className={selectClass} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} data-testid="purchase-order-status-input">
                  {STATUS_OPTIONS.map((status) => <option key={status}>{status}</option>)}
                </select>
              </Field>
              <Field label="ETA">
                <Input type="date" value={form.eta} onChange={(e) => setForm({ ...form, eta: e.target.value })} data-testid="purchase-order-eta-input" />
              </Field>
              <Field label="Payment Term">
                <Input value="" readOnly placeholder="30 hari setelah invoice" />
              </Field>
              <Field label="Dokumen PO">
                <Input type="file" accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx" data-testid="purchase-order-file-input" />
              </Field>
            </div>

            <Field label="Alamat Pengiriman">
              <Textarea value={form.shipping_address} onChange={(e) => setForm({ ...form, shipping_address: e.target.value })} data-testid="purchase-order-address-input" />
            </Field>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-4 flex items-center justify-between">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Item PO</div>
                <Button type="button" variant="outline" size="sm" onClick={() => setItems((current) => [...current, emptyItem()])} data-testid="purchase-order-add-item-button">
                  <Plus className="mr-2 h-4 w-4" />Tambah Item
                </Button>
              </div>

              <div className="space-y-3">
                {items.map((item, index) => {
                  const itemTotal = Math.max(0, Number(item.quantity || 0) * Number(item.unit_price || 0));
                  return (
                    <div key={index} className="rounded-lg border border-slate-200 bg-slate-50/60 p-4" data-testid={`purchase-order-item-${index}`}>
                      <div className="mb-3 flex items-center justify-between">
                        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Item {index + 1}</div>
                        {items.length > 1 && (
                          <Button type="button" variant="ghost" size="icon-sm" title="Hapus item" onClick={() => setItems((current) => current.filter((_, itemIndex) => itemIndex !== index))}>
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </div>

                      <div className="grid gap-4 lg:grid-cols-[1.4fr_2fr_120px_180px_150px]">
                        <Field label="Produk">
                          <select className={selectClass} value={item.product_id} onChange={(e) => selectProduct(index, e.target.value)} data-testid={`purchase-order-product-input-${index}`}>
                            <option value="">— Pilih produk —</option>
                            {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
                          </select>
                        </Field>
                        <Field label="Deskripsi">
                          <Input value={item.description} onChange={(e) => updateItem(index, "description", e.target.value)} placeholder="Deskripsi item PO" data-testid={`purchase-order-description-input-${index}`} />
                        </Field>
                        <Field label="Qty">
                          <Input type="number" min="1" value={item.quantity} onChange={(e) => updateItem(index, "quantity", e.target.value)} data-testid={`purchase-order-qty-input-${index}`} />
                        </Field>
                        <Field label="Harga Satuan">
                          <Input type="number" min="0" value={item.unit_price} onChange={(e) => updateItem(index, "unit_price", e.target.value)} data-testid={`purchase-order-price-input-${index}`} />
                        </Field>
                        <div className="flex items-end justify-end pb-2 font-mono text-xs font-semibold text-slate-700">{money(itemTotal)}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between rounded-lg bg-slate-900 p-4 text-white">
              <span>Total PO</span>
              <span className="font-mono text-blue-300">{money(total)}</span>
            </div>

            <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
              <Button type="button" variant="outline" onClick={closeForm} data-testid="purchase-order-cancel-button">
                <X className="mr-2 h-4 w-4" />Batal
              </Button>
              <Button type="submit" disabled={saveOrder.isPending} data-testid="purchase-order-save-button">
                {saveOrder.isPending ? "Menyimpan..." : editing ? "Simpan Perubahan" : "Simpan PO Customer"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
