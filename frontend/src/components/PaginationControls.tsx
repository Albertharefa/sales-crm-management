import { Button } from "@/components/ui/button";

const PAGE_SIZES = [25, 50, 100] as const;

export default function PaginationControls({
  page,
  pageSize,
  total,
  onPage,
  onPageSize,
  testId,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
  onPageSize: (pageSize: number) => void;
  testId: string;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const firstItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastItem = total === 0 ? 0 : Math.min(page * pageSize, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-4 py-3 text-xs text-slate-500">
      <div className="flex items-center gap-3">
        <select
          className="h-9 rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 outline-none focus:border-blue-500"
          value={pageSize}
          onChange={(e) => onPageSize(Number(e.target.value))}
          aria-label="Jumlah data per halaman"
          data-testid={testId + "-page-size"}
        >
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>{size} / halaman</option>
          ))}
        </select>
        <span data-testid={testId + "-pagination-summary"}>
          {total === 0 ? "Tidak ada data" : "Menampilkan " + firstItem + "–" + lastItem + " dari " + total + " data"}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="icon-sm"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          aria-label="Halaman sebelumnya"
          data-testid={testId + "-previous-page"}
        >
          ‹
        </Button>
        <span className="min-w-10 text-center font-medium text-slate-700" data-testid={testId + "-current-page"}>
          {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="icon-sm"
          disabled={page >= totalPages || total === 0}
          onClick={() => onPage(page + 1)}
          aria-label="Halaman berikutnya"
          data-testid={testId + "-next-page"}
        >
          ›
        </Button>
      </div>
    </div>
  );
}
