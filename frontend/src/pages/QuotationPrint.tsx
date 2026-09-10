import { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Printer, FileText } from "lucide-react";
import { apiGet } from "@/lib/api";
import type { Customer, Quotation } from "@/lib/types";
import { Button } from "@/components/ui/button";

const money = (value: number) =>
  new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);

const dateId = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
};

export default function QuotationPrint() {
  const { quotationId } = useParams<{ quotationId: string }>();
  const navigate = useNavigate();

  const quotation = useQuery({
    queryKey: ["quotation-print", quotationId],
    queryFn: () => apiGet<Quotation>(`/quotations/${quotationId}`),
    enabled: !!quotationId,
  });

  const customer = useQuery({
    queryKey: ["quotation-print-customer", quotation.data?.customer_id],
    queryFn: () =>
      apiGet<Customer>(`/customers/${quotation.data?.customer_id}`),
    enabled: !!quotation.data?.customer_id,
  });

  const q = quotation.data;

  const itemRows = useMemo(() => q?.items ?? [], [q?.items]);

  if (quotation.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 text-slate-500">
        Memuat quotation...
      </div>
    );
  }

  if (!q) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="text-center">
          <div className="text-lg font-semibold">Quotation tidak ditemukan</div>
          <Button className="mt-4" onClick={() => navigate("/quotations")}>
            Kembali
          </Button>
        </div>
      </div>
    );
  }

  const customerName =
    customer.data?.company_name || customer.data?.company || q.customer_name;
  const pic = customer.data?.pic_name || "—";
  const email = customer.data?.email || "—";
  const phone = customer.data?.phone || "—";
  const address = [
    customer.data?.address,
    customer.data?.city,
    customer.data?.province,
  ]
    .filter(Boolean)
    .join(", ");

  return (
    <div className="quotation-print-root min-h-screen bg-slate-100 py-4 sm:py-6">
      <div className="no-print mx-auto mb-4 flex max-w-[210mm] items-center justify-between gap-2 px-2">
        <Button variant="outline" onClick={() => navigate("/quotations")}>
          <ArrowLeft className="mr-2 size-4" />
          Kembali
        </Button>
        <Button onClick={() => window.print()}>
          <Printer className="mr-2 size-4" />
          Cetak / Simpan PDF
        </Button>
      </div>

      <main className="quotation-paper relative mx-auto flex min-h-[297mm] w-full max-w-[210mm] flex-col bg-white px-7 py-6 text-[11px] text-slate-800 shadow-sm sm:px-8">
        <header className="border-b-2 border-slate-900 pb-3">
          <div className="flex items-start gap-3">
            <div
              aria-label="Wellracom"
              className="size-[54px] shrink-0 overflow-hidden"
            >
              <svg
                viewBox="0 0 225 225"
                role="img"
                aria-label="Wellracom logo"
                className="size-full"
              >
                <circle cx="112.5" cy="112.5" r="101.5" fill="#fff" stroke="#111" strokeWidth="6" />
                <path
                  fill="#ff9800"
                  d="M38 54h20l34 70 20.5-40 20.5 40 34-70h20l-43 91-31.5-61-31.5 61z"
                />
                <path
                  fill="#111"
                  d="M87 50h51l-10 20-15.5 23-15.5-23zm12 6 13.5 26 13.5-26z"
                />
                <path fill="#111" d="M109.5 92h6v57h-6z" />
                <path fill="#111" d="M86 151h53l-6 10H92z" />
                <path fill="#111" d="M101 167h23l-11.5 22z" />
              </svg>
            </div>
            <div className="pt-0.5">
              <div className="text-[17px] font-bold tracking-tight text-slate-900">
                PT WELLRACOM INDUSTRI KOMPUTINDO
              </div>
              <div className="mt-0.5 text-[9px] leading-relaxed text-slate-500">
                Industrial Computing • Automation • Communication
                <br />
                www.wellracom.co.id · info@wellracom.co.id
              </div>
            </div>
          </div>
        </header>

        <section className="mt-5">
          <span className="inline-flex rounded-full border border-slate-300 px-2 py-0.5 text-[9px] font-medium text-slate-600">
            {q.status}
          </span>

          <div className="mt-5 grid grid-cols-[1fr_230px] items-start gap-6 text-[10px] leading-relaxed">
            <div>
              <div className="font-semibold uppercase text-slate-500">TO:</div>
              <div className="mt-1 font-semibold text-slate-900">{customerName}</div>
              <div>ATTN: {pic}</div>
              <div>EMAIL: {email}</div>
              <div>PHONE: {phone}</div>
              {address && <div>{address}</div>}
            </div>

            <div className="pt-1 text-right">
              <div className="text-[22px] font-bold tracking-[0.08em] text-slate-900">
                QUOTATION
              </div>
              <div className="mt-1 text-[10px] text-slate-700">
                No: <span className="font-mono font-semibold">{q.number}</span>
              </div>
              <div className="text-[10px] text-slate-700">
                Date: <span className="font-semibold">{dateId(q.date)}</span>
              </div>
              <div className="text-[10px] text-slate-700">
                Valid Until: <span className="font-semibold">{dateId(q.valid_until)}</span>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-7">
          <table className="w-full border-collapse text-[9px]">
            <thead>
              <tr className="bg-slate-900 text-white">
                <th className="w-9 border border-slate-900 px-2 py-2 text-center">NO</th>
                <th className="border border-slate-900 px-2 py-2 text-left">ITEMS / SPECIFICATION</th>
                <th className="w-28 border border-slate-900 px-2 py-2 text-right">UNIT PRICE</th>
                <th className="w-16 border border-slate-900 px-2 py-2 text-center">QTY</th>
                <th className="w-28 border border-slate-900 px-2 py-2 text-right">AMOUNT</th>
              </tr>
            </thead>
            <tbody>
              {itemRows.map((item, index) => (
                <tr key={index}>
                  <td className="border border-slate-300 px-2 py-2 text-center">{index + 1}</td>
                  <td className="whitespace-pre-line border border-slate-300 px-2 py-2 align-top">
                    {item.description}
                  </td>
                  <td className="border border-slate-300 px-2 py-2 text-right font-mono">
                    {money(item.unit_price)}
                  </td>
                  <td className="border border-slate-300 px-2 py-2 text-center">
                    {item.quantity} Unit
                  </td>
                  <td className="border border-slate-300 px-2 py-2 text-right font-mono">
                    {money(item.quantity * item.unit_price)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="mt-5 ml-auto w-[280px] text-[10px]">
          <div className="flex justify-between py-1">
            <span>SUBTOTAL</span>
            <span className="font-mono">{money(q.subtotal)}</span>
          </div>
          <div className="flex justify-between py-1">
            <span>DISKON</span>
            <span className="font-mono">- {money(q.discount_total)}</span>
          </div>
          <div className="flex justify-between py-1">
            <span>PPN {q.tax_total && q.subtotal - q.discount_total > 0 ? "11%" : ""}</span>
            <span className="font-mono">{money(q.tax_total)}</span>
          </div>
          <div className="mt-1 flex justify-between bg-slate-900 px-2 py-2 font-bold text-white">
            <span>GRAND TOTAL</span>
            <span className="font-mono">{money(q.grand_total)}</span>
          </div>
        </section>

        <section className="mt-8 grid grid-cols-[1fr_190px] gap-8 text-[9px]">
          <div>
            <div className="font-semibold uppercase tracking-wide">TERMS AND CONDITIONS:</div>
            <ol className="mt-2 list-decimal space-y-1 pl-4 leading-relaxed">
              <li>Payment: {q.payment_term || "30 hari setelah invoice"}</li>
              <li>Pengiriman: {q.delivery_term || "4–6 minggu setelah PO"}</li>
              <li>Harga FOB Jakarta</li>
              <li>Validitas: s/d {dateId(q.valid_until)}</li>
            </ol>
            {q.notes && (
              <div className="mt-4">
                <div className="font-semibold uppercase tracking-wide">CATATAN:</div>
                <div className="mt-1 whitespace-pre-line leading-relaxed">{q.notes}</div>
              </div>
            )}
          </div>

          <div className="text-center">
            <div className="mb-16">Hormat kami, PT WELLRACOM INDUSTRI KOMPUTINDO</div>
            <div className="border-t border-slate-500 pt-1 font-semibold">
              {q.sales_name || "Sales"}
            </div>
            <div className="text-slate-500">Sales Representative</div>
          </div>
        </section>

        <footer className="mt-auto border-t-2 border-slate-900 pt-3 text-[8px] text-slate-500">
          <div className="flex items-start justify-between gap-8">
            <div className="text-left">
              <div className="font-semibold text-slate-700">Jakarta Office :</div>
              Epincentrum Walk A707
              <br />
              Rasuna Epicentrum Kuningan
              <br />
              Jl. HR Rasuna Said, Jakarta
              <br />
              Telp : 021-2994 1841
            </div>
            <div className="text-right">
              <div className="font-semibold text-slate-700">Surabaya Office :</div>
              Jl. Bratang Binangun 83, Surabaya 60284
              <br />
              Phone : 031-502-8999
            </div>
          </div>
          <div className="mt-2 text-center text-[7px] italic text-slate-500">
            This document is digitally generated
          </div>
        </footer>
      </main>

      <style>{`
        @media print {
          @page {
            size: A4 portrait;
            margin: 0;
          }

          html,
          body,
          #root {
            background: #fff !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            min-height: 0 !important;
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
          }

          .no-print {
            display: none !important;
          }

          body > *:not(#root) {
            display: none !important;
            visibility: hidden !important;
          }

          #root {
            position: relative !important;
            z-index: 0 !important;
            isolation: isolate !important;
          }

          .quotation-print-root,
          .quotation-print-root * {
            visibility: visible !important;
          }

          .quotation-print-root {
            box-sizing: border-box !important;
            width: 100% !important;
            min-height: 0 !important;
            height: auto !important;
            max-height: none !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
            background: #fff !important;
            page-break-after: auto !important;
            break-after: auto !important;
          }

          .quotation-paper {
            box-sizing: border-box !important;
            position: relative !important;
            width: 210mm !important;
            max-width: 210mm !important;
            min-height: 277mm !important;
            height: auto !important;
            max-height: none !important;
            margin: 0 auto !important;
            padding: 9mm !important;
            box-shadow: none !important;
            overflow: visible !important;
            page-break-after: auto !important;
            break-after: auto !important;
          }

          .quotation-paper header {
            padding-bottom: 2.5mm !important;
          }

          .quotation-paper section {
            page-break-inside: auto !important;
            break-inside: auto !important;
          }

          .quotation-paper table {
            width: 100% !important;
            border-collapse: collapse !important;
            page-break-inside: auto !important;
          }

          .quotation-paper thead {
            display: table-header-group !important;
          }

          .quotation-paper tbody {
            display: table-row-group !important;
          }

          .quotation-paper tr {
            page-break-inside: avoid !important;
            break-inside: avoid-page !important;
          }

          .quotation-paper th,
          .quotation-paper td {
            overflow-wrap: anywhere !important;
            word-break: normal !important;
          }

          .quotation-paper footer {
            position: static !important;
            left: auto !important;
            right: auto !important;
            bottom: auto !important;
            margin-top: 8mm !important;
            page-break-inside: avoid !important;
            break-inside: avoid-page !important;
          }
        }
      `}</style>
    </div>
  );
}
