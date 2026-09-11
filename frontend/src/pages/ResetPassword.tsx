import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Eye, EyeOff, KeyRound, ShieldCheck } from "lucide-react";
import { apiPost } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/Field";
import { toast } from "sonner";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = useMemo(() => params.get("token") ?? "", [params]);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) return toast.error("Link reset password tidak valid.");
    if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      return toast.error("Password minimal 8 karakter dan harus mengandung huruf serta angka.");
    }
    if (password !== confirmPassword) return toast.error("Konfirmasi password tidak sama.");

    setLoading(true);
    try {
      await apiPost("/auth/reset-password", { token, password });
      toast.success("Password berhasil direset. Silakan login dengan password baru.");
      navigate("/login", { replace: true });
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Link reset password tidak valid atau sudah kedaluwarsa.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-gradient-to-br from-slate-50 via-orange-50/30 to-amber-50/50 p-5">
      <div className="w-full max-w-md rounded-2xl border border-orange-100 bg-white p-7 shadow-2xl shadow-orange-100/60 sm:p-9">
        <div className="mb-6 flex size-11 items-center justify-center rounded-xl bg-orange-50 text-orange-600"><KeyRound className="size-5" /></div>
        <h1 className="font-heading text-2xl font-bold tracking-tight">Buat password baru</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">Masukkan password baru untuk akun CRM Sales Management Anda.</p>
        <form onSubmit={submit} className="mt-7 space-y-5" data-testid="reset-password-form">
          <Field label="Password Baru" required>
            <div className="relative">
              <Input type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" className="pr-10" required data-testid="reset-password-input" />
              <button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-orange-600" onClick={() => setShowPassword(v => !v)} aria-label={showPassword ? "Sembunyikan password" : "Lihat password"}>{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button>
            </div>
          </Field>
          <Field label="Konfirmasi Password" required>
            <div className="relative">
              <Input type={showConfirm ? "text" : "password"} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} autoComplete="new-password" className="pr-10" required data-testid="reset-password-confirm-input" />
              <button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-orange-600" onClick={() => setShowConfirm(v => !v)} aria-label={showConfirm ? "Sembunyikan password" : "Lihat password"}>{showConfirm ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button>
            </div>
          </Field>
          <div className="flex items-start gap-2 rounded-lg bg-orange-50 p-3 text-xs text-orange-900"><ShieldCheck className="mt-0.5 size-4 shrink-0" /><span>Gunakan minimal 8 karakter dan kombinasi huruf serta angka.</span></div>
          <Button type="submit" className="h-11 w-full bg-orange-600 hover:bg-orange-700" disabled={loading || !token}>{loading ? "Menyimpan..." : "Simpan Password Baru"}</Button>
        </form>
      </div>
    </div>
  );
}
