import { Button } from "@/components/ui/button";
import PaginationControls from "@/components/PaginationControls";

export interface Column<T> { key: string; label: string; render: (item: T) => React.ReactNode }

export default function DataTable<T extends { id: string }>({
  columns,
  items,
  loading,
  empty,
  testId,
  total,
  page = 1,
  pageSize = 25,
  onPage,
  onPageSize,
}: {
  columns: Column<T>[];
  items: T[];
  loading?: boolean;
  empty?: string;
  testId: string;
  total?: number;
  page?: number;
  pageSize?: number;
  onPage?: (page: number) => void;
  onPageSize?: (pageSize: number) => void;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" data-testid={testId}>
      <div className="overflow-x-auto">
        <table className="crm-data-table w-full table-fixed text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="crm-data-table-no whitespace-nowrap px-3 py-2.5 font-semibold">No</th>
              {columns.map(column => <th key={column.key} className="whitespace-nowrap px-3 py-2.5 font-semibold">{column.label}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td colSpan={columns.length + 1} className="px-4 py-12 text-center text-slate-400">Memuat data...</td></tr>
            ) : items.length ? (
              items.map(item => (
                <tr key={item.id} className="hover:bg-slate-50" data-testid={testId + "-row-" + item.id}>
                  <td className="crm-data-table-no whitespace-nowrap px-3 py-2.5 text-slate-500">{(page - 1) * pageSize + items.indexOf(item) + 1}</td>
                  {columns.map(column => <td key={column.key} className="crm-data-table-cell whitespace-nowrap px-3 py-2.5">{column.render(item)}</td>)}
                </tr>
              ))
            ) : (
              <tr><td colSpan={columns.length + 1} className="px-4 py-12 text-center text-slate-400">{empty ?? "Belum ada data"}</td></tr>
            )}
          </tbody>
        </table>
      </div>
      {total !== undefined && onPage && onPageSize && (
        <PaginationControls
          page={page}
          pageSize={pageSize}
          total={total}
          onPage={onPage}
          onPageSize={onPageSize}
          testId={testId}
        />
      )}
    </div>
  );
}
