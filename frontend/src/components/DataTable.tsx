import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import PaginationControls from "@/components/PaginationControls";

export interface Column<T> { key: string; label: string; render: (item: T) => React.ReactNode }

function TableSkeleton({ columns }: { columns: number }) {
  return (
    <>
      {Array.from({ length: 5 }).map((_, row) => (
        <tr key={row} className="animate-pulse">
          <td className="px-3 py-2.5"><div className="h-3 w-6 rounded bg-slate-200" /></td>
          {Array.from({ length: columns }).map((__, col) => (
            <td key={col} className="px-3 py-2.5"><div className={`h-3 rounded bg-slate-200 ${col === 0 ? "w-32" : "w-20"}`} /></td>
          ))}
        </tr>
      ))}
    </>
  );
}

export default function DataTable<T extends { id: string }>({
  columns, items, loading, empty, testId, total, page = 1, pageSize = 25, onPage, onPageSize,
}: {
  columns: Column<T>[]; items: T[]; loading?: boolean; empty?: string; testId: string;
  total?: number; page?: number; pageSize?: number; onPage?: (page: number) => void; onPageSize?: (pageSize: number) => void;
}) {
  const [globalSearch, setGlobalSearch] = useState("");
  const hasGlobalSearch = testId === "users-table" || testId === "audit-log-table";
  const filteredItems = useMemo(() => {
    if (!hasGlobalSearch || !globalSearch.trim()) return items;
    const keyword = globalSearch.trim().toLowerCase();
    return items.filter(item => Object.values(item as Record<string, unknown>).some(value => {
      if (value === null || value === undefined) return false;
      return (typeof value === "object" ? JSON.stringify(value) : String(value)).toLowerCase().includes(keyword);
    }));
  }, [hasGlobalSearch, globalSearch, items]);
  const expandedHeight = testId === "users-table" || testId === "audit-log-table";
  return (
    <div className="crm-data-table-card flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" data-testid={testId}>
      {hasGlobalSearch && (
        <div className="border-b border-slate-200 bg-white p-3">
          <div className="relative max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <input
              value={globalSearch}
              onChange={event => setGlobalSearch(event.target.value)}
              placeholder={testId === "users-table" ? "Cari nama, User ID, email, role..." : "Cari user, aksi, modul, record..."}
              className="h-10 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              data-testid={`${testId}-search-input`}
            />
          </div>
        </div>
      )}
      <div
        className="crm-data-table-viewport min-w-0 overflow-auto overscroll-contain"
        style={{
          height: expandedHeight ? "calc(100svh - 260px)" : "clamp(240px, calc(100svh - 380px), 520px)",
          maxHeight: expandedHeight ? "calc(100svh - 260px)" : "calc(100svh - 380px)",
          scrollbarGutter: "stable both-edges",
          WebkitOverflowScrolling: "touch",
        }}
      >
        <table className="crm-data-table min-w-full table-auto text-left text-sm">
          <thead className="sticky top-0 z-10 border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="crm-data-table-no whitespace-nowrap px-3 py-2.5 font-semibold">No</th>
              {columns.map(column => <th key={column.key} className="whitespace-nowrap px-3 py-2.5 font-semibold">{column.label}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? <TableSkeleton columns={columns.length} /> : filteredItems.length ? filteredItems.map((item, index) => (
              <tr key={item.id} className="hover:bg-slate-50" data-testid={testId + "-row-" + item.id}>
                <td className="crm-data-table-no whitespace-nowrap px-3 py-2.5 text-slate-500">{(page - 1) * pageSize + index + 1}</td>
                {columns.map(column => <td key={column.key} className="crm-data-table-cell whitespace-nowrap px-3 py-2.5">{column.render(item)}</td>)}
              </tr>
            )) : <tr><td colSpan={columns.length + 1} className="px-4 py-12 text-center text-slate-400">{globalSearch.trim() ? "Data tidak ditemukan" : (empty ?? "Belum ada data")}</td></tr>}
          </tbody>
        </table>
      </div>
      {!globalSearch.trim() && total !== undefined && onPage && onPageSize && <PaginationControls page={page} pageSize={pageSize} total={total} onPage={onPage} onPageSize={onPageSize} testId={testId} />}
    </div>
  );
}
