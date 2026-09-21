import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Download, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (ch === '"') {
      if (quoted && next === '"') { cell += '"'; i += 1; }
      else quoted = !quoted;
    } else if (ch === "," && !quoted) {
      row.push(cell); cell = "";
    } else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && next === "\n") i += 1;
      row.push(cell); cell = "";
      if (row.some((v) => v.length > 0)) rows.push(row);
      row = [];
    } else {
      cell += ch;
    }
  }
  if (cell.length || row.length) { row.push(cell); rows.push(row); }
  return rows;
}

function csvFilename(source: string) {
  const endpoint = source.split("?")[0].split("/").filter(Boolean).pop() || "export";
  return `${endpoint}.csv`;
}

export default function CsvPreview() {
  const params = new URLSearchParams(window.location.search);
  const source = params.get("source") || "";
  const title = params.get("title") || "CSV Export Preview";
  const [csv, setCsv] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    if (!source) { setError("Sumber CSV tidak ditemukan."); setLoading(false); return; }
    setLoading(true); setError("");
    try {
      const response = await fetch(source, { credentials: "include" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setCsv(await response.text());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengambil data CSV.");
    } finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, [source]);

  const rows = useMemo(() => parseCsv(csv), [csv]);
  const headers = rows[0] || [];
  const dataRows = rows.slice(1);

  const download = () => {
    const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = csvFilename(source);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-5 md:p-8">
      <div className="mx-auto max-w-[1600px]">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
            <p className="mt-1 text-sm text-slate-500">Preview data CSV sebelum di-download</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => window.close()} title="Kembali"><ArrowLeft className="mr-2 size-4" />Kembali</Button>
            <Button variant="outline" onClick={() => void load()} disabled={loading} title="Refresh"><RefreshCw className="mr-2 size-4" />Refresh</Button>
            <Button onClick={download} disabled={loading || !csv} title="Download CSV"><Download className="mr-2 size-4" />Download CSV</Button>
          </div>
        </div>

        {loading ? (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-slate-500">Memuat preview CSV...</div>
        ) : error ? (
          <div className="rounded-xl border border-red-200 bg-white p-12 text-center text-red-600">Gagal memuat CSV: {error}</div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="max-h-[calc(100vh-170px)] overflow-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="sticky top-0 z-10 border-b border-slate-200 bg-slate-50">
                  <tr>{headers.map((header, index) => <th key={`${header}-${index}`} className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-600">{header || `Kolom ${index + 1}`}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {dataRows.map((row, rowIndex) => <tr key={rowIndex} className="hover:bg-slate-50">{headers.map((_, colIndex) => <td key={colIndex} className="whitespace-nowrap px-4 py-3 text-slate-700">{row[colIndex] ?? ""}</td>)}</tr>)}
                  {!dataRows.length && <tr><td colSpan={Math.max(headers.length, 1)} className="px-4 py-10 text-center text-slate-400">CSV tidak berisi data.</td></tr>}
                </tbody>
              </table>
            </div>
            <div className="border-t border-slate-200 px-4 py-3 text-xs text-slate-500">{dataRows.length.toLocaleString("id-ID")} baris data</div>
          </div>
        )}
      </div>
    </div>
  );
}
