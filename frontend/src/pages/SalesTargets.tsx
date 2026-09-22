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
  owner_role?: string;
  sales_status?: string;
  year: number;
  target: number;
};

type UserOption = { id: string; name: string; role: string };
type TargetMember = { id: string; name: string; role: string; target: number };
type ManagerSummary = {
  id: string;
  name: string;
  personal_target: number;
  team_target: number;
  members: TargetMember[];
};
type ManagerTargetSummary = {
  year: number;
  personal_target: number;
  team_target: number;
  manager: { id: string; name: string; role: string };
  members: TargetMember[];
};
type ManagementTargetSummary = {
  year: number;
  managers: ManagerSummary[];
};
type TargetSummary = ManagerTargetSummary | ManagementTargetSummary;

const money = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(Number(value || 0));

export default function SalesTargets() {
  const qc = useQueryClient();
  const [modal, setModal] = useState(false);
  const [viewing, setViewing] = useState<SalesTarget | null>(null);
  const [editing, setEditing] = useState<SalesTarget | null>(null);
  const [yearFilter, setYearFilter] = useState(String(new Date().getFullYear()));
  const [search, setSearch] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedManagerId, setSelectedManagerId] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [form, setForm] = useState({ sales_id: "", year: String(new Date().getFullYear()), target: "" });

  const targets = useQuery({ queryKey: ["sales-targets"], queryFn: () => apiGet<SalesTarget[]>("/sales-targets") });
  const userOptions = useQuery({ queryKey: ["sales-target-options"], queryFn: () => apiGet<UserOption[]>("/sales-targets/options"), staleTime: 60_000 });
  const summary = useQuery({ queryKey: ["sales-target-summary", yearFilter], queryFn: () => apiGet<TargetSummary>(`/sales-targets/summary?year=${yearFilter}`), staleTime: 30_000 });
  const users = userOptions.data ?? [];

  const visibleTargets = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return (targets.data ?? []).filter(item => {
      const matchesYear = !yearFilter || String(item.year) === yearFilter;
      const matchesSearch = !keyword || item.sales_name.toLowerCase().includes(keyword);
      const matchesUser = !userFilter || item.sales_id === userFilter;
      const matchesRole = !roleFilter || (item.owner_role ?? "SALES") === roleFilter;
      const matchesStatus = !statusFilter || (item.sales_status ?? "Active") === statusFilter;
      return matchesYear && matchesSearch && matchesUser && matchesRole && matchesStatus;
    });
  }, [targets.data, yearFilter, search, userFilter, roleFilter, statusFilter]);

  const pagedTargets = useMemo(() => visibleTargets.slice((page - 1) * pageSize, page * pageSize), [visibleTargets, page, pageSize]);

  const save = useMutation({
    mutationFn: () => {
      const payload = { sales_id: form.sales_id, year: Number(form.year), target: Number(form.target || 0) };
      return editing ? apiPut<SalesTarget>(`/sales-targets/${editing.id}`, payload) : apiPost<SalesTarget>("/sales-targets", payload);
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sales-targets"] }); qc.invalidateQueries({ queryKey: ["sales-target-summary"] }); setModal(false); setEditing(null); toast.success("Target berhasil disimpan"); },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "Target gagal disimpan"),
  });
  const remove = useMutation({
    mutationFn: (id: string) => apiDelete(`/sales-targets/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sales-targets"] }); qc.invalidateQueries({ queryKey: ["sales-target-summary"] }); toast.success("Target berhasil dihapus"); },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "Target gagal dihapus"),
  });

  const openCreate = () => { setViewing(null); setEditing(null); setForm({ sales_id: users[0]?.id ?? "", year: yearFilter || String(new Date().getFullYear()), target: "" }); setModal(true); };
  const openView = (item: SalesTarget) => { setModal(false); setEditing(null); setViewing(item); };
  const openEdit = (item: SalesTarget) => { setViewing(null); setEditing(item); setForm({ sales_id: item.sales_id, year: String(item.year), target: String(item.target) }); setModal(true); };
  const handleDelete = (item: SalesTarget) => { if (window.confirm(`Hapus target ${item.sales_name} tahun ${item.year}?`)) remove.mutate(item.id); };
  const totalTarget = visibleTargets.reduce((sum, item) => sum + Number(item.target || 0), 0);
  const isManagerView = Boolean(summary.data && "manager" in summary.data);
  const isManagementView = Boolean(summary.data && "managers" in summary.data);
  const managerSummary = isManagerView ? summary.data as ManagerTargetSummary : null;
  const managementSummary = isManagementView ? summary.data as ManagementTargetSummary : null;
  const selectedManager = useMemo(() => managementSummary?.managers.find(manager => manager.id === selectedManagerId) ?? null, [managementSummary, selectedManagerId]);

  return (
    <div data-testid="sales-targets-page">
      <PageHeader title="Target Sales" description="Target personal Sales dan Sales Manager; Team Target Manager adalah penjumlahan target personal Manager dan Sales di bawahnya." action={{ label: "Tambah / Set Target", onClick: openCreate }} onRefresh={() => window.location.reload()} />

      {managerSummary && (
        <div className="mb-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3" data-testid="manager-target-summary">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Personal Target Manager</div><div className="mt-2 font-mono text-xl font-semibold text-slate-900">{money(managerSummary.personal_target)}</div></div>
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Team Target</div><div className="mt-2 font-mono text-xl font-semibold text-blue-700">{money(managerSummary.team_target)}</div></div>
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Anggota Team</div><div className="mt-2 font-mono text-xl font-semibold text-slate-900">{managerSummary.members.filter(item => item.role === "SALES").length} Sales</div></div>
        </div>
      )}

      {managementSummary && (
        <section className="mb-5 rounded-lg border border-slate-200 bg-white p-4 shadow-sm" data-testid="management-target-summary">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="font-heading text-sm font-semibold text-slate-900">Target Personal & Target Tim Sales Manager</h2>
              <p className="text-xs text-slate-500">Pilih Sales Manager untuk melihat target personal, target tim, dan target masing-masing Sales.</p>
            </div>
            <div className="w-full md:w-72">
              <label htmlFor="management-manager-filter" className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-500">Sales Manager</label>
              <select id="management-manager-filter" className={selectClass + " h-10 w-full"} value={selectedManagerId} onChange={e => setSelectedManagerId(e.target.value)} data-testid="management-manager-filter">
                <option value="">— Pilih Sales Manager —</option>
                {managementSummary.managers.map(manager => <option key={manager.id} value={manager.id}>{manager.name}</option>)}
              </select>
            </div>
          </div>
          {!selectedManager ? (
            <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">Silakan pilih Sales Manager untuk melihat detail target.</div>
          ) : (
            <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4" data-testid={`manager-target-card-${selectedManager.id}`}>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-900">{selectedManager.name}</div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Sales Manager</div>
                </div>
                <div className="text-xs text-slate-500">{selectedManager.members.filter(item => item.role === "SALES").length} Sales dalam team</div>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Target Personal</div>
                  <div className="mt-2 font-mono text-xl font-semibold text-slate-900">{money(selectedManager.personal_target)}</div>
                  <div className="mt-1 text-xs text-slate-500">Target pribadi {selectedManager.name}</div>
                </div>
                <div className="rounded-lg border border-blue-100 bg-blue-50/60 p-4">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-blue-600">Target Tim</div>
                  <div className="mt-2 font-mono text-xl font-semibold text-blue-700">{money(selectedManager.team_target)}</div>
                  <div className="mt-1 text-xs text-slate-500">Manager + seluruh Sales dalam team</div>
                </div>
              </div>
              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {selectedManager.members.map(member => (
                  <div key={member.id} className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="text-xs font-medium text-slate-700">{member.name}</div>
                    <div className="mt-1 text-[10px] uppercase tracking-wider text-slate-400">{member.role === "SALES_MANAGER" ? "Personal Manager" : "Personal Sales"}</div>
                    <div className="mt-2 font-mono text-sm font-semibold text-slate-900">{money(member.target)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <div className="crm-filter-grid mb-5">
        <div className="relative w-full"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Cari nama user..." className="h-10 w-full pl-9" data-testid="sales-target-search-input" /></div>
        <select className={selectClass + " h-10"} value={userFilter} onChange={e => { setUserFilter(e.target.value); setPage(1); }} data-testid="sales-target-user-filter"><option value="">Semua user</option>{users.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <select className={selectClass + " h-10"} value={roleFilter} onChange={e => { setRoleFilter(e.target.value); setPage(1); }} data-testid="sales-target-role-filter"><option value="">Semua peran</option><option value="SALES_MANAGER">Sales Manager</option><option value="SALES">Sales</option></select>
        <select className={selectClass + " h-10"} value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} data-testid="sales-target-status-filter"><option value="">Semua status</option><option value="Active">Active</option><option value="Inactive">Inactive</option></select>
        <div className="flex h-10 items-center gap-2"><span className="shrink-0 text-[11px] font-medium uppercase tracking-wide text-slate-500">Tahun</span><select className={selectClass + " h-10 flex-1"} value={yearFilter} onChange={e => { setYearFilter(e.target.value); setPage(1); }} data-testid="sales-target-year-filter">{[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(year => <option key={year} value={year}>{year}</option>)}</select></div>
      </div>

      <div className="mb-5 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Total Target {yearFilter}</div><div className="mt-2 font-mono text-xl font-semibold text-slate-900">{money(totalTarget)}</div></div>

      {managerSummary && (
        <div className="mb-5 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"><div className="mb-3"><h2 className="font-heading text-sm font-semibold text-slate-900">Target Personal & Team</h2><p className="text-xs text-slate-500">Team Target = Personal Target Manager + seluruh target personal Sales.</p></div><div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{managerSummary.members.map(item => <div key={item.id} className="rounded-lg bg-slate-50 p-3"><div className="text-xs font-medium text-slate-600">{item.name}</div><div className="mt-1 text-[10px] uppercase tracking-wider text-slate-400">{item.role === "SALES_MANAGER" ? "Personal Manager" : "Personal Sales"}</div><div className="mt-2 font-mono text-sm font-semibold text-slate-900">{money(item.target)}</div></div>)}</div></div>
      )}

      <DataTable testId="sales-targets-table" items={pagedTargets} loading={targets.isLoading} total={visibleTargets.length} page={page} pageSize={pageSize} onPage={setPage} onPageSize={size => { setPageSize(size); setPage(1); }} columns={[
        { key: "sales", label: "User", render: i => <span className="font-medium">{i.sales_name}</span> },
        { key: "role", label: "Peran", render: i => i.owner_role === "SALES_MANAGER" ? "Sales Manager" : "Sales" },
        { key: "year", label: "Tahun", render: i => i.year },
        { key: "target", label: "Target Personal", render: i => <span className="font-mono font-semibold">{money(i.target)}</span> },
        { key: "status", label: "Status", render: i => i.sales_status ?? "Active" },
        { key: "action", label: "Aksi", render: i => <div className="flex items-center gap-2"><Button type="button" size="icon" variant="ghost" className="size-8 text-blue-600 hover:text-blue-700" onClick={() => openView(i)} title="View" aria-label={`View target ${i.sales_name}`}><Eye className="size-4" /></Button><Button type="button" size="icon" variant="ghost" className="size-8 text-slate-600 hover:text-slate-900" onClick={() => openEdit(i)} title="Edit" aria-label={`Edit target ${i.sales_name}`}><Pencil className="size-4" /></Button><Button type="button" size="icon" variant="ghost" className="size-8 text-red-600 hover:text-red-700" onClick={() => handleDelete(i)} disabled={remove.isPending} title="Delete" aria-label={`Delete target ${i.sales_name}`}><Trash2 className="size-4" /></Button></div> },
      ]} />
      {viewing && <Modal title="Detail Target" onClose={() => setViewing(null)}><div className="grid gap-4 sm:grid-cols-2"><Field label="User"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">{viewing.sales_name}</div></Field><Field label="Peran"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">{viewing.owner_role === "SALES_MANAGER" ? "Sales Manager" : "Sales"}</div></Field><Field label="Status"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">{viewing.sales_status ?? "Active"}</div></Field><Field label="Tahun"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">{viewing.year}</div></Field><Field label="Target Personal"><div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm font-semibold">{money(viewing.target)}</div></Field></div></Modal>}
      {modal && <Modal title={editing ? "Edit Target Personal" : "Set Target Personal"} onClose={() => { setModal(false); setEditing(null); }}><form className="grid gap-4 sm:grid-cols-2" onSubmit={e => { e.preventDefault(); save.mutate(); }} data-testid="sales-target-form"><Field label="User" required><select className={selectClass} value={form.sales_id} onChange={e => setForm({ ...form, sales_id: e.target.value })} data-testid="sales-target-user-input"><option value="">— Pilih User —</option>{users.map(user => <option key={user.id} value={user.id}>{user.name} — {user.role === "SALES_MANAGER" ? "Sales Manager" : "Sales"}</option>)}</select></Field><Field label="Tahun" required><Input type="number" min="2000" max="2100" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} data-testid="sales-target-year-input" /></Field><Field label="Target Personal (IDR)" required><Input type="number" min="0" step="1000000" value={form.target} onChange={e => setForm({ ...form, target: e.target.value })} placeholder="Contoh: 1000000000" data-testid="sales-target-value-input" /></Field><div className="rounded-md bg-slate-50 p-3 text-xs text-slate-500 sm:col-span-2">Untuk Sales Manager, <strong>Team Target</strong> otomatis dihitung dari Target Personal Manager + seluruh Target Personal Sales di bawahnya.</div><div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="outline" onClick={() => { setModal(false); setEditing(null); }}>Batal</Button><Button type="submit" disabled={save.isPending || !form.sales_id || !form.target}>Simpan</Button></div></form></Modal>}
    </div>
  );
}
