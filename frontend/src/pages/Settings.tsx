import { useQuery } from "@tanstack/react-query";
import { useCurrentUser } from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";
import { CheckCircle2, Database, Gauge, KeyRound, LockKeyhole, ShieldCheck } from "lucide-react";

type SessionInfo = { authenticated: boolean; role: string; permissions: string[]; session_ttl_seconds: number };

const matrix = [
  { module: "Dashboard", admin: "Semua data", manager: "Data team", sales: "Data sendiri" },
  { module: "Customers", admin: "Kelola semua", manager: "Kelola team", sales: "Kelola sendiri" },
  { module: "Sales Pipeline", admin: "Kelola semua", manager: "Kelola team", sales: "Kelola sendiri" },
  { module: "Aktivitas", admin: "Kelola semua", manager: "Kelola team", sales: "Kelola sendiri" },
  { module: "Quotations", admin: "Kelola & Approve semua", manager: "Kelola & Approve team", sales: "Buat & kelola sendiri" },
  { module: "Purchase Orders", admin: "Kelola semua", manager: "Kelola team", sales: "Input & kelola sendiri" },
  { module: "Order Monitoring", admin: "Semua data", manager: "Data team", sales: "Update sendiri" },
  { module: "Sales Team", admin: "Kelola penuh", manager: "Lihat team", sales: "Tidak ada akses" },
  { module: "Target Sales", admin: "Kelola penuh", manager: "Kelola team", sales: "Lihat sendiri" },
  { module: "Users", admin: "Kelola penuh", manager: "Lihat team", sales: "Tidak ada akses" },
  { module: "Products", admin: "Kelola penuh", manager: "Lihat", sales: "Lihat" },
  { module: "Audit Log", admin: "Lihat penuh", manager: "Lihat team", sales: "Tidak ada akses" },
];

export default function Settings() {
  const { data: user } = useCurrentUser();
  const { data: session } = useQuery({ queryKey: ["session-info"], queryFn: () => apiGet<SessionInfo>("/session-info"), staleTime: 60_000, retry: false });
  const profile: { label: string; value: string }[] = [
    { label: "USER ID", value: user?.user_id ?? "—" },
    { label: "NAMA", value: user?.name ?? "—" },
    { label: "EMAIL", value: user?.email ?? "—" },
    { label: "ROLE", value: user?.role ?? "—" },
    { label: "MANAGER ID", value: user?.manager_id ?? "-" },
  ];
  const strategies = [
    { icon: ShieldCheck, title: "RBAC server-side", text: "Setiap API request melewati permission guard. Menyembunyikan menu bukan satu-satunya lapisan keamanan." },
    { icon: LockKeyhole, title: "Session security", text: "httpOnly cookie, Secure/SameSite, session expiry 8 jam, dan sesi kedaluwarsa otomatis ditolak." },
    { icon: KeyRound, title: "Login protection", text: "5 kali password salah mengunci akun selama 15 menit. Login gagal, berhasil, logout, dan access denied dicatat." },
    { icon: Database, title: "Data scope", text: "SUPER ADMIN = ALL · SALES MANAGER = TEAM · SALES = SELF. Record-level scope tetap divalidasi backend." },
    { icon: Gauge, title: "Performance", text: "Index autentikasi, session, manager hierarchy, audit, pagination, dan query operasional disiapkan untuk production." },
    { icon: CheckCircle2, title: "Password recovery", text: "Reset password memakai token satu kali dengan masa berlaku 30 menit dan seluruh sesi user dibatalkan setelah reset." },
  ];
  const ttlHours = Math.round((session?.session_ttl_seconds ?? 28800) / 3600);

  return <div data-testid="settings-page">
    <PageHeader title="Pengaturan Sistem" description="Profil, matriks role & permission, keamanan login, dan strategi performa CRM" />
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      <Card className="border-slate-200"><CardContent className="p-6">
        <div className="text-[10px] font-semibold tracking-wider text-slate-400">PROFIL SAYA</div>
        <div className="mt-5 flex size-14 items-center justify-center rounded-xl bg-blue-50 font-heading text-xl font-bold text-blue-600">{user?.name?.slice(0, 1) ?? "A"}</div>
        <dl className="mt-6 space-y-4 text-sm">{profile.map(item => <div key={item.label}><dt className="text-[10px] font-semibold tracking-wider text-slate-400">{item.label}</dt><dd className="mt-1 font-medium" data-testid={`profile-${item.label.toLowerCase().replaceAll(" ", "-")}`}>{item.value}</dd></div>)}</dl>
        <div className="mt-6 rounded-xl border border-emerald-100 bg-emerald-50/60 p-4"><div className="flex items-center gap-2 text-sm font-semibold text-emerald-800"><ShieldCheck className="size-4" />Session aktif</div><p className="mt-1 text-xs leading-relaxed text-emerald-700">Role: {session?.role ?? user?.role ?? "—"} · TTL maksimum {ttlHours} jam.</p></div>
      </CardContent></Card>
      <div className="space-y-6">
        <Card className="border-slate-200"><CardContent className="p-6">
          <div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="font-heading text-xl font-semibold">Matriks Role & Permission</h2><p className="mt-1 text-sm text-slate-500">Akses mengikuti role dan scope data. Enforcement dilakukan di backend.</p></div><Badge variant="outline">RBAC aktif</Badge></div>
          <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-slate-200 text-[10px] uppercase tracking-wider text-slate-500"><tr><th className="py-3">Modul</th><th>Super Admin</th><th>Sales Manager</th><th>Sales</th></tr></thead><tbody className="divide-y divide-slate-100">{matrix.map(row => <tr key={row.module}><td className="py-3 font-medium">{row.module}</td><td><Badge variant="outline">{row.admin}</Badge></td><td>{row.manager}</td><td>{row.sales}</td></tr>)}</tbody></table></div>
        </CardContent></Card>
        <div className="grid gap-4 md:grid-cols-2">{strategies.map(({ icon: Icon, title, text }) => <Card key={title} className="border-slate-200"><CardContent className="p-5"><Icon className="size-5 text-blue-600" /><h3 className="mt-4 font-heading font-semibold">{title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-500">{text}</p></CardContent></Card>)}</div>
      </div>
    </div>
  </div>;
}
