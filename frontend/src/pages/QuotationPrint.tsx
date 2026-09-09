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
    <div className="min-h-screen bg-slate-100 py-4 sm:py-6">
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

      <main className="quotation-paper mx-auto flex min-h-[297mm] w-full max-w-[210mm] flex-col bg-white px-7 py-6 text-[11px] text-slate-800 shadow-sm sm:px-8">
        <header className="border-b-2 border-slate-900 pb-3">
          <div className="flex items-start justify-between gap-5">
            <div className="flex items-start gap-3">
              <img
                src="/wellracom-logo.svg"
                alt="Wellracom"
                className="size-[54px] shrink-0 object-contain"
              />
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
            <div className="min-w-[170px] text-right">
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
        </header>

        <section className="mt-5 grid grid-cols-[1fr_175px] gap-6">
          <div>
            <span className="inline-flex rounded-full border border-slate-300 px-2 py-0.5 text-[9px] font-medium text-slate-600">
              {q.status}
            </span>

            <div className="mt-7 text-[10px] leading-relaxed">
              <div className="font-semibold uppercase text-slate-500">TO:</div>
              <div className="mt-1 font-semibold text-slate-900">{customerName}</div>
              <div>ATTN: {pic}</div>
              <div>EMAIL: {email}</div>
              <div>PHONE: {phone}</div>
              {address && <div>{address}</div>}
            </div>
          </div>

          <div className="border border-slate-700 text-[10px]">
            <div className="grid grid-cols-[1fr_1fr] border-b border-slate-700">
              <div className="bg-slate-100 px-2 py-1 font-semibold">DATE</div>
              <div className="px-2 py-1">{dateId(q.date)}</div>
            </div>
            <div className="grid grid-cols-[1fr_1fr] border-b border-slate-700">
              <div className="bg-slate-100 px-2 py-1 font-semibold">QUOTE NO</div>
              <div className="px-2 py-1 font-mono">{q.number}</div>
            </div>
            <div className="grid grid-cols-[1fr_1fr]">
              <div className="bg-slate-100 px-2 py-1 font-semibold">EXPIRATION DATE</div>
              <div className="px-2 py-1">{dateId(q.valid_until)}</div>
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
          <div className="grid grid-cols-2 gap-8">
            <div>
              <div className="font-semibold text-slate-700">JAKARTA OFFICE</div>
              Epicentrum Walk Office, Rasuna Epicentrum Kuningan, Jakarta
              <br />
              T. 021 2991 4981 / 021 7145 9144
            </div>
            <div>
              <div className="font-semibold text-slate-700">SURABAYA OFFICE</div>
              Jl. Bratang Binangun 83, Surabaya 60284
              <br />
              T. 031 5028 999
            </div>
          </div>
        </footer>
      </main>

      <style>{`
        @media print {
          @page {
            size: A4;
            margin: 0;
          }
          html, body {
            background: #fff !important;
          }
          body {
            margin: 0 !important;
          }
          .no-print {
            display: none !important;
          }
          .quotation-paper {
            max-width: none !important;
            width: 210mm !important;
            min-height: 297mm !important;
            margin: 0 !important;
            padding: 12mm !important;
            box-shadow: none !important;
          }
        }
      `}</style>
    </div>
  );
}
