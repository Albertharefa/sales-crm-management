import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import type { OptionsResponse } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import DataTable from "@/components/DataTable";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";


type SalesTarget = {
  id: string;
  sales_id: string;
  sales_name: string;
  year: number;
  target: number;
};

const money = (value: number) => new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0,
}).format(Number(value || 0));

export default function SalesTargets() {
  const qc = useQueryClient();
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<SalesTarget | null>(null);
  const [yearFilter, setYearFilter] = useState(String(new Date().getFullYear()));
  const [form, setForm] = useState({ sales_id: "", year: String(new Date().getFullYear()), target: "" });

  const targets = useQuery({
    queryKey: ["sales-targets"],
    queryFn: () => apiGet<SalesTarget[]>("/sales-targets"),
  });

  const options = useQuery({
    queryKey: ["options"],
    queryFn: () => apiGet<OptionsResponse>("/options"),
  });

  const salesUsers = useMemo(
    () => (options.data?.users ?? []).filter(user => user.role === "SALES"),
    [options.data],
  );

  const visibleTargets = useMemo(
    () => (targets.data ?? []).filter(item => !yearFilter || String(item.year) === yearFilter),
    [targets.data, yearFilter],
  );

  const save = useMutation({
    mutationFn: () => {
      const payload = {
        sales_id: form.sales_id,
        year: Number(form.year),
        target: Number(form.target || 0),
      };
      return editing
        ? apiPut<SalesTarget>(`/sales-targets/${editing.id}`, payload)
        : apiPost<SalesTarget>("/sales-targets", payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
      setModal(false);
      setEditing(null);
      toast.success("Target sales berhasil disimpan");
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "Target gagal disimpan"),
  });

  const openCreate = () => {
    setEditing(null);
    setForm({ sales_id: salesUsers[0]?.id ?? "", year: yearFilter || String(new Date().getFullYear()), target: "" });
    setModal(true);
  };

  const openEdit = (item: SalesTarget) => {
    setEditing(item);
    setForm({ sales_id: item.sales_id, year: String(item.year), target: String(item.target) });
    setModal(true);
  };

  const totalTarget = visibleTargets.reduce((sum, item) => sum + Number(item.target || 0), 0);

  return (
    <div data-testid="sales-targets-page">
      <PageHeader
        title="Target Sales"
        description="Master target tahunan per sales sebagai sumber resmi KPI Sales Team"
        action={{ label: "Tambah / Set Target", onClick: openCreate }}
        onRefresh={() => window.location.reload()}
      />

      <div className="mb-5 grid gap-3 sm:grid-cols-[220px_1fr]">
        <Field label="Tahun">
          <select className={selectClass} value={yearFilter} onChange={e => setYearFilter(e.target.value)} data-testid="sales-target-year-filter">
            {[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </Field>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Total Target {yearFilter}</div>
          <div className="mt-2 font-mono text-xl font-semibold text-slate-900">{money(totalTarget)}</div>
        </div>
      </div>

      <DataTable
        testId="sales-targets-table"
        items={visibleTargets}
        loading={targets.isLoading}
        total={visibleTargets.length}
        columns={[
          { key: "sales", label: "Sales", render: i => <span className="font-medium">{i.sales_name}</span> },
          { key: "year", label: "Tahun", render: i => i.year },
          { key: "target", label: "Target", render: i => <span className="font-mono font-semibold">{money(i.target)}</span> },
          { key: "action", label: "Aksi", render: i => <Button size="sm" variant="outline" onClick={() => openEdit(i)}>Edit</Button> },
        ]}
      />

      {modal && (
        <Modal title={editing ? "Edit Target Sales" : "Set Target Sales"} onClose={() => { setModal(false); setEditing(null); }}>
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={e => { e.preventDefault(); save.mutate(); }}
            data-testid="sales-target-form"
          >
            <Field label="Sales" required>
              <select className={selectClass} value={form.sales_id} onChange={e => setForm({ ...form, sales_id: e.target.value })} data-testid="sales-target-sales-input">
                <option value="">— Pilih Sales —</option>
                {salesUsers.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}
              </select>
            </Field>
            <Field label="Tahun" required>
              <Input type="number" min="2000" max="2100" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} data-testid="sales-target-year-input" />
            </Field>
            <Field label="Target Tahunan (IDR)" required>
              <Input type="number" min="0" step="1000000" value={form.target} onChange={e => setForm({ ...form, target: e.target.value })} placeholder="Contoh: 4000000000" data-testid="sales-target-value-input" />
            </Field>
            <div className="rounded-md bg-slate-50 p-3 text-xs text-slate-500 sm:col-span-2">
              Target ini menjadi sumber perhitungan <strong>Target, Achievement, Gap, dan Coverage</strong> pada menu Sales Team & KPI.
            </div>
            <div className="flex justify-end gap-2 sm:col-span-2">
              <Button type="button" variant="outline" onClick={() => { setModal(false); setEditing(null); }}>Batal</Button>
              <Button type="submit" disabled={save.isPending || !form.sales_id || !form.target}>Simpan</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
