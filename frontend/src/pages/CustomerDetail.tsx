import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { apiGet } from "@/lib/api";
import type { Activity, Contact, Customer, Opportunity, Paginated, PurchaseOrder, Quotation } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Building2, CalendarDays, Mail, MapPin, Phone, UserRound } from "lucide-react";

type CustomerActivity = Activity & { customer_id?: string };

const money = (value: number) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(value || 0);

const dateText = (value?: string | null) => {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" });
};

export default function CustomerDetail() {
  const { customerId } = useParams<{ customerId: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState("pipeline");

  const customerQuery = useQuery({
    queryKey: ["customer-detail-page", customerId],
    queryFn: () => apiGet<Customer>(`/customers/${customerId}`),
    enabled: !!customerId,
  });

  const contactsQuery = useQuery({
    queryKey: ["customer-detail-page-contacts", customerId],
    queryFn: () => apiGet<Contact[]>(`/customers/${customerId}/contacts`),
    enabled: !!customerId,
  });

  const pipelineQuery = useQuery({
    queryKey: ["customer-detail-page-pipeline", customerId],
    queryFn: () => apiGet<Paginated<Opportunity>>(`/pipeline?page=1&page_size=100&customer_id=${encodeURIComponent(customerId || "")}`),
    enabled: !!customerId,
  });

  const quotationsQuery = useQuery({
    queryKey: ["customer-detail-page-quotations", customerId, customerQuery.data?.name],
    queryFn: () => apiGet<Paginated<Quotation>>(`/quotations?page=1&page_size=100&search=${encodeURIComponent(customerQuery.data?.name || "")}`),
    enabled: !!customerQuery.data?.name,
  });

  const ordersQuery = useQuery({
    queryKey: ["customer-detail-page-orders", customerId, customerQuery.data?.name],
    queryFn: () => apiGet<Paginated<PurchaseOrder>>(`/purchase-orders?page=1&page_size=100&search=${encodeURIComponent(customerQuery.data?.name || "")}`),
    enabled: !!customerQuery.data?.name,
  });

  const activitiesQuery = useQuery({
    queryKey: ["customer-detail-page-activities", customerId, customerQuery.data?.name],
    queryFn: () => apiGet<Paginated<CustomerActivity>>(`/activities?page=1&page_size=100&search=${encodeURIComponent(customerQuery.data?.name || "")}`),
    enabled: !!customerQuery.data?.name,
  });

  const customer = customerQuery.data;
  const contacts = contactsQuery.data ?? [];
  const pipeline = pipelineQuery.data?.items ?? [];
  const quotations = quotationsQuery.data?.items ?? [];
  const orders = ordersQuery.data?.items ?? [];
  const activities = activitiesQuery.data?.items ?? [];

  const stats = useMemo(() => ({
    pipeline: pipeline.reduce((sum, x) => sum + (x.value || 0), 0),
    quotations: quotations.reduce((sum, x) => sum + (x.grand_total || 0), 0),
    orders: orders.reduce((sum, x) => sum + (x.total || 0), 0),
  }), [pipeline, quotations, orders]);

  if (customerQuery.isLoading) {
    return <div className="flex min-h-[70vh] items-center justify-center text-slate-500">Memuat detail customer...</div>;
  }

  if (customerQuery.isError || !customer) {
    return (
      <div className="space-y-4">
        <Button variant="outline" onClick={() => navigate("/customers")}><ArrowLeft className="mr-2 size-4" /> Kembali ke daftar</Button>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-600">Gagal mengambil detail customer.</div>
      </div>
    );
  }

  const tabs = [
    { id: "pipeline", label: "Sales Pipeline", count: pipeline.length },
    { id: "quotations", label: "Quotations", count: quotations.length },
    { id: "orders", label: "Purchase Orders", count: orders.length },
    { id: "activities", label: "Aktivitas", count: activities.length },
  ];

  return (
    <div className="min-h-full space-y-6 pb-8" data-testid="customer-detail-page">
      <div className="flex items-center justify-between gap-4">
        <button type="button" onClick={() => navigate("/customers")} className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900">
          <ArrowLeft className="size-4" /> Kembali ke daftar
        </button>
        <Badge variant={customer.status === "Active" ? "default" : "secondary"} className="px-3 py-1">{customer.status}</Badge>
      </div>

      <div className="flex flex-col gap-5 border-b border-slate-200 pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 text-sm font-semibold uppercase tracking-wider text-blue-600">Customer</div>
          <h1 className="font-heading text-4xl font-semibold tracking-tight text-slate-900">{customer.name}</h1>
          <div className="mt-2 font-mono text-sm text-slate-500">{customer.customer_id}</div>
        </div>
        <div className="grid grid-cols-3 gap-3 text-right">
          <Stat label="Pipeline" value={money(stats.pipeline)} />
          <Stat label="Quotation" value={money(stats.quotations)} />
          <Stat label="PO" value={money(stats.orders)} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-6 text-base font-semibold uppercase tracking-wider text-slate-800">Customer Information</h2>
          <div className="grid gap-5 sm:grid-cols-2">
            <Info label="Customer ID" value={customer.customer_id} icon={<Building2 className="size-4" />} />
            <Info label="Perusahaan" value={customer.company_name || customer.name} icon={<Building2 className="size-4" />} />
            <Info label="Industri" value={customer.industry} />
            <Info label="Kota / Provinsi" value={[customer.city, customer.province].filter(Boolean).join(" / ")} icon={<MapPin className="size-4" />} />
            <Info label="Sumber" value={customer.source} />
            <Info label="Sales" value={customer.sales_name} icon={<UserRound className="size-4" />} />
            <Info label="Dibuat" value={dateText(customer.created_at)} icon={<CalendarDays className="size-4" />} />
            <Info label="Telepon" value={customer.phone} icon={<Phone className="size-4" />} />
          </div>
          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <LargeInfo label="Alamat" value={customer.address} icon={<MapPin className="size-4" />} />
            <LargeInfo label="Notes" value={customer.notes} />
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-base font-semibold uppercase tracking-wider text-slate-800">Contacts</h2>
            <span className="text-sm text-slate-400">{contacts.length} contact</span>
          </div>
          {contactsQuery.isLoading ? <Loading /> : contacts.length ? (
            <div className="space-y-3">
              {contacts.map((contact) => (
                <div key={contact.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="font-semibold text-slate-900">{[contact.first_name, contact.last_name].filter(Boolean).join(" ") || "—"}</div>
                  <div className="mt-1 text-sm text-slate-500">{contact.position || contact.department || "—"}</div>
                  <div className="mt-3 space-y-1 text-sm text-slate-600">
                    {contact.mobile && <div className="flex items-center gap-2"><Phone className="size-3.5" />{contact.mobile}</div>}
                    {contact.email && <div className="flex items-center gap-2"><Mail className="size-3.5" />{contact.email}</div>}
                  </div>
                </div>
              ))}
            </div>
          ) : <Empty text="Belum ada contact." />}
        </section>
      </div>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex overflow-x-auto border-b border-slate-200 px-5">
          {tabs.map((item) => (
            <button key={item.id} type="button" onClick={() => setTab(item.id)}
              className={`whitespace-nowrap border-b-2 px-4 py-4 text-sm font-medium transition ${tab === item.id ? "border-blue-600 text-slate-900" : "border-transparent text-slate-500 hover:text-slate-800"}`}>
              {item.label}
              <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs">{item.count}</span>
            </button>
          ))}
        </div>
        <div className="p-5">
          {tab === "pipeline" && <PipelineTab data={pipeline} loading={pipelineQuery.isLoading} />}
          {tab === "quotations" && <QuotationTab data={quotations} loading={quotationsQuery.isLoading} />}
          {tab === "orders" && <OrderTab data={orders} loading={ordersQuery.isLoading} />}
          {tab === "activities" && <ActivityTab data={activities} loading={activitiesQuery.isLoading} />}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0"><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{label}</div><div className="mt-1 truncate text-sm font-semibold text-slate-800">{value}</div></div>;
}

function Info({ label, value, icon }: { label: string; value?: string | null; icon?: React.ReactNode }) {
  return <div><div className="mb-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{icon}{label}</div><div className="text-base text-slate-800">{value || "—"}</div></div>;
}

function LargeInfo({ label, value, icon }: { label: string; value?: string | null; icon?: React.ReactNode }) {
  return <div><div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{icon}{label}</div><div className="min-h-20 whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700">{value || "—"}</div></div>;
}

function Loading() { return <div className="rounded-xl border border-slate-200 p-5 text-center text-sm text-slate-400">Memuat data...</div>; }
function Empty({ text }: { text: string }) { return <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400">{text}</div>; }

function PipelineTab({ data, loading }: { data: Opportunity[]; loading: boolean }) {
  if (loading) return <Loading />; if (!data.length) return <Empty text="Belum ada opportunity untuk customer ini." />;
  return <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Opportunity</th><th className="p-3">Stage</th><th className="p-3">Value</th><th className="p-3">Weighted</th><th className="p-3">Target Close</th></tr></thead><tbody className="divide-y">{data.map(x=><tr key={x.id}><td className="p-3 font-medium">{x.name}</td><td className="p-3"><Badge variant="secondary">{x.stage}</Badge></td><td className="p-3">{money(x.value)}</td><td className="p-3">{money((x.value||0)*(x.probability||0)/100)}</td><td className="p-3">{dateText(x.target_close)}</td></tr>)}</tbody></table></div>;
}

function QuotationTab({ data, loading }: { data: Quotation[]; loading: boolean }) {
  if (loading) return <Loading />; if (!data.length) return <Empty text="Belum ada quotation untuk customer ini." />;
  return <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Quotation</th><th className="p-3">Tanggal</th><th className="p-3">Sales</th><th className="p-3">Status</th><th className="p-3 text-right">Grand Total</th></tr></thead><tbody className="divide-y">{data.map(x=><tr key={x.id}><td className="p-3 font-medium">{x.number}</td><td className="p-3">{dateText(x.date)}</td><td className="p-3">{x.sales_name || "—"}</td><td className="p-3"><Badge variant="secondary">{x.status}</Badge></td><td className="p-3 text-right font-semibold">{money(x.grand_total)}</td></tr>)}</tbody></table></div>;
}

function OrderTab({ data, loading }: { data: PurchaseOrder[]; loading: boolean }) {
  if (loading) return <Loading />; if (!data.length) return <Empty text="Belum ada purchase order untuk customer ini." />;
  return <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">PO</th><th className="p-3">Tanggal</th><th className="p-3">Sales</th><th className="p-3">Status</th><th className="p-3 text-right">Total</th></tr></thead><tbody className="divide-y">{data.map(x=><tr key={x.id}><td className="p-3 font-medium">{x.po_number}</td><td className="p-3">{dateText(x.date)}</td><td className="p-3">{x.sales_name || "—"}</td><td className="p-3"><Badge variant="secondary">{x.status}</Badge></td><td className="p-3 text-right font-semibold">{money(x.total)}</td></tr>)}</tbody></table></div>;
}

function ActivityTab({ data, loading }: { data: CustomerActivity[]; loading: boolean }) {
  if (loading) return <Loading />; if (!data.length) return <Empty text="Belum ada aktivitas untuk customer ini." />;
  return <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Aktivitas</th><th className="p-3">Tipe</th><th className="p-3">Tanggal</th><th className="p-3">Sales</th><th className="p-3">Status</th></tr></thead><tbody className="divide-y">{data.map(x=><tr key={x.id}><td className="p-3 font-medium">{x.subject}</td><td className="p-3">{x.activity_type}</td><td className="p-3">{dateText(x.date)}</td><td className="p-3">{x.sales_name || "—"}</td><td className="p-3"><Badge variant="secondary">{x.status}</Badge></td></tr>)}</tbody></table></div>;
}
