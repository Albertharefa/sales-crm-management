import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Dispatch, SetStateAction } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import type { Options, Paginated, Quotation } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import DataTable from "@/components/DataTable";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Copy,
  Download,
  Eye,
  FileCheck2,
  Pencil,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";

const STATUS_OPTIONS = [
  "Draft",
  "Sent",
  "Negotiation",
  "Approved",
  "Rejected",
  "Expired",
  "Converted",
];

const money = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);

type QuotationForm = {
  customer_id: string;
  sales_id: string;
  date: string;
  valid_until: string;
  payment_term: string;
  delivery_term: string;
  product_id: string;
  description: string;
  quantity: string;
  unit_price: string;
  discount: string;
  tax: string;
  notes: string;
};

const emptyForm = (): QuotationForm => ({
  customer_id: "",
  sales_id: "",
  date: new Date().toISOString().slice(0, 10),
  valid_until: "",
  payment_term: "30 hari setelah invoice",
  delivery_term: "4–6 minggu setelah PO",
  product_id: "",
  description: "",
  quantity: "1",
  unit_price: "0",
  discount: "0",
  tax: "11",
  notes: "",
});

export default function Quotations() {
  const navigate = useNavigate();
  const [createModal, setCreateModal] = useState(false);
  const [viewModal, setViewModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [poModal, setPoModal] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [sales, setSales] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [poNumber, setPoNumber] = useState("");
  const [form, setForm] = useState<QuotationForm>(emptyForm());

  const qc = useQueryClient();

  const list = useQuery({
    queryKey: ["quotations", page, pageSize, search, status, sales],
    queryFn: () =>
      apiGet<Paginated<Quotation>>(
        `/quotations?page=${page}&page_size=${pageSize}&search=${encodeURIComponent(
          search,
        )}&status=${encodeURIComponent(status)}&sales=${encodeURIComponent(sales)}`,
      ),
  });

  const salesOptions = useQuery({
    queryKey: ["quotation-sales-options"],
    queryFn: () =>
      apiGet<{ id: string; name: string; role?: string }[]>(
        "/customers/sales-options",
      ),
    staleTime: 60_000,
  });

  const options = useQuery({
    queryKey: ["options"],
    queryFn: () => apiGet<Options>("/options"),
    staleTime: 60_000,
  });

  const detail = useQuery({
    queryKey: ["quotation-detail", selectedId],
    queryFn: () => apiGet<Quotation>(`/quotations/${selectedId}`),
    enabled: !!selectedId && (viewModal || editModal || poModal),
  });

  useEffect(() => {
    if (!editModal || !detail.data) return;
    const q = detail.data;
    const item = q.items?.[0];
    setForm({
      customer_id: q.customer_id ?? "",
      sales_id: q.sales_id ?? "",
      date: q.date ?? new Date().toISOString().slice(0, 10),
      valid_until: q.valid_until ?? "",
      payment_term: q.payment_term ?? "30 hari setelah invoice",
      delivery_term: q.delivery_term ?? "4–6 minggu setelah PO",
      product_id: item?.product_id ?? "",
      description: item?.description ?? "",
      quantity: String(item?.quantity ?? 1),
      unit_price: String(item?.unit_price ?? 0),
      discount: String(item?.discount ?? 0),
      tax: String(item?.tax ?? 11),
      notes: q.notes ?? "",
    });
  }, [editModal, detail.data]);

  const subtotal = useMemo(
    () =>
      Math.max(0, Number(form.quantity || 0) * Number(form.unit_price || 0)),
    [form.quantity, form.unit_price],
  );
  const discount = Math.max(0, Number(form.discount || 0));
  const taxable = Math.max(0, subtotal - discount);
  const taxValue = taxable * (Number(form.tax || 0) / 100);
  const grandTotal = taxable + taxValue;

  const closeAll = () => {
    setCreateModal(false);
    setViewModal(false);
    setEditModal(false);
    setPoModal(false);
    setSelectedId(null);
  };

  const create = useMutation({
    mutationFn: () =>
      apiPost<Quotation>("/quotations", {
        customer_id: form.customer_id,
        sales_id: form.sales_id || null,
        date: form.date,
        valid_until: form.valid_until || null,
        payment_term: form.payment_term,
        delivery_term: form.delivery_term,
        notes: form.notes,
        items: [
          {
            product_id: form.product_id || null,
            description: form.description,
            quantity: Number(form.quantity),
            unit_price: Number(form.unit_price),
            discount,
            tax: Number(form.tax),
          },
        ],
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["quotations"] });
      setCreateModal(false);
      setForm(emptyForm());
      toast.success(`${data.number} berhasil dibuat`);
    },
    onError: () => toast.error("Quotation gagal disimpan"),
  });

  const update = useMutation({
    mutationFn: () =>
      apiPut<Quotation>(`/quotations/${selectedId}`, {
        sales_id: form.sales_id || null,
        status: detail.data?.status ?? "Draft",
        valid_until: form.valid_until || null,
        payment_term: form.payment_term,
        delivery_term: form.delivery_term,
        notes: form.notes,
        items: [
          {
            product_id: form.product_id || null,
            description: form.description,
            quantity: Number(form.quantity),
            unit_price: Number(form.unit_price),
            discount,
            tax: Number(form.tax),
          },
        ],
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["quotations"] });
      qc.invalidateQueries({ queryKey: ["quotation-detail", selectedId] });
      setEditModal(false);
      toast.success("Quotation berhasil diperbarui");
    },
    onError: () => toast.error("Quotation gagal diperbarui"),
  });

  const changeStatus = useMutation({
    mutationFn: ({ id, value }: { id: string; value: string }) =>
      apiPut<Quotation>(`/quotations/${id}`, { status: value }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["quotations"] });
      toast.success("Status quotation diperbarui");
    },
    onError: () => toast.error("Status quotation gagal diperbarui"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => apiDelete<void>(`/quotations/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["quotations"] });
      toast.success("Quotation dihapus");
    },
    onError: () => toast.error("Quotation gagal dihapus"),
  });

  const duplicate = useMutation({
    mutationFn: (id: string) =>
      apiPost<Quotation>(`/quotations/${id}/duplicate`),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["quotations"] });
      toast.success(`${data.number} berhasil dibuat dari duplikasi`);
    },
    onError: () => toast.error("Quotation gagal diduplikasi"),
  });

  const savePo = useMutation({
    mutationFn: () =>
      apiPost<Quotation>(
        `/quotations/${selectedId}/customer-po?po_number=${encodeURIComponent(
          poNumber.trim(),
        )}`,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["quotations"] });
      qc.invalidateQueries({ queryKey: ["quotation-detail", selectedId] });
      setPoModal(false);
      setPoNumber("");
      toast.success("Nomor PO customer berhasil dicatat");
    },
    onError: () => toast.error("Nomor PO customer gagal disimpan"),
  });

  const openView = (id: string) => {
    setSelectedId(id);
    setViewModal(true);
  };

  const openEdit = (id: string) => {
    setSelectedId(id);
    setEditModal(true);
  };

  const openPo = (item: Quotation) => {
    setSelectedId(item.id);
    setPoNumber(item.customer_po_number ?? "");
    setPoModal(true);
  };

  const confirmDelete = (item: Quotation) => {
    if (
      window.confirm(
        `Hapus quotation ${item.number}? Data yang dihapus tidak dapat dikembalikan.`,
      )
    ) {
      remove.mutate(item.id);
    }
  };

  const refresh = async () => {
    await Promise.all([list.refetch(), salesOptions.refetch(), options.refetch()]);
    toast.success("Quotations berhasil diperbarui");
  };

  const resetCreate = () => {
    setForm(emptyForm());
    setCreateModal(true);
  };

  return (
    <div data-testid="quotations-page">
      <PageHeader
        title="Quotations"
        description="Nomor otomatis QT-TAHUN-URUT, item & total dihitung di server"
        action={{ label: "Buat Quotation", onClick: resetCreate }}
        onRefresh={refresh}
        onExport={() => window.open("/api/v1/exports/quotations", "_blank")}
      />

      <div className="mb-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid gap-3 md:grid-cols-[1.5fr_1fr_1fr]">
          <Input
            placeholder="Cari nomor / customer..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            data-testid="quotation-search-input"
          />
          <select
            className={selectClass}
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            data-testid="quotation-status-filter"
          >
            <option value="">Semua status</option>
            {STATUS_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <select
            className={selectClass}
            value={sales}
            onChange={(e) => {
              setSales(e.target.value);
              setPage(1);
            }}
            data-testid="quotation-sales-filter"
          >
            <option value="">Semua sales</option>
            {(salesOptions.data ?? []).map((item) => (
              <option key={item.id} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <DataTable
        testId="quotations-table"
        items={list.data?.items ?? []}
        loading={list.isLoading}
        total={list.data?.total}
        page={page}
        pageSize={pageSize}
        onPage={setPage}
        onPageSize={(size) => {
          setPageSize(size);
          setPage(1);
        }}
        columns={[
          {
            key: "number",
            label: "Nomor",
            render: (item) => (
              <button
                type="button"
                className="font-mono text-xs text-blue-600 hover:underline"
                title="Buka quotation untuk cetak / simpan PDF"
                onClick={() => navigate(`/quotations/${item.id}/print`)}
                data-testid={`quotation-number-${item.id}`}
              >
                {item.number}
              </button>
            ),
          },
          { key: "date", label: "Tanggal", render: (item) => item.date },
          {
            key: "customer",
            label: "Customer",
            render: (item) => (
              <span className="font-medium">{item.customer_name}</span>
            ),
          },
          { key: "sales", label: "Sales", render: (item) => item.sales_name ?? "—" },
          {
            key: "total",
            label: "Grand Total",
            render: (item) => (
              <span className="font-mono text-xs">{money(item.grand_total)}</span>
            ),
          },
          {
            key: "status",
            label: "Status",
            render: (item) => (
              <select
                className={`${selectClass} min-w-[118px] py-1.5 text-xs`}
                value={item.status}
                disabled={changeStatus.isPending}
                onChange={(e) =>
                  changeStatus.mutate({ id: item.id, value: e.target.value })
                }
                data-testid={`quotation-status-${item.id}`}
              >
                {STATUS_OPTIONS.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            ),
          },
          {
            key: "action",
            label: "Aksi",
            render: (item) => (
              <div className="flex items-center gap-1 whitespace-nowrap">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  title="View"
                  onClick={() => openView(item.id)}
                  data-testid={`quotation-view-${item.id}`}
                >
                  <Eye className="size-4 text-blue-600" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  title="Edit"
                  onClick={() => openEdit(item.id)}
                  data-testid={`quotation-edit-${item.id}`}
                >
                  <Pencil className="mr-1 size-4" />
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  title="Duplikat quotation"
                  onClick={() => duplicate.mutate(item.id)}
                  disabled={duplicate.isPending}
                  data-testid={`quotation-duplicate-${item.id}`}
                >
                  <Copy className="size-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  title="Catat PO Customer"
                  onClick={() => openPo(item)}
                  data-testid={`quotation-po-${item.id}`}
                >
                  <FileCheck2 className="size-4 text-blue-600" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  title="Hapus"
                  onClick={() => confirmDelete(item)}
                  disabled={remove.isPending}
                  data-testid={`quotation-delete-${item.id}`}
                >
                  <Trash2 className="size-4 text-red-500" />
                </Button>
              </div>
            ),
          },
        ]}
      />

      {createModal && (
        <QuotationFormModal
          title="Buat Quotation"
          form={form}
          setForm={setForm}
          options={options.data}
          salesOptions={salesOptions.data ?? []}
          subtotal={subtotal}
          discount={discount}
          taxValue={taxValue}
          grandTotal={grandTotal}
          submitting={create.isPending}
          onClose={() => setCreateModal(false)}
          onSubmit={() => create.mutate()}
        />
      )}

      {editModal && (
        <QuotationFormModal
          title="Edit Quotation"
          form={form}
          setForm={setForm}
          options={options.data}
          salesOptions={salesOptions.data ?? []}
          subtotal={subtotal}
          discount={discount}
          taxValue={taxValue}
          grandTotal={grandTotal}
          submitting={update.isPending || detail.isLoading}
          onClose={() => {
            setEditModal(false);
            setSelectedId(null);
          }}
          onSubmit={() => update.mutate()}
          editStatus={detail.data?.status}
          onStatusChange={(value) => {
            if (!selectedId) return;
            changeStatus.mutate({ id: selectedId, value });
            if (detail.data) {
              qc.setQueryData(["quotation-detail", selectedId], {
                ...detail.data,
                status: value,
              });
            }
          }}
        />
      )}

      {viewModal && (
        <Modal
          title="Detail Quotation"
          onClose={() => {
            setViewModal(false);
            setSelectedId(null);
          }}
        >
          {detail.isLoading ? (
            <div className="py-10 text-center text-slate-500">Memuat quotation...</div>
          ) : detail.data ? (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-2">
                <DetailItem label="Nomor" value={detail.data.number} />
                <DetailItem label="Tanggal" value={detail.data.date} />
                <DetailItem label="Customer" value={detail.data.customer_name} />
                <DetailItem label="Sales" value={detail.data.sales_name} />
                <DetailItem label="Berlaku Sampai" value={detail.data.valid_until} />
                <DetailItem label="Status" value={detail.data.status} />
                <DetailItem label="Payment Term" value={detail.data.payment_term} />
                <DetailItem label="Delivery Term" value={detail.data.delivery_term} />
                <DetailItem
                  label="PO Customer"
                  value={detail.data.customer_po_number}
                />
              </div>
              <div className="overflow-hidden rounded-lg border border-slate-200">
                <div className="bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Item Quotation
                </div>
                <div className="divide-y divide-slate-100">
                  {detail.data.items?.map((item, index) => (
                    <div key={index} className="p-4">
                      <div className="font-medium text-slate-800">{item.description}</div>
                      <div className="mt-2 grid grid-cols-3 gap-3 text-sm">
                        <DetailItem label="Qty" value={String(item.quantity)} />
                        <DetailItem label="Harga Satuan" value={money(item.unit_price)} />
                        <DetailItem label="Total" value={money(item.quantity * item.unit_price)} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg bg-slate-900 p-4 text-white">
                <div className="flex justify-between text-sm">
                  <span>Subtotal</span>
                  <span>{money(detail.data.subtotal)}</span>
                </div>
                <div className="mt-2 flex justify-between text-sm">
                  <span>Diskon</span>
                  <span>-{money(detail.data.discount_total)}</span>
                </div>
                <div className="mt-2 flex justify-between text-sm">
                  <span>Pajak</span>
                  <span>{money(detail.data.tax_total)}</span>
                </div>
                <div className="mt-3 flex justify-between border-t border-white/10 pt-3 font-semibold">
                  <span>Grand Total</span>
                  <span>{money(detail.data.grand_total)}</span>
                </div>
              </div>
              {detail.data.notes && (
                <div className="rounded-lg border border-slate-200 p-4 text-sm">
                  <div className="mb-1 text-xs font-semibold uppercase text-slate-400">
                    Catatan
                  </div>
                  {detail.data.notes}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() =>
                    window.open(`/api/v1/quotations/${detail.data?.id}/pdf`, "_blank")
                  }
                >
                  <Download className="mr-2 size-4" />
                  PDF
                </Button>
                <Button variant="outline" onClick={() => setViewModal(false)}>
                  Tutup
                </Button>
              </div>
            </div>
          ) : (
            <div className="py-10 text-center text-red-500">
              Quotation tidak ditemukan.
            </div>
          )}
        </Modal>
      )}

      {poModal && (
        <Modal
          title="Catat PO Customer"
          onClose={() => {
            setPoModal(false);
            setSelectedId(null);
            setPoNumber("");
          }}
        >
          <form
            className="space-y-5"
            onSubmit={(e) => {
              e.preventDefault();
              savePo.mutate();
            }}
          >
            <div className="text-sm text-slate-600">
              Quotation <strong>{detail.data?.number}</strong> —{" "}
              {detail.data?.customer_name}
            </div>
            <Field label="Nomor PO Customer" required>
              <Input
                value={poNumber}
                onChange={(e) => setPoNumber(e.target.value)}
                placeholder="mis. 450/PO/ESIC/2026"
                autoFocus
              />
            </Field>
            <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
              <Button type="button" variant="outline" onClick={() => setPoModal(false)}>
                Batal
              </Button>
              <Button type="submit" disabled={!poNumber.trim() || savePo.isPending}>
                {savePo.isPending ? "Menyimpan..." : "Simpan"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function QuotationFormModal({
  title,
  form,
  setForm,
  options,
  salesOptions,
  subtotal,
  discount,
  taxValue,
  grandTotal,
  submitting,
  onClose,
  onSubmit,
  editStatus,
  onStatusChange,
}: {
  title: string;
  form: QuotationForm;
  setForm: Dispatch<SetStateAction<QuotationForm>>;
  options?: Options;
  salesOptions: { id: string; name: string }[];
  subtotal: number;
  discount: number;
  taxValue: number;
  grandTotal: number;
  submitting: boolean;
  onClose: () => void;
  onSubmit: () => void;
  editStatus?: string;
  onStatusChange?: (value: string) => void;
}) {
  const update = (key: keyof QuotationForm, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  return (
    <Modal title={title} onClose={onClose}>
      <form
        className="space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
        data-testid="quotation-form"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Customer" required>
            <select
              className={selectClass}
              value={form.customer_id}
              onChange={(e) => update("customer_id", e.target.value)}
              disabled={title.startsWith("Edit")}
              data-testid="quotation-customer-input"
            >
              <option value="">— Pilih customer —</option>
              {(options?.customers ?? []).map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Sales" required>
            <select
              className={selectClass}
              value={form.sales_id}
              onChange={(e) => update("sales_id", e.target.value)}
              data-testid="quotation-sales-input"
            >
              <option value="">— Pilih sales —</option>
              {salesOptions.map((sales) => (
                <option key={sales.id} value={sales.id}>
                  {sales.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Tanggal Quotation" required>
            <Input
              type="date"
              value={form.date}
              onChange={(e) => update("date", e.target.value)}
              disabled={title.startsWith("Edit")}
              data-testid="quotation-date-input"
            />
          </Field>

          <Field label="Berlaku Sampai">
            <Input
              type="date"
              value={form.valid_until}
              onChange={(e) => update("valid_until", e.target.value)}
              data-testid="quotation-valid-input"
            />
          </Field>

          <Field label="Payment Term">
            <Input
              value={form.payment_term}
              onChange={(e) => update("payment_term", e.target.value)}
              data-testid="quotation-payment-input"
            />
          </Field>

          <Field label="Delivery Term">
            <Input
              value={form.delivery_term}
              onChange={(e) => update("delivery_term", e.target.value)}
              data-testid="quotation-delivery-input"
            />
          </Field>
        </div>

        {editStatus && (
          <Field label="Status">
            <select
              className={selectClass}
              value={editStatus}
              onChange={(e) => onStatusChange?.(e.target.value)}
            >
              {STATUS_OPTIONS.map((value) => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </Field>
        )}

        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-4 flex items-center justify-between">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Item Quotation
            </div>
          </div>

          <div className="grid gap-4">
            <Field label="Produk / Deskripsi" required>
              <select
                className={selectClass}
                value={form.product_id}
                onChange={(e) => {
                  const product = options?.products.find(
                    (item) => item.id === e.target.value,
                  );
                  setForm((current) => ({
                    ...current,
                    product_id: e.target.value,
                    description: product?.name ?? current.description,
                    unit_price: product?.default_price
                      ? String(product.default_price)
                      : current.unit_price,
                  }));
                }}
                data-testid="quotation-product-input"
              >
                <option value="">— Pilih produk —</option>
                {(options?.products ?? []).map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name}
                  </option>
                ))}
              </select>
              <Textarea
                className="mt-2 min-h-28"
                value={form.description}
                onChange={(e) => update("description", e.target.value)}
                placeholder={"Deskripsi / spesifikasi item — tekan ENTER untuk baris baru\nIndustrial PC Axiomtek\nIntel Core i5\nRAM 16GB"}
                data-testid="quotation-description-input"
              />
            </Field>

            <div className="grid gap-4 sm:grid-cols-4">
              <Field label="Qty">
                <Input
                  type="number"
                  min="1"
                  value={form.quantity}
                  onChange={(e) => update("quantity", e.target.value)}
                  data-testid="quotation-qty-input"
                />
              </Field>
              <Field label="Harga Satuan">
                <Input
                  type="number"
                  min="0"
                  value={form.unit_price}
                  onChange={(e) => update("unit_price", e.target.value)}
                  data-testid="quotation-price-input"
                />
              </Field>
              <Field label="Diskon Total (Rp)">
                <Input
                  type="number"
                  min="0"
                  value={form.discount}
                  onChange={(e) => update("discount", e.target.value)}
                  data-testid="quotation-discount-input"
                />
              </Field>
              <Field label="Pajak (%)">
                <Input
                  type="number"
                  min="0"
                  value={form.tax}
                  onChange={(e) => update("tax", e.target.value)}
                  data-testid="quotation-tax-input"
                />
              </Field>
            </div>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Catatan">
            <Textarea
              className="min-h-28"
              value={form.notes}
              onChange={(e) => update("notes", e.target.value)}
              data-testid="quotation-notes-input"
            />
          </Field>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="flex justify-between text-sm">
              <span>Subtotal</span>
              <span className="font-mono">{money(subtotal)}</span>
            </div>
            <div className="mt-2 flex justify-between text-sm">
              <span>Diskon</span>
              <span className="font-mono">-{money(discount)}</span>
            </div>
            <div className="mt-2 flex justify-between text-sm">
              <span>Pajak</span>
              <span className="font-mono">{money(taxValue)}</span>
            </div>
            <div className="mt-3 flex justify-between border-t border-slate-200 pt-3 font-semibold">
              <span>Grand Total</span>
              <span className="font-mono">{money(grandTotal)}</span>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            <X className="mr-2 size-4" />
            Batal
          </Button>
          <Button
            type="submit"
            disabled={
              submitting ||
              !form.customer_id ||
              !form.sales_id ||
              !form.date ||
              !form.description.trim() ||
              Number(form.quantity) < 1
            }
            data-testid="quotation-save-button"
          >
            {submitting ? "Menyimpan..." : title.startsWith("Edit") ? "Simpan Perubahan" : "Simpan Quotation"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function DetailItem({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </div>
      <div className="text-sm text-slate-800">{value || "—"}</div>
    </div>
  );
}
