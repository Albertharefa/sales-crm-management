import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@/lib/api";
import type { Customer, Opportunity, Options, Paginated } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { Search, List, KanbanSquare, Pencil, Trash2 } from "lucide-react";
import PaginationControls from "@/components/PaginationControls";

const money = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);

const stages = ["Lead", "Qualification", "Proposal", "Negotiation", "Won", "Lost"];

const emptyForm = {
  name: "",
  customer_id: "",
  sales_id: "",
  value: "",
  probability: "50",
  stage: "Lead",
  target_close: "",
  next_action: "",
  description: "",
  loss_reason: "",
};

export default function Pipeline() {
  const [view, setView] = useState<"table" | "kanban">("table");
  const [modal, setModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [editingOpportunity, setEditingOpportunity] = useState<Opportunity | null>(null);
  const [search, setSearch] = useState("");
  const [stage, setStage] = useState("");
  const [salesId, setSalesId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [lossModal, setLossModal] = useState(false);
  const [lossReason, setLossReason] = useState("");
  const [pendingLostOpportunity, setPendingLostOpportunity] = useState<Opportunity | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [form, setForm] = useState({ ...emptyForm });
  const [editForm, setEditForm] = useState({ ...emptyForm });

  const qc = useQueryClient();

  const queryParams = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (search.trim()) queryParams.set("search", search.trim());
  if (stage) queryParams.set("stage", stage);
  if (salesId) queryParams.set("sales_id", salesId);
  if (customerId) queryParams.set("customer_id", customerId);

  const list = useQuery({
    queryKey: ["pipeline", page, pageSize, search, stage, salesId, customerId],
    queryFn: () => apiGet<Paginated<Opportunity>>(`/pipeline?${queryParams.toString()}`),
  });

  const options = useQuery({
    queryKey: ["options"],
    queryFn: () => apiGet<Options>("/options"),
  });

  const salesOptions = useQuery({
    queryKey: ["pipeline-sales-options"],
    queryFn: () => apiGet<{ id: string; name: string; role: string }[]>("/pipeline/sales-options"),
    staleTime: 60_000,
  });

  const customerOptions = useQuery({
    queryKey: ["pipeline-customer-options"],
    queryFn: () => apiGet<{ id: string; name: string }[]>("/pipeline/customer-options"),
    staleTime: 60_000,
  });

  const refreshPage = async () => {
    await Promise.all([
      list.refetch(),
      options.refetch(),
      salesOptions.refetch(),
      customerOptions.refetch(),
    ]);
    toast.success("Sales Pipeline berhasil diperbarui");
  };

  const create = useMutation({
    mutationFn: () =>
      apiPost<Opportunity>("/pipeline", {
        ...form,
        value: Number(form.value),
        probability: Number(form.probability),
        sales_id: form.sales_id || null,
        target_close: form.target_close || null,
        loss_reason: form.stage === "Lost" ? form.loss_reason.trim() || null : null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      setModal(false);
      setForm({ ...emptyForm });
      toast.success("Opportunity berhasil dibuat");
    },
    onError: () => toast.error("Opportunity gagal disimpan"),
  });

  const update = useMutation({
    mutationFn: () => {
      if (!editingOpportunity) throw new Error("Opportunity tidak dipilih");
      return apiPut<Opportunity>(`/pipeline/${editingOpportunity.id}`, {
        name: editForm.name.trim(),
        customer_id: editForm.customer_id,
        sales_id: editForm.sales_id || null,
        value: Number(editForm.value),
        probability: Number(editForm.probability),
        stage: editForm.stage,
        target_close: editForm.target_close || null,
        next_action: editForm.next_action.trim() || null,
        description: editForm.description.trim() || null,
        loss_reason: editForm.stage === "Lost" ? editForm.loss_reason.trim() || null : null,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      setEditModal(false);
      setEditingOpportunity(null);
      toast.success("Opportunity berhasil diperbarui");
    },
    onError: () => toast.error("Opportunity gagal diperbarui"),
  });

  const remove = useMutation({
    mutationFn: (item: Opportunity) => apiDelete<{ message: string; id: string }>(`/pipeline/${item.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      toast.success("Opportunity berhasil dihapus");
    },
    onError: () => toast.error("Opportunity gagal dihapus"),
  });

  const changeStage = useMutation({
    mutationFn: ({
      id,
      nextStage,
      lossReason,
    }: {
      id: string;
      nextStage: string;
      lossReason?: string;
    }) => {
      const params = new URLSearchParams({ stage: nextStage });
      if (nextStage === "Lost" && lossReason?.trim()) {
        params.set("loss_reason", lossReason.trim());
      }
      return apiPatch<Opportunity>(`/pipeline/${id}/stage?${params.toString()}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      setLossModal(false);
      setLossReason("");
      setPendingLostOpportunity(null);
      toast.success("Stage opportunity diperbarui");
    },
    onError: () => toast.error("Stage gagal diperbarui"),
  });

  const handleStageChange = (item: Opportunity, nextStage: string) => {
    if (nextStage === "Lost") {
      setPendingLostOpportunity(item);
      setLossReason(item.loss_reason ?? "");
      setLossModal(true);
      return;
    }

    changeStage.mutate({ id: item.id, nextStage });
  };

  const confirmLostStage = () => {
    if (!pendingLostOpportunity) return;
    if (!lossReason.trim()) {
      toast.error("Alasan Lost wajib diisi");
      return;
    }
    changeStage.mutate({
      id: pendingLostOpportunity.id,
      nextStage: "Lost",
      lossReason,
    });
  };

  const openEdit = (item: Opportunity) => {
    setEditingOpportunity(item);
    setEditForm({
      name: item.name ?? "",
      customer_id: item.customer_id ?? "",
      sales_id: item.sales_id ?? "",
      value: String(item.value ?? 0),
      probability: String(item.probability ?? 0),
      stage: item.stage ?? "Lead",
      target_close: item.target_close ?? "",
      next_action: item.next_action ?? "",
      description: item.description ?? "",
      loss_reason: item.loss_reason ?? "",
    });
    setEditModal(true);
  };

  const confirmDelete = (item: Opportunity) => {
    if (remove.isPending) return;
    const confirmed = window.confirm(`Hapus opportunity "${item.name}"? Data yang dihapus tidak dapat dikembalikan.`);
    if (confirmed) remove.mutate(item);
  };

  const items = list.data?.items ?? [];

  const metrics = useMemo(() => {
    const openItems = items.filter((item) => !["Won", "Lost"].includes(item.stage));
    return {
      open: openItems.reduce((sum, item) => sum + Number(item.value || 0), 0),
      weighted: openItems.reduce(
        (sum, item) => sum + Number(item.value || 0) * Number(item.probability || 0) / 100,
        0,
      ),
      won: items
        .filter((item) => item.stage === "Won")
        .reduce((sum, item) => sum + Number(item.value || 0), 0),
      active: openItems.length,
    };
  }, [items]);

  const resetFilters = () => {
    setSearch("");
    setStage("");
    setSalesId("");
    setCustomerId("");
    setPage(1);
  };

  const submitCreate = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.name.trim() || !form.customer_id || !form.value) {
      toast.error("Opportunity, Customer, dan Value wajib diisi");
      return;
    }
    if (form.stage === "Lost" && !form.loss_reason.trim()) {
      toast.error("Alasan Lost wajib diisi");
      return;
    }
    create.mutate();
  };

  const submitEdit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!editForm.name.trim() || !editForm.customer_id || !editForm.value) {
      toast.error("Opportunity, Customer, dan Value wajib diisi");
      return;
    }
    if (editForm.stage === "Lost" && !editForm.loss_reason.trim()) {
      toast.error("Alasan Lost wajib diisi");
      return;
    }
    update.mutate();
  };

  return (
    <div data-testid="pipeline-page">
      <PageHeader
        title="Sales Pipeline"
        description="Weighted value = value × probability, dihitung di server"
        onRefresh={refreshPage}
        action={{ label: "Opportunity", onClick: () => { setForm({ ...emptyForm }); setModal(true); } }}
        onExport={() => window.open("/api/v1/exports/pipeline", "_blank")}
      />

      <div className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ["OPEN PIPELINE", money(metrics.open)],
          ["WEIGHTED PIPELINE", money(metrics.weighted)],
          ["WON VALUE", money(metrics.won)],
          ["DEAL AKTIF", String(metrics.active)],
        ].map(([label, value]) => (
          <Card key={label} className="border-slate-200 shadow-none">
            <CardContent className="p-5">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
              <div className="mt-8 font-mono text-2xl font-semibold text-slate-900">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mb-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <Button variant={view === "table" ? "default" : "outline"} size="sm" onClick={() => setView("table")} data-testid="pipeline-table-view-button">
            <List className="mr-2 size-4" />Table
          </Button>
          <Button variant={view === "kanban" ? "default" : "outline"} size="sm" onClick={() => setView("kanban")} data-testid="pipeline-kanban-view-button">
            <KanbanSquare className="mr-2 size-4" />Kanban
          </Button>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input className="pl-9" placeholder="Cari opportunity / customer..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} data-testid="pipeline-search-input" />
          </div>

          <select className={selectClass} value={stage} onChange={(e) => { setStage(e.target.value); setPage(1); }} data-testid="pipeline-stage-filter">
            <option value="">Semua stage</option>
            {stages.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>

          <select className={selectClass} value={salesId} onChange={(e) => { setSalesId(e.target.value); setPage(1); }} data-testid="pipeline-sales-filter">
            <option value="">Semua sales</option>
            {(salesOptions.data ?? []).map((user) => <option key={user.id} value={user.id}>{user.name}</option>)}
          </select>

          <select className={selectClass} value={customerId} onChange={(e) => { setCustomerId(e.target.value); setPage(1); }} data-testid="pipeline-customer-filter">
            <option value="">Semua customer</option>
            {(customerOptions.data ?? []).map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}
          </select>
        </div>

        {(search || stage || salesId || customerId) && (
          <div className="mt-3 flex justify-end">
            <Button variant="ghost" size="sm" onClick={resetFilters}>Reset filter</Button>
          </div>
        )}
      </div>

      {list.isLoading ? (
        <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-400">Memuat pipeline...</div>
      ) : list.isError ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-600">Gagal memuat Sales Pipeline. Silakan refresh.</div>
      ) : view === "table" ? (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1250px] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">No</th>
                  {["Opportunity", "Customer", "Sales", "Value", "Prob.", "Weighted", "Stage", "Target Close", "Aksi"].map((head) => <th key={head} className="px-4 py-3 font-semibold">{head}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item, index) => (
                  <tr key={item.id} className="hover:bg-slate-50" data-testid={`opportunity-row-${item.opportunity_id}`}>
                    <td className="px-4 py-3 text-slate-500">{(page - 1) * pageSize + index + 1}</td>
                    <td className="px-4 py-3"><div className="font-medium text-slate-800">{item.name}</div><div className="font-mono text-[10px] text-slate-400">{item.opportunity_id}</div></td>
                    <td className="px-4 py-3 text-slate-600">{item.customer_name}</td>
                    <td className="px-4 py-3 text-slate-600">{item.sales_name ?? "—"}</td>
                    <td className="px-4 py-3 font-mono text-xs">{money(item.value)}</td>
                    <td className="px-4 py-3">{item.probability}%</td>
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-800">{money(item.value * item.probability / 100)}</td>
                    <td className="px-4 py-3">
                      <select className="h-8 rounded-md border border-slate-200 bg-white px-2 text-xs" value={item.stage} onChange={(e) => handleStageChange(item, e.target.value)} disabled={changeStage.isPending} aria-label={`Stage ${item.name}`}>
                        {stages.map((itemStage) => <option key={itemStage}>{itemStage}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{item.target_close ?? "—"}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Button type="button" variant="ghost" size="icon" title="Edit Opportunity" onClick={() => openEdit(item)} disabled={update.isPending}>
                          <Pencil className="size-4" />
                        </Button>
                        <Button type="button" variant="ghost" size="icon" title="Hapus Opportunity" onClick={() => confirmDelete(item)} disabled={remove.isPending}>
                          <Trash2 className="size-4 text-red-500" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!items.length && <div className="border-t border-slate-200 p-10 text-center text-sm text-slate-400">Tidak ada opportunity yang sesuai filter.</div>}
          <PaginationControls page={page} pageSize={pageSize} total={list.data?.total ?? 0} onPage={setPage} onPageSize={(size) => { setPageSize(size); setPage(1); }} testId="pipeline" />
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((stageName) => {
            const stageItems = items.filter((item) => item.stage === stageName);
            return (
              <div key={stageName} className="min-w-[220px] flex-1 rounded-xl border border-slate-200 bg-slate-100/80 p-3" data-testid={`pipeline-kanban-column-${stageName.toLowerCase()}`}>
                <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold">{stageName}</h3><Badge variant="default" className="min-w-5 bg-blue-600 text-white">{stageItems.length}</Badge></div>
                <div className="space-y-3">
                  {stageItems.map((item) => (
                    <Card key={item.id} className="border-slate-200 bg-white">
                      <CardContent className="p-4">
                        <div className="text-sm font-semibold">{item.name}</div>
                        <div className="mt-1 text-xs text-slate-500">{item.customer_name}</div>
                        <div className="mt-3 text-xs text-slate-500">{item.sales_name ?? "—"}</div>
                        <div className="mt-4 flex items-center justify-between font-mono text-xs"><span>{money(item.value)}</span><span className="text-blue-600">{item.probability}%</span></div>
                        <div className="mt-1 text-right text-[10px] text-slate-400">Weighted {money(item.value * item.probability / 100)}</div>
                        <div className="mt-3 flex gap-2">
                          <Button type="button" variant="outline" size="sm" className="flex-1" onClick={() => openEdit(item)}><Pencil className="mr-1 size-3" />Edit</Button>
                          <Button type="button" variant="outline" size="sm" onClick={() => confirmDelete(item)} disabled={remove.isPending}><Trash2 className="size-3 text-red-500" /></Button>
                        </div>
                        <select className="mt-3 h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-xs text-slate-700" value={item.stage} onChange={(e) => handleStageChange(item, e.target.value)} disabled={changeStage.isPending} aria-label={`Pindahkan ${item.name}`}>
                          {stages.map((itemStage) => <option key={itemStage} value={itemStage}>Pindah ke: {itemStage}</option>)}
                        </select>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {lossModal && (
        <Modal title="Pindahkan Opportunity ke Lost" onClose={() => { if (changeStage.isPending) return; setLossModal(false); setLossReason(""); setPendingLostOpportunity(null); }}>
          <div className="grid gap-4">
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"><div className="font-semibold">{pendingLostOpportunity?.name}</div><div className="mt-1">Customer: {pendingLostOpportunity?.customer_name ?? "—"}</div></div>
            <Field label="Alasan Lost" required><Textarea value={lossReason} onChange={(e) => setLossReason(e.target.value)} placeholder="Contoh: Customer memilih vendor lain karena harga..." rows={4} disabled={changeStage.isPending} data-testid="pipeline-loss-reason-input" /></Field>
            <div className="flex justify-end gap-2"><Button type="button" variant="outline" disabled={changeStage.isPending} onClick={() => { setLossModal(false); setLossReason(""); setPendingLostOpportunity(null); }}>Batal</Button><Button type="button" variant="destructive" disabled={changeStage.isPending || !lossReason.trim()} onClick={confirmLostStage} data-testid="pipeline-confirm-lost-button">{changeStage.isPending ? "Menyimpan..." : "Pindahkan ke Lost"}</Button></div>
          </div>
        </Modal>
      )}

      {modal && (
        <Modal title="Tambah Opportunity" onClose={() => setModal(false)} size="landscape">
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={submitCreate} data-testid="opportunity-create-form">
            <div className="sm:col-span-2"><Field label="Opportunity" required><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="opportunity-name-input" /></Field></div>
            <Field label="Customer" required><select className={selectClass} value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} data-testid="opportunity-customer-input"><option value="">— Pilih customer —</option>{(customerOptions.data ?? []).map((customer: Customer) => <option value={customer.id} key={customer.id}>{customer.name}</option>)}</select></Field>
            <Field label="Sales Penanggung Jawab"><select className={selectClass} value={form.sales_id} onChange={(e) => setForm({ ...form, sales_id: e.target.value })} data-testid="opportunity-sales-input"><option value="">— Gunakan sales login —</option>{(salesOptions.data ?? []).map((user) => <option value={user.id} key={user.id}>{user.name}</option>)}</select></Field>
            <Field label="Stage"><select className={selectClass} value={form.stage} onChange={(e) => setForm({ ...form, stage: e.target.value })} data-testid="opportunity-stage-input">{stages.map((item) => <option key={item}>{item}</option>)}</select></Field>
            <Field label="Value (Rp)" required><Input type="number" min="0" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} data-testid="opportunity-value-input" /></Field>
            <Field label="Probability (%)"><Input type="number" min="0" max="100" value={form.probability} onChange={(e) => setForm({ ...form, probability: e.target.value })} data-testid="opportunity-probability-input" /></Field>
            <Field label="Target Close"><Input type="date" value={form.target_close} onChange={(e) => setForm({ ...form, target_close: e.target.value })} data-testid="opportunity-close-input" /></Field>
            <Field label="Next Action"><Input value={form.next_action} onChange={(e) => setForm({ ...form, next_action: e.target.value })} data-testid="opportunity-next-action-input" /></Field>
            <div className="sm:col-span-2"><Field label="Description"><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field></div>
            {form.stage === "Lost" && <div className="sm:col-span-2"><Field label="Alasan Lost" required><Textarea value={form.loss_reason} onChange={(e) => setForm({ ...form, loss_reason: e.target.value })} placeholder="Alasan customer tidak jadi membeli..." /></Field></div>}
            <div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="outline" onClick={() => setModal(false)}>Batal</Button><Button type="submit" disabled={create.isPending} data-testid="opportunity-save-button">{create.isPending ? "Menyimpan..." : "Simpan"}</Button></div>
          </form>
        </Modal>
      )}

      {editModal && editingOpportunity && (
        <Modal title="Edit Opportunity" onClose={() => { if (!update.isPending) { setEditModal(false); setEditingOpportunity(null); } }} size="landscape">
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={submitEdit} data-testid="opportunity-edit-form">
            <div className="sm:col-span-2"><Field label="Opportunity" required><Input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} /></Field></div>
            <Field label="Customer" required><select className={selectClass} value={editForm.customer_id} onChange={(e) => setEditForm({ ...editForm, customer_id: e.target.value })}><option value="">— Pilih customer —</option>{(customerOptions.data ?? []).map((customer) => <option value={customer.id} key={customer.id}>{customer.name}</option>)}</select></Field>
            <Field label="Sales Penanggung Jawab"><select className={selectClass} value={editForm.sales_id} onChange={(e) => setEditForm({ ...editForm, sales_id: e.target.value })}><option value="">— Pilih sales —</option>{(salesOptions.data ?? []).map((user) => <option value={user.id} key={user.id}>{user.name}</option>)}</select></Field>
            <Field label="Stage"><select className={selectClass} value={editForm.stage} onChange={(e) => setEditForm({ ...editForm, stage: e.target.value })}>{stages.map((item) => <option key={item}>{item}</option>)}</select></Field>
            <Field label="Value (Rp)" required><Input type="number" min="0" value={editForm.value} onChange={(e) => setEditForm({ ...editForm, value: e.target.value })} /></Field>
            <Field label="Probability (%)"><Input type="number" min="0" max="100" value={editForm.probability} onChange={(e) => setEditForm({ ...editForm, probability: e.target.value })} /></Field>
            <Field label="Target Close"><Input type="date" value={editForm.target_close} onChange={(e) => setEditForm({ ...editForm, target_close: e.target.value })} /></Field>
            <Field label="Next Action"><Input value={editForm.next_action} onChange={(e) => setEditForm({ ...editForm, next_action: e.target.value })} /></Field>
            <div className="sm:col-span-2"><Field label="Description"><Textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} /></Field></div>
            {editForm.stage === "Lost" && <div className="sm:col-span-2"><Field label="Alasan Lost" required><Textarea value={editForm.loss_reason} onChange={(e) => setEditForm({ ...editForm, loss_reason: e.target.value })} placeholder="Alasan customer tidak jadi membeli..." /></Field></div>}
            <div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="outline" disabled={update.isPending} onClick={() => { setEditModal(false); setEditingOpportunity(null); }}>Batal</Button><Button type="submit" disabled={update.isPending}>{update.isPending ? "Menyimpan..." : "Simpan Perubahan"}</Button></div>
          </form>
        </Modal>
      )}
    </div>
  );
}
