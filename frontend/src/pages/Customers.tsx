import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import type { Customer, Paginated, Contact } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Search, Trash2, Eye, X, Pencil } from "lucide-react";
import PaginationControls from "@/components/PaginationControls";

export default function Customers() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [industry, setIndustry] = useState("");
  const [sales, setSales] = useState("");
  const [modal, setModal] = useState(false);
  const [detailModal, setDetailModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(
    null
  );
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const [form, setForm] = useState({
    name: "",
    company_name: "",
    industry: "Manufacturing",
    source: "Referral",
    city: "Jakarta",
    province: "",
    phone: "",
    email: "",
    pic_name: "",
    pic_position: "",
    status: "Active",
    sales_id: "",
    sales_name: "",
    address: "",
    notes: "",
  });

  const qc = useQueryClient();

  /* =========================
     CUSTOMER LIST
  ========================= */

  const query = useQuery({
    queryKey: ["customers", page, pageSize, search, status, industry, sales],
    queryFn: () =>
      apiGet<Paginated<Customer>>(
        `/customers?page=${page}&page_size=${pageSize}&search=${encodeURIComponent(
          search
        )}&status=${encodeURIComponent(status)}&industry=${encodeURIComponent(
          industry
        )}&sales_id=${encodeURIComponent(sales)}`
      ),
  });

  const salesOptionsQuery = useQuery({
    queryKey: ["sales-master-options"],
    queryFn: () => apiGet<{ id: string; name: string }[]>("/customers/sales-options"),
    staleTime: 60_000,
  });

  /* =========================
     CUSTOMER DETAIL
  ========================= */

  const detailQuery = useQuery({
    queryKey: ["customer-detail", selectedCustomerId],
    queryFn: () =>
      apiGet<Customer>(`/customers/${selectedCustomerId}`),
    enabled: !!selectedCustomerId && (detailModal || editModal),
  });

  /* =========================
     CUSTOMER CONTACTS
  ========================= */

  const contactsQuery = useQuery({
    queryKey: ["customer-contacts", selectedCustomerId],
    queryFn: () =>
      apiGet<Contact[]>(
        `/customers/${selectedCustomerId}/contacts`
      ),
    enabled: !!selectedCustomerId && detailModal,
  });

  /* =========================
     OPEN DETAIL
  ========================= */

  const openDetail = (customerId: string) => {
    setSelectedCustomerId(customerId);
    setDetailModal(true);
  };

  const closeDetail = () => {
    setDetailModal(false);
    setSelectedCustomerId(null);
  };

  /* =========================
     EDIT CUSTOMER
  ========================= */

  const updateCustomer = useMutation({
    mutationFn: () =>
      apiPut<Customer>(`/customers/${selectedCustomerId}`, {
        ...form,
        email: form.email || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["customers"] });
      qc.invalidateQueries({
        queryKey: ["customer-detail", selectedCustomerId],
      });
      setEditModal(false);
      setSelectedCustomerId(null);
      toast.success("Customer berhasil diperbarui");
    },
    onError: () => {
      toast.error("Customer gagal diperbarui");
    },
  });

  const openEdit = (customerId: string) => {
    setSelectedCustomerId(customerId);
    setEditModal(true);
  };

  useEffect(() => {
    if (!editModal || !detailQuery.data) return;

    const customer = detailQuery.data;

    setForm({
      name: customer.name ?? "",
      company_name: customer.company_name ?? "",
      industry: customer.industry ?? "Manufacturing",
      source: customer.source ?? "Referral",
      city: customer.city ?? "",
      province: customer.province ?? "",
      phone: customer.phone ?? "",
      email: customer.email ?? "",
      pic_name: customer.pic_name ?? "",
      pic_position: customer.pic_position ?? "",
      status: customer.status ?? "Active",
      sales_id: customer.sales_id ?? "",
      sales_name: customer.sales_name ?? "",
      address: customer.address ?? "",
      notes: customer.notes ?? "",
    });
  }, [editModal, detailQuery.data]);

  /* =========================
     CREATE CUSTOMER
  ========================= */

  const create = useMutation({
    mutationFn: () =>
      apiPost<Customer>("/customers", {
        ...form,
        email: form.email || null,
      }),

    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["customers"] });

      setModal(false);

      setForm({
        name: "",
        industry: "Manufacturing",
        city: "Jakarta",
        phone: "",
        email: "",
        pic_name: "",
        status: "Active",
        address: "",
        notes: "",
      });

      toast.success("Customer berhasil ditambahkan");
    },

    onError: () => {
      toast.error("Customer gagal disimpan");
    },
  });

  /* =========================
     DELETE CUSTOMER
  ========================= */

  const remove = useMutation({
    mutationFn: (id: string) =>
      apiDelete<void>(`/customers/${id}`),

    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["customers"] });
      toast.success("Customer dihapus");
    },

    onError: () => {
      toast.error("Customer gagal dihapus");
    },
  });

  return (
    <div data-testid="customers-page">

      {/* =========================
          PAGE HEADER
      ========================= */}

      <PageHeader
        title="Customers"
        description="Database pelanggan — pencarian dan filter dijalankan di server"
        action={{
          label: "Tambah Customer",
          onClick: () => setModal(true),
        }}
        onRefresh={() => window.location.reload()}
        onExport={() =>
          window.open(`/api/v1/customers/export`, "_blank")
        }
      />

      {/* =========================
          SEARCH & FILTER
      ========================= */}

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">

        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-2.5 size-4 text-slate-400" />

          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Cari nama, PIC, email..."
            className="pl-9"
            data-testid="customers-search-input"
          />
        </div>

        <select
          className={selectClass}
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          data-testid="customers-status-filter"
        >
          <option value="">Semua status</option>
          <option value="Active">Active</option>
          <option value="Prospect">Prospect</option>
          <option value="Inactive">Inactive</option>
        </select>

        <select
          className={selectClass}
          value={industry}
          onChange={(e) => {
            setIndustry(e.target.value);
            setPage(1);
          }}
          data-testid="customers-industry-filter"
        >
          <option value="">Semua industri</option>

          {[
            "Manufacturing",
            "Oil & Gas",
            "Mining",
            "EPC",
            "Power Generation",
          ].map((v) => (
            <option key={v}>{v}</option>
          ))}
        </select>

        <select
          className={selectClass}
          value={sales}
          onChange={(e) => {
            setSales(e.target.value);
            setPage(1);
          }}
          data-testid="customers-sales-filter"
        >
          <option value="">Semua sales</option>
          {salesOptionsQuery.data?.map((sales) => (
                    <option key={sales.id} value={sales.id}>
                      {sales.name}
                    </option>
                  ))}
        </select>

      </div>

      {/* =========================
          CUSTOMER TABLE
      ========================= */}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full text-left text-sm">

            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500">

              <tr>
                {[
                  "Customer ID",
                  "Nama Customer",
                  "Industri",
                  "Kota",
                  "PIC",
                  "Sales",
                  "Status",
                  "Aksi",
                ].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 font-semibold"
                  >
                    {h}
                  </th>
                ))}
              </tr>

            </thead>

            <tbody className="divide-y divide-slate-100">

              {query.isLoading ? (

                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-10 text-center text-slate-400"
                    data-testid="customers-loading-state"
                  >
                    Memuat customer...
                  </td>
                </tr>

              ) : query.isError ? (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-10 text-center text-red-500"
                    data-testid="customers-error-state"
                  >
                    Gagal memuat customer. Silakan tekan Refresh.
                  </td>
                </tr>
              ) : query.data?.items?.length ? (

                query.data.items.map((customer) => (

                  <tr
                    key={customer.id}
                    className="hover:bg-slate-50"
                    data-testid={`customer-row-${customer.customer_id}`}
                  >

                    {/* CUSTOMER ID - CLICKABLE */}

                    <td className="px-4 py-3">

                      <button
                        type="button"
                        onClick={() =>
                          openDetail(customer.id)
                        }
                        className="font-mono text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        {customer.customer_id}
                      </button>

                    </td>

                    {/* CUSTOMER NAME - CLICKABLE */}

                    <td className="px-4 py-3 font-medium">

                      <button
                        type="button"
                        onClick={() =>
                          openDetail(customer.id)
                        }
                        className="text-left hover:text-blue-600 hover:underline"
                      >
                        {customer.name}
                      </button>

                    </td>

                    <td className="px-4 py-3 text-slate-600">
                      {customer.industry}
                    </td>

                    <td className="px-4 py-3 text-slate-600">
                      {customer.city}
                    </td>

                    <td className="px-4 py-3">
                      {customer.pic_name ?? "—"}
                    </td>

                    <td className="px-4 py-3">
                      {customer.sales_name ?? "—"}
                    </td>

                    <td className="px-4 py-3">

                      <Badge
                        variant={
                          customer.status === "Active"
                            ? "default"
                            : "secondary"
                        }
                      >
                        {customer.status}
                      </Badge>

                    </td>

                    {/* ACTION */}

                    <td className="px-4 py-3">

                      <div className="flex items-center gap-1">

                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() =>
                            openDetail(customer.id)
                          }
                          title="Lihat detail"
                        >
                          <Eye className="size-4 text-blue-600" />
                        </Button>

                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => openEdit(customer.id)}
                          data-testid={`customer-edit-${customer.customer_id}`}
                          title="Edit customer"
                        >
                          <Pencil className="size-4 text-slate-600" />
                        </Button>

                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() =>
                            remove.mutate(customer.id)
                          }
                          data-testid={`customer-delete-${customer.customer_id}`}
                          title="Hapus customer"
                        >
                          <Trash2 className="size-4 text-red-500" />
                        </Button>

                      </div>

                    </td>

                  </tr>

                ))

              ) : (

                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-10 text-center text-slate-400"
                  >
                    Tidak ada customer ditemukan.
                  </td>
                </tr>

              )}

            </tbody>

          </table>

        </div>

        <PaginationControls
          page={page}
          pageSize={pageSize}
          total={query.data?.total ?? 0}
          onPage={setPage}
          onPageSize={(size) => {
            setPageSize(size);
            setPage(1);
          }}
          testId="customers"
        />

      </div>

      {/* =====================================================
          CUSTOMER DETAIL MODAL
      ===================================================== */}

      {detailModal && (

        <Modal
          title="Detail Customer"
          onClose={closeDetail}
        >

          {detailQuery.isLoading ? (

            <div className="py-10 text-center text-slate-500">
              Memuat detail customer...
            </div>

          ) : detailQuery.isError ? (

            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              Gagal mengambil detail customer.
            </div>

          ) : detailQuery.data ? (

            <div className="space-y-6">

              {/* CUSTOMER HEADER */}

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">

                <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-blue-600">
                  Customer
                </div>

                <div className="text-xl font-semibold text-slate-900">
                  {detailQuery.data.name}
                </div>

                <div className="mt-1 font-mono text-sm text-slate-500">
                  {detailQuery.data.customer_id}
                </div>

              </div>

              {/* STATUS */}

              <div className="flex items-center justify-between">

                <span className="text-sm font-medium text-slate-600">
                  Status
                </span>

                <Badge
                  variant={
                    detailQuery.data.status === "Active"
                      ? "default"
                      : "secondary"
                  }
                >
                  {detailQuery.data.status}
                </Badge>

              </div>

              {/* CUSTOMER INFORMATION */}

              <div>

                <h3 className="mb-3 text-sm font-semibold text-slate-900">
                  Informasi Customer
                </h3>

                <div className="grid gap-4 sm:grid-cols-2">

                  <DetailItem
                    label="Industri"
                    value={detailQuery.data.industry}
                  />

                  <DetailItem
                    label="Kota"
                    value={detailQuery.data.city}
                  />

                  <DetailItem
                    label="PIC"
                    value={detailQuery.data.pic_name}
                  />

                  <DetailItem
                    label="Sales"
                    value={detailQuery.data.sales_name}
                  />

                  <DetailItem
                    label="Telepon"
                    value={detailQuery.data.phone}
                  />

                  <DetailItem
                    label="Email"
                    value={detailQuery.data.email}
                  />

                </div>

              </div>

              {/* ADDRESS */}

              <div>

                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  Alamat
                </h3>

                <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600">
                  {detailQuery.data.address || "—"}
                </div>

              </div>

              {/* NOTES */}

              <div>

                <h3 className="mb-2 text-sm font-semibold text-slate-900">
                  Notes
                </h3>

                <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600 whitespace-pre-wrap">
                  {detailQuery.data.notes || "—"}
                </div>

              </div>

              {/* CONTACTS */}

              <div>

                <div className="mb-3 flex items-center justify-between">

                  <h3 className="text-sm font-semibold text-slate-900">
                    Contacts
                  </h3>

                  <span className="text-xs text-slate-400">
                    {contactsQuery.data?.length ?? 0} contact
                  </span>

                </div>

                {contactsQuery.isLoading ? (

                  <div className="rounded-lg border border-slate-200 p-4 text-center text-sm text-slate-400">
                    Memuat contacts...
                  </div>

                ) : contactsQuery.data?.length ? (

                  <div className="space-y-2">

                    {contactsQuery.data.map(
                      (contact, index) => {

                        const contactData =
                          contact as Contact & {
                            name?: string;
                            email?: string;
                            phone?: string;
                            position?: string;
                          };

                        return (
                          <div
                            key={
                              (contact as any).id ??
                              index
                            }
                            className="rounded-lg border border-slate-200 bg-white p-4"
                          >

                            <div className="font-medium text-slate-900">
                              {contactData.name ||
                                "Contact"}
                            </div>

                            {contactData.position && (
                              <div className="text-xs text-slate-500">
                                {contactData.position}
                              </div>
                            )}

                            {contactData.email && (
                              <div className="mt-2 text-sm text-slate-600">
                                Email:{" "}
                                {contactData.email}
                              </div>
                            )}

                            {contactData.phone && (
                              <div className="text-sm text-slate-600">
                                Telepon:{" "}
                                {contactData.phone}
                              </div>
                            )}

                          </div>
                        );
                      }
                    )}

                  </div>

                ) : (

                  <div className="rounded-lg border border-dashed border-slate-300 p-5 text-center text-sm text-slate-400">
                    Belum ada contact untuk customer ini.
                  </div>

                )}

              </div>

              {/* CLOSE */}

              <div className="flex justify-end border-t border-slate-200 pt-4">

                <Button
                  type="button"
                  variant="outline"
                  onClick={closeDetail}
                >
                  <X className="mr-2 size-4" />
                  Tutup
                </Button>

              </div>

            </div>

          ) : (

            <div className="py-10 text-center text-slate-400">
              Data customer tidak ditemukan.
            </div>

          )}

        </Modal>

      )}

      {/* =====================================================
          EDIT CUSTOMER MODAL
      ===================================================== */}

      {editModal && (
        <Modal
          title="Edit Customer"
          onClose={() => {
            setEditModal(false);
            setSelectedCustomerId(null);
          }}
        >
          {detailQuery.isLoading ? (
            <div className="py-10 text-center text-slate-500">
              Memuat data customer...
            </div>
          ) : detailQuery.isError || !detailQuery.data ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              Gagal mengambil data customer.
            </div>
          ) : (
            <form
              className="grid gap-4 sm:grid-cols-2"
              onSubmit={(e) => {
                e.preventDefault();
                updateCustomer.mutate();
              }}
              data-testid="customer-edit-form"
            >
              <Field label="Nama Customer" required>
                <Input
                  value={form.name}
                  onChange={(e) =>
                    setForm({ ...form, name: e.target.value })
                  }
                  data-testid="customer-edit-name-input"
                />
              </Field>

              <Field label="Perusahaan">
                <Input
                  value={form.company_name}
                  onChange={(e) =>
                    setForm({ ...form, company_name: e.target.value })
                  }
                  data-testid="customer-edit-company-input"
                />
              </Field>

              <Field label="Industri">
                <select
                  className={selectClass}
                  value={form.industry}
                  onChange={(e) =>
                    setForm({ ...form, industry: e.target.value })
                  }
                >
                  <option>Manufacturing</option>
                  <option>Oil & Gas</option>
                  <option>Mining</option>
                  <option>Otomotif</option>
                  <option>FMCG</option>
                  <option>Telekomunikasi</option>
                  <option>Konstruksi</option>
                  <option>EPC</option>
                  <option>Power Generation</option>
                </select>
              </Field>

              <Field label="Sumber">
                <select
                  className={selectClass}
                  value={form.source}
                  onChange={(e) =>
                    setForm({ ...form, source: e.target.value })
                  }
                >
                  <option>Referral</option>
                  <option>Website</option>
                  <option>Pameran</option>
                  <option>Cold Call</option>
                  <option>Partner</option>
                </select>
              </Field>

              <Field label="Kota">
                <Input
                  value={form.city}
                  onChange={(e) =>
                    setForm({ ...form, city: e.target.value })
                  }
                />
              </Field>

              <Field label="Provinsi">
                <Input
                  value={form.province}
                  onChange={(e) =>
                    setForm({ ...form, province: e.target.value })
                  }
                />
              </Field>

              <Field label="Telepon">
                <Input
                  value={form.phone}
                  onChange={(e) =>
                    setForm({ ...form, phone: e.target.value })
                  }
                />
              </Field>

              <Field label="Email">
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) =>
                    setForm({ ...form, email: e.target.value })
                  }
                />
              </Field>

              <Field label="Nama PIC">
                <Input
                  value={form.pic_name}
                  onChange={(e) =>
                    setForm({ ...form, pic_name: e.target.value })
                  }
                />
              </Field>

              <Field label="Jabatan PIC">
                <Input
                  value={form.pic_position}
                  onChange={(e) =>
                    setForm({ ...form, pic_position: e.target.value })
                  }
                />
              </Field>

              <Field label="Status">
                <select
                  className={selectClass}
                  value={form.status}
                  onChange={(e) =>
                    setForm({ ...form, status: e.target.value })
                  }
                >
                  <option>Active</option>
                  <option>Prospect</option>
                  <option>Inactive</option>
                </select>
              </Field>

              <Field label="Sales Penanggung Jawab">
                <select
                  className={selectClass}
                  value={form.sales_id}
                  onChange={(e) => {
                    const selected = salesOptionsQuery.data?.find(
                      (sales) => sales.id === e.target.value,
                    );
                    setForm({
                      ...form,
                      sales_id: e.target.value,
                      sales_name: selected?.name ?? "",
                    });
                  }}
                >
                  <option value="">— Pilih sales —</option>
                  {salesOptionsQuery.data?.map((sales) => (
                    <option key={sales.id} value={sales.id}>
                      {sales.name}
                    </option>
                  ))}
                </select>
              </Field>

              <div className="sm:col-span-2">
                <Field label="Alamat">
                  <Textarea
                    value={form.address}
                    onChange={(e) =>
                      setForm({ ...form, address: e.target.value })
                    }
                  />
                </Field>
              </div>

              <div className="sm:col-span-2">
                <Field label="Catatan">
                  <Textarea
                    value={form.notes}
                    onChange={(e) =>
                      setForm({ ...form, notes: e.target.value })
                    }
                  />
                </Field>
              </div>

              <div className="flex justify-end gap-2 border-t border-slate-200 pt-4 sm:col-span-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setEditModal(false);
                    setSelectedCustomerId(null);
                  }}
                  disabled={updateCustomer.isPending}
                >
                  Batal
                </Button>

                <Button
                  type="submit"
                  disabled={updateCustomer.isPending}
                  data-testid="customer-edit-save-button"
                >
                  {updateCustomer.isPending ? "Menyimpan..." : "Simpan Perubahan"}
                </Button>
              </div>
            </form>
          )}
        </Modal>
      )}

      {/* =====================================================
          ADD CUSTOMER MODAL
      ===================================================== */}

      {modal && (

        <Modal
          title="Tambah Customer"
          onClose={() => setModal(false)}
        >
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
            data-testid="customer-create-form"
          >
            <Field label="Nama Customer" required>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                data-testid="customer-name-input"
              />
            </Field>

            <Field label="Perusahaan">
              <Input
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                data-testid="customer-company-input"
              />
            </Field>

            <Field label="Industri">
              <select
                className={selectClass}
                value={form.industry}
                onChange={(e) => setForm({ ...form, industry: e.target.value })}
                data-testid="customer-industry-input"
              >
                <option>Manufacturing</option>
                <option>Oil & Gas</option>
                <option>Mining</option>
                <option>Otomotif</option>
                <option>FMCG</option>
                <option>Telekomunikasi</option>
                <option>Konstruksi</option>
                <option>EPC</option>
                <option>Power Generation</option>
              </select>
            </Field>

            <Field label="Sumber">
              <select
                className={selectClass}
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
                data-testid="customer-source-input"
              >
                <option>Referral</option>
                <option>Website</option>
                <option>Pameran</option>
                <option>Cold Call</option>
                <option>Partner</option>
              </select>
            </Field>

            <Field label="Kota">
              <Input
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                data-testid="customer-city-input"
              />
            </Field>

            <Field label="Provinsi">
              <Input
                value={form.province}
                onChange={(e) => setForm({ ...form, province: e.target.value })}
                data-testid="customer-province-input"
              />
            </Field>

            <Field label="Telepon">
              <Input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                data-testid="customer-phone-input"
              />
            </Field>

            <Field label="Email">
              <Input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                data-testid="customer-email-input"
              />
            </Field>

            <Field label="Nama PIC">
              <Input
                value={form.pic_name}
                onChange={(e) => setForm({ ...form, pic_name: e.target.value })}
                data-testid="customer-pic-input"
              />
            </Field>

            <Field label="Jabatan PIC">
              <Input
                value={form.pic_position}
                onChange={(e) => setForm({ ...form, pic_position: e.target.value })}
                data-testid="customer-pic-position-input"
              />
            </Field>

            <Field label="Status">
              <select
                className={selectClass}
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                data-testid="customer-status-input"
              >
                <option>Active</option>
                <option>Prospect</option>
                <option>Inactive</option>
              </select>
            </Field>

            <Field label="Sales Penanggung Jawab">
              <select
                className={selectClass}
                value={form.sales_id}
                  onChange={(e) => {
                    const selected = salesOptionsQuery.data?.find(
                      (sales) => sales.id === e.target.value,
                    );
                    setForm({
                      ...form,
                      sales_id: e.target.value,
                      sales_name: selected?.name ?? "",
                    });
                  }}
                data-testid="customer-sales-input"
              >
                <option value="">— Pilih sales —</option>
                {salesOptionsQuery.data?.map((sales) => (
                    <option key={sales.id} value={sales.id}>
                      {sales.name}
                    </option>
                  ))}
              </select>
            </Field>

            <div className="sm:col-span-2">
              <Field label="Alamat">
                <Textarea
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  data-testid="customer-address-input"
                />
              </Field>
            </div>

            <div className="sm:col-span-2">
              <Field label="Catatan">
                <Textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  data-testid="customer-notes-input"
                />
              </Field>
            </div>

            <div className="flex justify-end gap-2 sm:col-span-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setModal(false)}
                data-testid="customer-cancel-button"
              >
                Batal
              </Button>
              <Button
                type="submit"
                disabled={create.isPending}
                data-testid="customer-save-button"
              >
                {create.isPending ? "Menyimpan..." : "Simpan"}
              </Button>
            </div>
          </form>
        </Modal>

      )}

    </div>
  );
}


/* =========================================================
   DETAIL ITEM COMPONENT
========================================================= */

function DetailItem({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">