import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import DataTable from "@/components/DataTable";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Search, Eye, Pencil, Trash2 } from "lucide-react";

type SalesTarget = {
  id: string;
  sales_id: string;
  sales_name: string;
  sales_status?: string;
  year: number;
  target: number;
};

type SalesOption = {
  id: string;
  name: string;
};

const money = (value: number) => new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0,
}).format(Number(value || 0));

export default function SalesTargets() {
  const qc = useQueryClient();
  const [modal, setModal] = useState(false);
  const [viewing, setViewing] = useState<SalesTarget | null>(null);
  const [editing, setEditing] = useState<SalesTarget | null>(null);
  const [yearFilter, setYearFilter] = useState(String(new Date().getFullYear()));
  const [search, setSearch] = useState("");
  const [salesFilter, setSalesFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [form, setForm] = useState({ sales_id: "", year: String(new Date().getFullYear()), target: "" });

  const targets = useQuery({
    queryKey: ["sales-targets"],
    queryFn: () => apiGet<SalesTarget[]>("/sales-targets"),
  });

  const salesOptions = useQuery({
    queryKey: ["sales-target-options"],
    queryFn: () => apiGet<SalesOption[]>("/sales-targets/options"),
    staleTime: 60_000,
  });

  const salesUsers = salesOptions.data ?? [];

  const visibleTargets = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return (targets.data ?? []).filter(item => {
      const matchesYear = !yearFilter || String(item.year) === yearFilter;
      const matchesSearch = !keyword || item.sales_name.toLowerCase().includes(keyword);
      const matchesSales = !salesFilter || item.sales_id === salesFilter;
      const matchesStatus = !statusFilter || (item.sales_status ?? "Active") === statusFilter;
      return matchesYear && matchesSearch && matchesSales && matchesStatus;
    });
  }, [targets.data, yearFilter, search, salesFilter, statusFilter]);

  const pagedTargets = useMemo(() => {
    const start = (page - 1) * pageSize;
    return visibleTargets.slice(start, start + pageSize);
  }, [visibleTargets, page, pageSize]);

  const save = useMutation({
    mutationFn: () => {
      const payload = { sales_id: form.sales_id, year: Number(form.year), target: Number(form.target || 0) };
      return editing ? apiPut<SalesTarget>(`/sales-targets/${editing.id}`, payload) : apiPost<SalesTarget>("/sales-targets", payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
      setModal(false);
      setEditing(null);
      toast.success("Target sales berhasil disimpan");
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "Target gagal disimpan"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => apiDelete(`/sales-targets/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
      toast.success("Target sales berhasil dihapus");
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "Target gagal dihapus"),
  });

  const openCreate = () => {
    setViewing(null);
    setEditing(null);
    setForm({ sales_id: salesUsers[0]?.id ?? "", year: yearFilter || String(new Date().getFullYear()), target: "" });
    setModal(true);
  };

  const openView = (item: SalesTarget) => { setModal(false); setEditing(null); setViewing(item); };
  const openEdit = (item: SalesTarget) => {
    setViewing(null);
    setEditing(item);
    setForm({ sales_id: item.sales_id, year: String(item.year), target: String(item.target) });
    setModal(true);
  };
  const handleDelete = (item: SalesTarget) => {
    if (window.confirm(`Hapus target sales ${item.sales_name} tahun ${item.year}?`)) remove.mutate(item.id);
  };
  const totalTarget = visibleTargets.reduce((sum, item) => sum + Number(item.target || 0), 0);

  return (
    <div data-testid="sales-targets-page">
      <PageHeader title="Target Sales" description="Master target tahunan per sales sebagai sumber resmi KPI Sales Team" action={{ label: "Tambah / Set Target", onClick: openCreate }} onRefresh={() => window.location.reload()} />
      <div className="crm-filter-grid mb-5">
        <div className="relative w-full"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Cari nama sales..." className="h-10 w-full pl-9" data-testid="sales-target-search-input" /></div>
        <select className={selectClass + " h-10"} value={salesFilter} onChange={e => { setSalesFilter(e.target.value); setPage(1); }} data-testid="sales-target-sales-filter"><option value="">Semua sales</option>{salesUsers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <select className={selectClass + " h-10"} value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} data-testid="sales-target-status-filter"><option value="">Semua status</option><option value="Active">Active</option><option value="Inactive">Inactive</option></select>
        <div className="flex h-10 items-center gap-2"><span className="shrink-0 text-[11px] font-medium uppercase tracking-wide text-slate-500">Tahun</span><select className={selectClass + " h-10 flex-1"} value={yearFilter} onChange={e => { setYearFilter(e.target.value); setPage(1); }} data-testid="sales-target-year-filter">{[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(year => <option key={year} value={year}>{year}</option>)}</select></div>
      </div>
      <div className="mb-5 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Total Target {yearFilter}</div><div className="mt-2 font-mono text-xl font-semibold text-slate-900">{money(totalTarget)}</div></div>
      <DataTable testId="sales-targets-table" items={pagedTargets} loading={targets.isLoading} total={visibleTargets.length} page={page} pageSize={pageSize} onPage={setPage} onPageSize={size => { setPageSize(size); setPage(1); }} columns={[
        { key: "sales", label: "Sales", render: i => <span className="font-medium">{i.sales_name}</span> },
        { key: "year", label: "Tahun", render: i => i.year },
        { key: "target", label: "Target", render: i => <span className="font-mono font-semibold">{money(i.target)}</span> },
        { key: "status", label: "Status", render: i => i.sales_status ?? "Active" },
        { key: "action", label: "Aksi", render: i => <div className="flex items-center gap-2"><Button type="button" size="icon" variant="ghost" className="size-8 text-blue-600 hover:text-blue-700" onClick={() => openView(i)} title="View" aria-label={`View target ${i.sales_name}`}><Eye className="size-4" /></Button><Button type="button" size="icon" variant="ghost" className="size-8 text-slate-600 hover:text-slate-900" onClick={() => openEdit(i)} title="Edit" aria-label={`Edit target ${i.sales_name}`}><Pencil className="size-4" /></Button><Button type="button" size="icon" variant="ghost" className="size-8 text-red-600 hover:text-red-700" onClick={() => handleDelete(i)} disabled={remove.isPending} title="Delete" aria-label={`Delete target ${i.sales_name}`}><Trash2 className="size-4" /></Button></div> },
      ]} />
      {viewing && <Modal title="Detail Target Sales" onClose={() => setViewing(null)}><div className="grid gap-4 sm:grid-cols-2"><Field label="Sales"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">{viewing.sales_name}</div></Field><Field label="Status"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">{viewing.sales_status ?? "Active"}</div></Field><Field label="Tahun"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">{viewing.year}</div></Field><Field label="Target Tahunan"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm font-semibold">{money(viewing.target)}</div></Field></div></Modal>}
      {modal && <Modal title={editing ? "Edit Target Sales" : "Set Target Sales"} onClose={() => { setModal(false); setEditing(null); }}><form className="grid gap-4 sm:grid-cols-2" onSubmit={e => { e.preventDefault(); save.mutate(); }} data-testid="sales-target-form"><Field label="Sales" required><select className={selectClass} value={form.sales_id} onChange={e => setForm({ ...form, sales_id: e.target.value })} data-testid="sales-target-sales-input"><option value="">— Pilih Sales —</option>{salesUsers.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}</select></Field><Field label="Tahun" required><Input type="number" min="2000" max="2100" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} data-testid="sales-target-year-input" /></Field><Field label="Target Tahunan (IDR)" required><Input type="number" min="0" step="1000000" value={form.target} onChange={e => setForm({ ...form, target: e.target.value })} placeholder="Contoh: 4000000000" data-testid="sales-target-value-input" /></Field><div className="rounded-md bg-slate-50 p-3 text-xs text-slate-500 sm:col-span-2">Target ini menjadi sumber perhitungan <strong>Target, Achievement, Gap, dan Coverage</strong> pada menu Sales Team & KPI.</div><div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="outline" onClick={() => { setModal(false); setEditing(null); }}>Batal</Button><Button type="submit" disabled={save.isPending || !form.sales_id || !form.target}>Simpan</Button></div></form></Modal>}
    </div>
  );
}
