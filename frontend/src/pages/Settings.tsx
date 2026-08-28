import { useCurrentUser } from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Database, Gauge, ShieldCheck } from "lucide-react";

const matrix = [
  { module: "Dashboard", admin: "Semua data", manager: "Data team", sales: "Data sendiri" },
  { module: "Customers", admin: "Kelola semua", manager: "Lihat team", sales: "Kelola milik sendiri" },
  { module: "Sales Pipeline", admin: "Kelola semua", manager: "Lihat team", sales: "Kelola milik sendiri" },
  { module: "Aktivitas", admin: "Kelola semua", manager: "Lihat team", sales: "Input milik sendiri" },
  { module: "Quotations", admin: "Kelola semua", manager: "Approve team", sales: "Buat & kelola sendiri" },
  { module: "Purchase Orders", admin: "Kelola semua", manager: "Lihat team", sales: "Input milik sendiri" },
  { module: "Order Monitoring", admin: "Kelola semua", manager: "Lihat team", sales: "Update sendiri" },
  { module: "Users", admin: "Kelola penuh", manager: "Lihat team", sales: "Tidak ada akses" },
  { module: "Products", admin: "Kelola penuh", manager: "Lihat", sales: "Lihat" },
  { module: "Audit Log", admin: "Lihat penuh", manager: "Lihat", sales: "Tidak ada akses" },
];

export default function Settings() {
  const { data: user } = useCurrentUser();
  const profile: { label: string; value: string }[] = [
    { label: "USER ID", value: user?.user_id ?? "—" },
    { label: "NAMA", value: user?.name ?? "—" },
    { label: "EMAIL", value: user?.email ?? "—" },
    { label: "ROLE", value: user?.role ?? "—" },
    { label: "MANAGER ID", value: user?.manager_id ?? "-" },
  ];
  const strategies = [
    { icon: Database, title: "Server-side pagination", text: "LIMIT/OFFSET pada seluruh endpoint list, default 25 baris per halaman." },
    { icon: Gauge, title: "Database aggregation", text: "Dashboard dan KPI memakai grouped aggregation dengan respons angka ringkas." },
    { icon: ShieldCheck, title: "Security boundary", text: "Cookie httpOnly, password bcrypt, RBAC, validation, dan audit trail aktif." },
    { icon: CheckCircle2, title: "Indexed operations", text: "Index untuk email, role, customer_id, stage, po_number, status, dan created_at." },
  ];
  return <div data-testid="settings-page">
    <PageHeader title="Pengaturan Sistem" description="Profil, matriks izin, dan strategi performa yang diterapkan" />
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      <Card className="border-slate-200"><CardContent className="p-6">
        <div className="text-[10px] font-semibold tracking-wider text-slate-400">PROFIL SAYA</div>
        <div className="mt-5 flex size-14 items-center justify-center rounded-xl bg-blue-50 font-heading text-xl font-bold text-blue-600">{user?.name.slice(0, 1) ?? "A"}</div>
        <dl className="mt-6 space-y-4 text-sm">{profile.map(item => <div key={item.label}><dt className="text-[10px] font-semibold tracking-wider text-slate-400">{item.label}</dt><dd className="mt-1 font-medium" data-testid={`profile-${item.label.toLowerCase().replaceAll(" ", "-")}`}>{item.value}</dd></div>)}</dl>
      </CardContent></Card>
      <div className="space-y-6">
        <Card className="border-slate-200"><CardContent className="p-6">
          <h2 className="font-heading text-xl font-semibold">Matriks Role & Permission</h2>
          <div className="mt-5 overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-slate-200 text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="py-3">Modul</th><th>Super Admin</th><th>Sales Manager</th><th>Sales</th></tr></thead><tbody className="divide-y divide-slate-100">{matrix.map(row => <tr key={row.module}><td className="py-3 font-medium">{row.module}</td><td><Badge variant="outline">{row.admin}</Badge></td><td>{row.manager}</td><td>{row.sales}</td></tr>)}</tbody></table></div>
        </CardContent></Card>
        <div className="grid gap-4 md:grid-cols-2">{strategies.map(({ icon: Icon, title, text }) => <Card key={title} className="border-slate-200"><CardContent className="p-5"><Icon className="size-5 text-blue-600" /><h3 className="mt-4 font-heading font-semibold">{title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-500">{text}</p></CardContent></Card>)}</div>
      </div>
    </div>
  </div>;
}