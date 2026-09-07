import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ArrowRight, LockKeyhole, ShieldCheck } from "lucide-react";
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

  return (
    <>
      <Toaster position="top-right" richColors />
      <div className="grid min-h-svh bg-slate-50 lg:grid-cols-[1.05fr_0.95fr]" data-testid="login-page">
        <section className="relative hidden overflow-hidden bg-[#081126] p-10 text-white lg:flex lg:flex-col lg:justify-between lg:p-16">
          <div className="absolute -right-20 top-20 size-72 rounded-full border border-blue-500/10" />
          <div className="absolute -right-8 top-32 size-52 rounded-full border border-blue-500/10" />
          <div>
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-blue-600 font-heading text-xl font-bold">C</div>
              <div>
                <div className="font-heading font-bold">CRM Sales</div>
                <div className="text-[10px] tracking-[0.2em] text-slate-400">MANAGEMENT</div>
              </div>
            </div>
            <div className="mt-32 max-w-xl">
              <div className="mb-5 text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">Enterprise sales workspace</div>
              <h1 className="font-heading text-4xl font-bold leading-tight tracking-tight xl:text-5xl">Kendalikan pipeline, quotation, dan pengiriman order dalam satu tempat.</h1>
              <p className="mt-6 max-w-lg text-base leading-relaxed text-slate-400">Server-side pagination, agregasi dashboard, dan monitoring ETA per PO untuk tim sales industri yang bergerak cepat.</p>
              <div className="mt-12 grid max-w-lg grid-cols-3 gap-3">
                {[["11", "MODUL"], ["3", "PERAN"], ["6", "TAHAP ORDER"]].map(([value, label]) => (
                  <div key={label} className="border border-white/10 bg-white/[0.03] p-4" data-testid={`login-stat-${label.toLowerCase().replaceAll(" ", "-")}`}>
                    <div className="font-mono text-2xl text-blue-300">{value}</div>
                    <div className="mt-2 text-[10px] tracking-wider text-slate-500">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="size-4" /> Sesi httpOnly cookie · password ter-hash · RBAC per modul
          </div>
        </section>

        <section className="flex items-center justify-center p-5 sm:p-10">
          <div className="w-full max-w-md">
            <div className="mb-8 lg:hidden">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-blue-600 font-heading text-xl font-bold text-white">C</div>
                <div className="font-heading font-bold">CRM Sales Management</div>
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-7 shadow-sm sm:p-9">
              <div className="mb-8">
                <div className="mb-3 flex size-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                  <LockKeyhole className="size-5" />
                </div>
                <h2 className="font-heading text-2xl font-bold tracking-tight" data-testid="login-title">Masuk ke akun Anda</h2>
                <p className="mt-2 text-sm text-slate-500">Gunakan kredensial yang diberikan administrator.</p>
              </div>
              <form onSubmit={submit} className="space-y-5" data-testid="login-form">
                <Field label="Email" required>
                  <Input type="email" value={email} onChange={e => setEmail(e.target.value)} data-testid="login-email-input" />
                </Field>
                <Field label="Password" required>
                  <Input type="password" value={password} onChange={e => setPassword(e.target.value)} data-testid="login-password-input" />
                </Field>
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
    </>
  );
}
