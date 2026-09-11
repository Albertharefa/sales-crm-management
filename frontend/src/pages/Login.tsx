import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail, ShieldCheck, Sparkles } from "lucide-react";
import { apiPost } from "@/lib/api";
import { beginSession } from "@/lib/session";
import type { User } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/Field";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";

export default function Login() {
  const [email, setEmail] = useState("admin@crm.co.id");
  const [password, setPassword] = useState("Password123");
  const [showPassword, setShowPassword] = useState(false);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => apiPost<User>("/login", { email, password }),
    onSuccess: user => {
      beginSession();
      queryClient.setQueryData(["me"], user);
      toast.success(`Selamat datang, ${user.name}`);
      navigate("/");
    },
    onError: () => toast.error("Email atau password salah"),
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  function openForgotPassword() {
    setForgotEmail(email);
    setForgotOpen(true);
  }

  function submitForgotPassword(event: FormEvent) {
    event.preventDefault();
    toast.info("Permintaan reset password akan diproses oleh administrator CRM.");
    setForgotOpen(false);
  }

  return (
    <>
      <Toaster position="top-right" richColors />
      <div className="grid min-h-svh bg-slate-50 lg:grid-cols-[1.05fr_0.95fr]" data-testid="login-page">
        <section className="relative hidden overflow-hidden bg-[#061126] p-10 text-white lg:flex lg:flex-col lg:justify-between lg:p-16">
          <div className="absolute -right-28 -top-24 size-[30rem] rounded-full border border-blue-400/10" />
          <div className="absolute -right-8 top-28 size-64 rounded-full border border-blue-400/10" />
          <div className="absolute bottom-24 left-[-8rem] size-72 rounded-full bg-blue-600/10 blur-3xl" />
          <div className="absolute right-20 top-24 h-2 w-2 rounded-full bg-blue-400 shadow-[0_0_30px_8px_rgba(59,130,246,0.35)]" />
          <div className="relative z-10">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-blue-600 font-heading text-xl font-bold shadow-lg shadow-blue-950/40">C</div>
              <div>
                <div className="font-heading font-bold">CRM Sales</div>
                <div className="text-[10px] tracking-[0.2em] text-slate-400">MANAGEMENT</div>
              </div>
            </div>
            <div className="mt-32 max-w-xl">
              <div className="mb-5 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-blue-300"><Sparkles className="size-3.5" /> Enterprise sales workspace</div>
              <h1 className="font-heading text-4xl font-bold leading-tight tracking-tight xl:text-5xl">Kendalikan pipeline, quotation, dan pengiriman order dalam satu tempat.</h1>
              <p className="mt-6 max-w-lg text-base leading-relaxed text-slate-400">Server-side pagination, agregasi dashboard, dan monitoring ETA per PO untuk tim sales industri yang bergerak cepat.</p>
              <div className="mt-12 grid max-w-lg grid-cols-3 gap-3">
                {[["11", "MODUL"], ["3", "PERAN"], ["6", "TAHAP ORDER"]].map(([value, label]) => (
                  <div key={label} className="border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm" data-testid={`login-stat-${label.toLowerCase().replaceAll(" ", "-")}`}>
                    <div className="font-mono text-2xl text-blue-300">{value}</div>
                    <div className="mt-2 text-[10px] tracking-wider text-slate-500">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="relative z-10 flex items-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="size-4" /> Sesi httpOnly cookie · password ter-hash · RBAC per modul
          </div>
        </section>

        <section className="relative flex items-center justify-center overflow-hidden p-5 sm:p-10">
          <div className="absolute -left-24 top-1/4 size-64 rounded-full bg-blue-100/70 blur-3xl" />
          <div className="absolute -right-24 bottom-10 size-72 rounded-full bg-indigo-100/60 blur-3xl" />
          <div className="relative z-10 w-full max-w-md">
            <div className="mb-8 lg:hidden">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-xl bg-blue-600 font-heading text-xl font-bold text-white">C</div>
                <div className="font-heading font-bold">CRM Sales Management</div>
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-7 shadow-xl shadow-slate-200/60 backdrop-blur sm:p-9">
              <div className="mb-8">
                <div className="mb-3 flex size-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><LockKeyhole className="size-5" /></div>
                <h2 className="font-heading text-2xl font-bold tracking-tight" data-testid="login-title">Masuk ke akun Anda</h2>
                <p className="mt-2 text-sm text-slate-500">Gunakan kredensial yang diberikan administrator.</p>
              </div>
              <form onSubmit={submit} className="space-y-5" data-testid="login-form">
                <Field label="Email" required>
                  <Input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="username" data-testid="login-email-input" />
                </Field>
                <Field label="Password" required>
                  <div className="relative">
                    <Input type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" className="pr-10" data-testid="login-password-input" />
                    <button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 transition hover:text-blue-600" onClick={() => setShowPassword(v => !v)} title={showPassword ? "Sembunyikan password" : "Lihat password"} aria-label={showPassword ? "Sembunyikan password" : "Lihat password"} data-testid="login-password-toggle">
                      {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </button>
                  </div>
                </Field>
                <div className="flex justify-end -mt-2">
                  <button type="button" onClick={openForgotPassword} className="text-xs font-medium text-blue-600 transition hover:text-blue-800 hover:underline" data-testid="forgot-password-link">Lupa password?</button>
                </div>
                <Button type="submit" className="h-11 w-full" disabled={mutation.isPending} data-testid="login-submit-button">
                  {mutation.isPending ? "Memverifikasi..." : "Masuk"}
                  <ArrowRight className="ml-2 size-4" />
                </Button>
              </form>
              <div className="mt-7 border-t border-slate-100 pt-5">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Akun demo (password: Password123)</div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                  <button type="button" className="rounded border border-slate-200 px-2 py-1 hover:border-blue-300 hover:text-blue-600" onClick={() => setEmail("admin@crm.co.id")} data-testid="demo-admin-button">Super Admin</button>
                  <button type="button" className="rounded border border-slate-200 px-2 py-1 hover:border-blue-300 hover:text-blue-600" onClick={() => setEmail("manager@crm.co.id")} data-testid="demo-manager-button">Sales Manager</button>
                  <button type="button" className="rounded border border-slate-200 px-2 py-1 hover:border-blue-300 hover:text-blue-600" onClick={() => setEmail("sales@crm.co.id")} data-testid="demo-sales-button">Sales</button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {forgotOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-5 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="forgot-password-title" data-testid="forgot-password-modal">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-2xl sm:p-8">
            <div className="mb-6 flex size-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Mail className="size-5" /></div>
            <h2 id="forgot-password-title" className="font-heading text-2xl font-bold tracking-tight">Lupa password?</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">Masukkan email akun Anda. Permintaan reset akan diproses oleh administrator CRM.</p>
            <form onSubmit={submitForgotPassword} className="mt-6 space-y-5">
              <Field label="Email" required>
                <Input type="email" value={forgotEmail} onChange={e => setForgotEmail(e.target.value)} autoComplete="email" required data-testid="forgot-password-email-input" />
              </Field>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setForgotOpen(false)} data-testid="forgot-password-cancel">Batal</Button>
                <Button type="submit" data-testid="forgot-password-submit">Kirim Permintaan</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
