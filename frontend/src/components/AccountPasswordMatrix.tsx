import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { apiGet, apiPost } from "@/lib/api";
import type { Paginated, User } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type ResetResponse = { message: string; user_id: string };

export default function AccountPasswordMatrix() {
  const [busyUserId, setBusyUserId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const usersQuery = useQuery({
    queryKey: ["settings-password-users"],
    queryFn: () => apiGet<Paginated<User>>("/users?page=1&page_size=100"),
    staleTime: 60_000,
  });

  const resetPassword = async (target: User) => {
    const confirmed = window.confirm(
      `Reset password ${target.name} (${target.user_id})?\n\nPassword sementara akan dikembalikan ke Password123 dan semua sesi user akan dibatalkan.`
    );
    if (!confirmed) return;

    setBusyUserId(target.id);
    try {
      await apiPost<ResetResponse>(`/users/${target.id}/reset-password`, {});
      toast.success("Password berhasil direset", {
        description: `${target.name} dapat login menggunakan Password123.`,
      });
      await queryClient.invalidateQueries({ queryKey: ["settings-password-users"] });
    } catch (error: any) {
      toast.error("Reset password gagal", {
        description: error?.response?.data?.detail ?? "Silakan coba lagi.",
      });
    } finally {
      setBusyUserId(null);
    }
  };

  const users = usersQuery.data?.items ?? [];

  return (
    <Card className="border-slate-200" data-testid="password-reset-matrix-card">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <KeyRound className="size-5 text-blue-600" />
              <h2 className="font-heading text-xl font-semibold">Matriks Reset Password User</h2>
              <Badge variant="outline">SUPER ADMIN</Badge>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">
              Setiap user dapat mengganti password sendiri melalui Keamanan Akun. Hanya SUPER ADMIN yang dapat mereset password user lain.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => void usersQuery.refetch()}
            disabled={usersQuery.isFetching}
            data-testid="password-reset-matrix-refresh"
          >
            <RefreshCw className={`mr-2 size-4 ${usersQuery.isFetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        <div className="mt-5 overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full min-w-[760px] text-left text-sm" data-testid="password-reset-matrix-table">
            <thead className="border-b border-slate-200 bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">User ID</th>
                <th className="px-4 py-3">Nama</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Reset Password</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {usersQuery.isLoading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">Memuat daftar user...</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">Belum ada user.</td></tr>
              ) : (
                users.map((target) => (
                  <tr key={target.id}>
                    <td className="px-4 py-3 font-mono text-xs text-blue-600">{target.user_id}</td>
                    <td className="px-4 py-3 font-medium text-slate-800">{target.name}</td>
                    <td className="px-4 py-3 text-slate-600">{target.email}</td>
                    <td className="px-4 py-3"><Badge variant="outline">{target.role}</Badge></td>
                    <td className="px-4 py-3"><Badge variant="outline">{target.status}</Badge></td>
                    <td className="px-4 py-3">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => void resetPassword(target)}
                        disabled={busyUserId !== null}
                        data-testid={`settings-reset-password-${target.id}`}
                      >
                        <KeyRound className="mr-2 size-4" />
                        {busyUserId === target.id ? "Memproses..." : "Reset"}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 grid gap-3 text-xs text-slate-500 md:grid-cols-2">
          <div className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-3">
            <strong className="text-emerald-800">User sendiri</strong><br />
            Ganti password melalui form Keamanan Akun dengan password saat ini.
          </div>
          <div className="rounded-lg border border-blue-100 bg-blue-50/60 p-3">
            <strong className="text-blue-800">SUPER ADMIN</strong><br />
            Dapat mereset password seluruh user. Reset membatalkan semua sesi user tersebut.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
