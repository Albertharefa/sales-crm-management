import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, KeyRound, Pencil, Trash2 } from "lucide-react";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import type { Paginated, User } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import { useCurrentUser } from "@/components/AppShell";
import Modal from "@/components/Modal";
import DataTable from "@/components/DataTable";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

const emptyForm = { name: "", email: "", role: "SALES", manager_id: "", phone: "", status: "Active", password: "Password123" };
type UserForm = typeof emptyForm;
type UserOption = Pick<User, "id" | "user_id" | "name" | "role">;
type OptionsResponse = { users: UserOption[] };

export default function Users() {
  const { data: currentUser } = useCurrentUser();
  const isAdmin = currentUser?.role === "SUPER_ADMIN";
  const [modal, setModal] = useState(false);
  const [viewUser, setViewUser] = useState<User | null>(null);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [form, setForm] = useState<UserForm>(emptyForm);
  const [editForm, setEditForm] = useState<UserForm>({ ...emptyForm, password: "" });
  const [showCreatePassword, setShowCreatePassword] = useState(false);
  const [showEditPassword, setShowEditPassword] = useState(false);
  const qc = useQueryClient();

  const query = useQuery({ queryKey: ["users", page, pageSize], queryFn: () => apiGet<Paginated<User>>(`/users?page=${page}&page_size=${pageSize}`) });
  const optionsQuery = useQuery({ queryKey: ["user-manager-options"], queryFn: () => apiGet<OptionsResponse>("/options") });

  const create = useMutation({
    mutationFn: () => apiPost<User>("/users", { ...form, manager_id: form.manager_id || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); setModal(false); setForm({ ...emptyForm }); setShowCreatePassword(false); toast.success("User berhasil ditambahkan"); },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "User gagal disimpan"),
  });
  const update = useMutation({
    mutationFn: () => {
      if (!editUser) throw new Error("User tidak dipilih");
      const payload: Record<string, string | null> = { name: editForm.name, email: editForm.email, role: editForm.role, manager_id: editForm.manager_id || null, phone: editForm.phone || null, status: editForm.status };
      if (editForm.password.trim()) payload.password = editForm.password;
      return apiPut<User>(`/users/${editUser.id}`, payload);
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); setEditUser(null); setShowEditPassword(false); toast.success("User berhasil diperbarui"); },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "User gagal diperbarui"),
  });
  const remove = useMutation({
    mutationFn: (user: User) => apiDelete<{ message: string }>(`/users/${user.id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); toast.success("User berhasil dihapus"); },
    onError: (error: any) => toast.error(error?.response?.data?.detail || "User gagal dihapus"),
  });
  const resetPassword = useMutation({
    mutationFn: (user: User) => apiPost<{ message: string; user_id: string }>(`/users/${user.id}/reset-password`, {}),
    onSuccess: (_, user) => toast.success(`Password ${user.name} berhasil direset ke Password123`),
    onError: (error: any) => toast.error(error?.response?.data?.detail || "Password user gagal direset"),
  });

  const managerCandidates = [...(query.data?.items ?? []), ...(optionsQuery.data?.users ?? [])];
  const managers = Array.from(new Map(managerCandidates.filter(u => String(u.role ?? "").toUpperCase() === "SALES_MANAGER").map(u => [u.id, u])).values());
  const managerLabel = (managerId: string | null | undefined) => {
    if (!managerId) return "—";
    const manager = managers.find(u => u.id === managerId || u.user_id === managerId);
    return manager ? `${manager.name} — ${manager.user_id}` : managerId;
  };
  const normalizeManagerId = (managerId: string | null | undefined) => {
    if (!managerId) return "";
    const manager = managers.find(u => u.id === managerId || u.user_id === managerId);
    return manager?.id ?? managerId;
  };
  const openEdit = (user: User) => {
    if (!isAdmin) return;
    setEditUser(user);
    setEditForm({ name: user.name, email: user.email, role: user.role, manager_id: normalizeManagerId(user.manager_id), phone: user.phone ?? "", status: user.status, password: "" });
    setShowEditPassword(false);
  };
  const handleDelete = (user: User) => {
    if (!isAdmin) return;
    const confirmed = window.confirm(`Hapus user ${user.name} (${user.user_id})?\n\nData user akan dihapus dan tidak dapat dibatalkan.`);
    if (confirmed) remove.mutate(user);
  };
  const handleResetPassword = (user: User) => {
    if (!isAdmin) return;
    const confirmed = window.confirm(`Reset password ${user.name} (${user.user_id})?\n\nPassword akan dikembalikan ke Password123.`);
    if (confirmed) resetPassword.mutate(user);
  };

  return <div data-testid="users-page">
    <PageHeader title="Kelola Pengguna" description="User_ID adalah identifier utama; Manager_ID menghubungkan hierarki" action={isAdmin ? { label: "Tambah User", onClick: () => { setForm({ ...emptyForm }); setShowCreatePassword(false); setModal(true); } } : undefined} onRefresh={() => void query.refetch()} />
    <DataTable testId="users-table" items={query.data?.items ?? []} loading={query.isLoading} total={query.data?.total} page={page} pageSize={pageSize} onPage={setPage} onPageSize={size => { setPageSize(size); setPage(1); }} columns={[
      { key: "id", label: "User ID", render: i => <span className="font-mono text-xs text-blue-600">{i.user_id}</span> },
      { key: "name", label: "Nama", render: i => <span className="font-medium">{i.name}</span> },
      { key: "email", label: "Email", render: i => i.email },
      { key: "role", label: "Role", render: i => <Badge>{i.role}</Badge> },
      { key: "manager", label: "Manager", render: i => managerLabel(i.manager_id) },
      { key: "phone", label: "Telepon", render: i => i.phone ?? "—" },
      { key: "status", label: "Status", render: i => <Badge variant="outline">{i.status}</Badge> },
      { key: "last", label: "Last Login", render: i => i.last_login ? new Date(i.last_login).toLocaleString("id-ID") : "Belum pernah" },
      { key: "actions", label: "Aksi", render: i => <div className="flex items-center gap-1">
        <Button type="button" variant="ghost" size="icon-sm" className="text-blue-600 hover:text-blue-700" onClick={() => setViewUser(i)} title="View" aria-label={`View ${i.name}`} data-testid={`user-view-${i.id}`}><Eye /></Button>
        {isAdmin && <><Button type="button" variant="ghost" size="icon-sm" className="text-slate-600 hover:text-slate-900" onClick={() => openEdit(i)} title="Edit" aria-label={`Edit ${i.name}`} data-testid={`user-edit-${i.id}`}><Pencil /></Button><Button type="button" variant="ghost" size="icon-sm" className="text-amber-600 hover:text-amber-700" onClick={() => handleResetPassword(i)} title="Reset Password" aria-label={`Reset password ${i.name}`} data-testid={`user-reset-password-${i.id}`} disabled={resetPassword.isPending}><KeyRound /></Button><Button type="button" variant="ghost" size="icon-sm" className="text-red-500 hover:text-red-600" onClick={() => handleDelete(i)} title="Delete" aria-label={`Delete ${i.name}`} data-testid={`user-delete-${i.id}`} disabled={remove.isPending}><Trash2 /></Button></>}
      </div> },
    ]} />

    {modal && isAdmin && <Modal title="Tambah User" onClose={() => setModal(false)}><form className="grid gap-4 sm:grid-cols-2" onSubmit={e => { e.preventDefault(); create.mutate(); }} data-testid="user-create-form">
      <Field label="Nama" required><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} data-testid="user-name-input" /></Field><Field label="Email" required><Input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} data-testid="user-email-input" /></Field>
      <Field label="Role"><select className={selectClass} value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} data-testid="user-role-input"><option>SUPER_ADMIN</option><option>SALES_MANAGER</option><option>SALES</option></select></Field>
      <Field label="Manager"><select className={selectClass} value={form.manager_id} onChange={e => setForm({ ...form, manager_id: e.target.value })} data-testid="user-manager-input"><option value="">— Tanpa manager —</option>{managers.map(u => <option key={u.id} value={u.id}>{u.name} — {u.user_id}</option>)}</select></Field>
      <Field label="Telepon"><Input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} data-testid="user-phone-input" /></Field><Field label="Status"><select className={selectClass} value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} data-testid="user-status-input"><option>Active</option><option>Inactive</option></select></Field>
      <Field label="Password Awal"><div className="relative"><Input type={showCreatePassword ? "text" : "password"} value={form.password} autoComplete="new-password" onChange={e => setForm({ ...form, password: e.target.value })} data-testid="user-password-input" className="pr-10" /><button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-800" onClick={() => setShowCreatePassword(v => !v)} title={showCreatePassword ? "Sembunyikan password" : "Lihat password"} aria-label={showCreatePassword ? "Sembunyikan password" : "Lihat password"} data-testid="user-password-toggle">{showCreatePassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></div></Field>
      <div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="outline" onClick={() => setModal(false)}>Batal</Button><Button type="submit" disabled={create.isPending}>Simpan</Button></div>
    </form></Modal>}

    {viewUser && <Modal title={`Detail User — ${viewUser.name}`} onClose={() => setViewUser(null)}><div className="grid gap-4 sm:grid-cols-2" data-testid="user-view-modal">
      <Field label="User ID"><div className="rounded-md border bg-slate-50 px-3 py-2 font-mono text-sm">{viewUser.user_id}</div></Field><Field label="Nama"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.name}</div></Field><Field label="Email"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.email}</div></Field><Field label="Role"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.role}</div></Field><Field label="Manager ID"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{managerLabel(viewUser.manager_id)}</div></Field><Field label="Telepon"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.phone ?? "—"}</div></Field><Field label="Status"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.status}</div></Field><Field label="Last Login"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.last_login ? new Date(viewUser.last_login).toLocaleString("id-ID") : "Belum pernah"}</div></Field><Field label="Created At"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.created_at ? new Date(viewUser.created_at).toLocaleString("id-ID") : "—"}</div></Field>
      <div className="flex justify-end sm:col-span-2"><Button type="button" onClick={() => setViewUser(null)}>Tutup</Button></div>
    </div></Modal>}

    {editUser && isAdmin && <Modal title={`Edit User — ${editUser.name}`} onClose={() => setEditUser(null)}><form className="grid gap-4 sm:grid-cols-2" onSubmit={e => { e.preventDefault(); update.mutate(); }} data-testid="user-edit-form">
      <Field label="Nama" required><Input value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} data-testid="user-edit-name-input" /></Field><Field label="Email" required><Input type="email" value={editForm.email} onChange={e => setEditForm({ ...editForm, email: e.target.value })} data-testid="user-edit-email-input" /></Field><Field label="Role"><select className={selectClass} value={editForm.role} onChange={e => setEditForm({ ...editForm, role: e.target.value })} data-testid="user-edit-role-input"><option>SUPER_ADMIN</option><option>SALES_MANAGER</option><option>SALES</option></select></Field><Field label="Manager"><select className={selectClass} value={editForm.manager_id} onChange={e => setEditForm({ ...editForm, manager_id: e.target.value })} data-testid="user-edit-manager-input"><option value="">— Tanpa manager —</option>{managers.map(u => <option key={u.id} value={u.id}>{u.name} — {u.user_id}</option>)}</select></Field><Field label="Telepon"><Input value={editForm.phone} onChange={e => setEditForm({ ...editForm, phone: e.target.value })} data-testid="user-edit-phone-input" /></Field><Field label="Status"><select className={selectClass} value={editForm.status} onChange={e => setEditForm({ ...editForm, status: e.target.value })} data-testid="user-edit-status-input"><option>Active</option><option>Inactive</option></select></Field>
      <Field label="Password Baru"><div className="relative"><Input type={showEditPassword ? "text" : "password"} value={editForm.password} autoComplete="new-password" onChange={e => setEditForm({ ...editForm, password: e.target.value })} data-testid="user-edit-password-input" placeholder="Kosongkan jika tidak diubah" className="pr-10" /><button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-800" onClick={() => setShowEditPassword(v => !v)} title={showEditPassword ? "Sembunyikan password" : "Lihat password"} aria-label={showEditPassword ? "Sembunyikan password" : "Lihat password"} data-testid="user-edit-password-toggle">{showEditPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></div></Field>
      <div className="flex justify-end gap-2 sm:col-span-2"><Button type="button" variant="outline" onClick={() => setEditUser(null)}>Batal</Button><Button type="submit" disabled={update.isPending}>Simpan Perubahan</Button></div>
    </form></Modal>}
  </div>;
}
