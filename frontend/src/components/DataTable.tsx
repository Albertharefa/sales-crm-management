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
  return (
    <div className="crm-data-table-card flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" data-testid={testId}>
      <div
        className="crm-data-table-viewport min-h-[180px] max-h-[calc(100svh-22rem)] min-w-0 flex-1 overflow-auto overscroll-contain"
        style={{ scrollbarGutter: "stable both-edges", WebkitOverflowScrolling: "touch" }}
      >
        <table className="crm-data-table min-w-full table-auto text-left text-sm">
          <thead className="sticky top-0 z-10 border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="crm-data-table-no whitespace-nowrap px-3 py-2.5 font-semibold">No</th>
              {columns.map(column => <th key={column.key} className="whitespace-nowrap px-3 py-2.5 font-semibold">{column.label}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? <TableSkeleton columns={columns.length} /> : items.length ? items.map((item, index) => (
              <tr key={item.id} className="hover:bg-slate-50" data-testid={testId + "-row-" + item.id}>
                <td className="crm-data-table-no whitespace-nowrap px-3 py-2.5 text-slate-500">{(page - 1) * pageSize + index + 1}</td>
                {columns.map(column => <td key={column.key} className="crm-data-table-cell whitespace-nowrap px-3 py-2.5">{column.render(item)}</td>)}
              </tr>
            )) : <tr><td colSpan={columns.length + 1} className="px-4 py-12 text-center text-slate-400">{empty ?? "Belum ada data"}</td></tr>}
          </tbody>
        </table>
      </div>
      {total !== undefined && onPage && onPageSize && <PaginationControls page={page} pageSize={pageSize} total={total} onPage={onPage} onPageSize={onPageSize} testId={testId} />}
    </div>
  );
}
