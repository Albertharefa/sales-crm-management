import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Pencil, Trash2 } from "lucide-react";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import type { Paginated, User } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import DataTable from "@/components/DataTable";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

const emptyForm = {
  name: "",
  email: "",
  role: "SALES",
  manager_id: "",
  phone: "",
  status: "Active",
  password: "Password123",
};

type UserForm = typeof emptyForm;

export default function Users() {
  const [modal, setModal] = useState(false);
  const [viewUser, setViewUser] = useState<User | null>(null);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [form, setForm] = useState<UserForm>(emptyForm);
  const [editForm, setEditForm] = useState<UserForm>({ ...emptyForm, password: "" });
  const qc = useQueryClient();

  const query = useQuery({
    queryKey: ["users", page, pageSize],
    queryFn: () => apiGet<Paginated<User>>(`/users?page=${page}&page_size=${pageSize}`),
  });

  const create = useMutation({
    mutationFn: () => apiPost<User>("/users", { ...form, manager_id: form.manager_id || null }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setModal(false);
      setForm({ ...emptyForm });
      toast.success("User berhasil ditambahkan");
    },
    onError: () => toast.error("User gagal disimpan"),
  });

  const update = useMutation({
    mutationFn: () => {
      if (!editUser) throw new Error("User tidak dipilih");
      const payload: Record<string, string | null> = {
        name: editForm.name,
        email: editForm.email,
        role: editForm.role,
        manager_id: editForm.manager_id || null,
        phone: editForm.phone || null,
        status: editForm.status,
      };
      if (editForm.password.trim()) payload.password = editForm.password;
      return apiPut<User>(`/users/${editUser.id}`, payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setEditUser(null);
      toast.success("User berhasil diperbarui");
    },
    onError: () => toast.error("User gagal diperbarui"),
  });

  const remove = useMutation({
    mutationFn: (user: User) => apiDelete<{ message: string }>(`/users/${user.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("User berhasil dihapus");
    },
    onError: () => toast.error("User gagal dihapus"),
  });

  const openEdit = (user: User) => {
    setEditUser(user);
    setEditForm({
      name: user.name,
      email: user.email,
      role: user.role,
      manager_id: user.manager_id ?? "",
      phone: user.phone ?? "",
      status: user.status,
      password: "",
    });
  };

  const handleDelete = (user: User) => {
    const confirmed = window.confirm(`Hapus user ${user.name} (${user.user_id})?\n\nData user akan dihapus dan tidak dapat dibatalkan.`);
    if (confirmed) remove.mutate(user);
  };

  const managers = (query.data?.items ?? []).filter(u => u.role === "SALES_MANAGER");

  return (
    <div data-testid="users-page">
      <PageHeader
        title="Kelola Pengguna"
        description="User_ID adalah identifier utama; Manager_ID menghubungkan hierarki"
        action={{ label: "Tambah User", onClick: () => setModal(true) }}
        onRefresh={() => void query.refetch()}
      />

      <DataTable
        testId="users-table"
        items={query.data?.items ?? []}
        loading={query.isLoading}
        total={query.data?.total}
        page={page}
        pageSize={pageSize}
        onPage={setPage}
        onPageSize={size => {
          setPageSize(size);
          setPage(1);
        }}
        columns={[
          { key: "id", label: "User ID", render: i => <span className="font-mono text-xs text-blue-600">{i.user_id}</span> },
          { key: "name", label: "Nama", render: i => <span className="font-medium">{i.name}</span> },
          { key: "email", label: "Email", render: i => i.email },
          { key: "role", label: "Role", render: i => <Badge>{i.role}</Badge> },
          { key: "manager", label: "Manager", render: i => i.manager_id ?? "—" },
          { key: "phone", label: "Telepon", render: i => i.phone ?? "—" },
          { key: "status", label: "Status", render: i => <Badge variant="outline">{i.status}</Badge> },
          { key: "last", label: "Last Login", render: i => i.last_login ? new Date(i.last_login).toLocaleString("id-ID") : "Belum pernah" },
          {
            key: "actions",
            label: "Aksi",
            render: i => (
              <div className="flex items-center gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  className="text-blue-600 hover:text-blue-700"
                  onClick={() => setViewUser(i)}
                  title="View"
                  aria-label={`View ${i.name}`}
                  data-testid={`user-view-${i.id}`}
                >
                  <Eye />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  className="text-slate-600 hover:text-slate-900"
                  onClick={() => openEdit(i)}
                  title="Edit"
                  aria-label={`Edit ${i.name}`}
                  data-testid={`user-edit-${i.id}`}
                >
                  <Pencil />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  className="text-red-500 hover:text-red-600"
                  onClick={() => handleDelete(i)}
                  title="Delete"
                  aria-label={`Delete ${i.name}`}
                  data-testid={`user-delete-${i.id}`}
                  disabled={remove.isPending}
                >
                  <Trash2 />
                </Button>
              </div>
            ),
          },
        ]}
      />

      {modal && (
        <Modal title="Tambah User" onClose={() => setModal(false)}>
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={e => {
              e.preventDefault();
              create.mutate();
            }}
            data-testid="user-create-form"
          >
            <Field label="Nama" required>
              <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} data-testid="user-name-input" />
            </Field>
            <Field label="Email" required>
              <Input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} data-testid="user-email-input" />
            </Field>
            <Field label="Role">
              <select className={selectClass} value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} data-testid="user-role-input">
                <option>SUPER_ADMIN</option>
                <option>SALES_MANAGER</option>
                <option>SALES</option>
              </select>
            </Field>
            <Field label="Manager">
              <select className={selectClass} value={form.manager_id} onChange={e => setForm({ ...form, manager_id: e.target.value })} data-testid="user-manager-input">
                <option value="">— Tanpa manager —</option>
                {managers.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
              </select>
            </Field>
            <Field label="Telepon">
              <Input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} data-testid="user-phone-input" />
            </Field>
            <Field label="Status">
              <select className={selectClass} value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} data-testid="user-status-input">
                <option>Active</option>
                <option>Inactive</option>
              </select>
            </Field>
            <Field label="Password Awal">
              <Input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} data-testid="user-password-input" />
            </Field>
            <div className="flex justify-end gap-2 sm:col-span-2">
              <Button type="button" variant="outline" onClick={() => setModal(false)} data-testid="user-cancel-button">Batal</Button>
              <Button type="submit" disabled={create.isPending} data-testid="user-save-button">Simpan</Button>
            </div>
          </form>
        </Modal>
      )}

      {viewUser && (
        <Modal title={`Detail User — ${viewUser.name}`} onClose={() => setViewUser(null)}>
          <div className="grid gap-4 sm:grid-cols-2" data-testid="user-view-modal">
            <Field label="User ID"><div className="rounded-md border bg-slate-50 px-3 py-2 font-mono text-sm">{viewUser.user_id}</div></Field>
            <Field label="Nama"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.name}</div></Field>
            <Field label="Email"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.email}</div></Field>
            <Field label="Role"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.role}</div></Field>
            <Field label="Manager ID"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.manager_id ?? "—"}</div></Field>
            <Field label="Telepon"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.phone ?? "—"}</div></Field>
            <Field label="Status"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.status}</div></Field>
            <Field label="Last Login"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.last_login ? new Date(viewUser.last_login).toLocaleString("id-ID") : "Belum pernah"}</div></Field>
            <Field label="Created At"><div className="rounded-md border bg-slate-50 px-3 py-2 text-sm">{viewUser.created_at ? new Date(viewUser.created_at).toLocaleString("id-ID") : "—"}</div></Field>
            <div className="flex justify-end sm:col-span-2">
              <Button type="button" onClick={() => setViewUser(null)}>Tutup</Button>
            </div>
          </div>
        </Modal>
      )}

      {editUser && (
        <Modal title={`Edit User — ${editUser.name}`} onClose={() => setEditUser(null)}>
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={e => {
              e.preventDefault();
              update.mutate();
            }}
            data-testid="user-edit-form"
          >
            <Field label="Nama" required>
              <Input value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} data-testid="user-edit-name-input" />
            </Field>
            <Field label="Email" required>
              <Input type="email" value={editForm.email} onChange={e => setEditForm({ ...editForm, email: e.target.value })} data-testid="user-edit-email-input" />
            </Field>
            <Field label="Role">
              <select className={selectClass} value={editForm.role} onChange={e => setEditForm({ ...editForm, role: e.target.value })} data-testid="user-edit-role-input">
                <option>SUPER_ADMIN</option>
                <option>SALES_MANAGER</option>
                <option>SALES</option>
              </select>
            </Field>
            <Field label="Manager">
              <select className={selectClass} value={editForm.manager_id} onChange={e => setEditForm({ ...editForm, manager_id: e.target.value })} data-testid="user-edit-manager-input">
                <option value="">— Tanpa manager —</option>
                {managers.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
              </select>
            </Field>
            <Field label="Telepon">
              <Input value={editForm.phone} onChange={e => setEditForm({ ...editForm, phone: e.target.value })} data-testid="user-edit-phone-input" />
            </Field>
            <Field label="Status">
              <select className={selectClass} value={editForm.status} onChange={e => setEditForm({ ...editForm, status: e.target.value })} data-testid="user-edit-status-input">
                <option>Active</option>
                <option>Inactive</option>
              </select>
            </Field>
            <Field label="Password Baru" description="Kosongkan jika password tidak ingin diubah.">
              <Input type="password" value={editForm.password} onChange={e => setEditForm({ ...editForm, password: e.target.value })} data-testid="user-edit-password-input" placeholder="Tidak diubah" />
            </Field>
            <div className="flex justify-end gap-2 sm:col-span-2">
              <Button type="button" variant="outline" onClick={() => setEditUser(null)} data-testid="user-edit-cancel-button">Batal</Button>
              <Button type="submit" disabled={update.isPending} data-testid="user-edit-save-button">Simpan Perubahan</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
