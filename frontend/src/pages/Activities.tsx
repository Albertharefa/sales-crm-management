import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@/lib/api";
import type { Activity, Paginated, Task } from "@/lib/types";
import PageHeader from "@/components/PageHeader";
import Modal from "@/components/Modal";
import DataTable from "@/components/DataTable";
import { Field, selectClass } from "@/components/Field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Eye, Pencil, Trash2 } from "lucide-react";


const ACTIVITY_TYPES = [
  "Call",
  "WhatsApp",
  "Email",
  "Meeting",
  "Visit",
  "Presentation",
  "Follow Up",
  "Other",
];


export default function Activities() {
  const [mode, setMode] = useState("activities");
  const [modal, setModal] = useState(false);
  const [detailModal, setDetailModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [selectedActivityId, setSelectedActivityId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [activityFilter, setActivityFilter] = useState("");
  const [activityType, setActivityType] = useState("");
  const [status, setStatus] = useState("");
  const [salesId, setSalesId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const [form, setForm] = useState({
    subject: "",
    activity_type: "Call",
    date: new Date().toISOString().slice(0, 10),
    customer_id: "",
    opportunity_id: "",
    next_follow_up: "",
    status: "Open",
    description: "",
  });

  const qc = useQueryClient();

  const activityParams = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  if (search.trim()) activityParams.set("search", search.trim());
  if (activityFilter) activityParams.set("activity_filter", activityFilter);
  if (activityType) activityParams.set("activity_type", activityType);
  if (status) activityParams.set("status", status);
  if (salesId) activityParams.set("sales_id", salesId);
  if (customerId) activityParams.set("customer_id", customerId);

  const activities = useQuery({
    queryKey: [
      "activities",
      page,
      pageSize,
      search,
      activityFilter,
      activityType,
      status,
      salesId,
      customerId,
    ],
    queryFn: () =>
      apiGet<Paginated<Activity>>(
        `/activities?${activityParams.toString()}`
      ),
  });

  const activitySummary = useQuery({
    queryKey: ["activities-summary"],
    queryFn: () =>
      apiGet<{
        today: number;
        upcoming: number;
        overdue: number;
        completed: number;
      }>("/activities/summary"),
  });

  const tasks = useQuery({
    queryKey: ["tasks", page, pageSize],
    queryFn: () =>
      apiGet<Paginated<Task>>(
        `/activities/tasks?page=${page}&page_size=${pageSize}`
      ),
  });

  const customerOptions = useQuery({
    queryKey: ["activities-customer-options"],
    queryFn: () =>
      apiGet<{ id: string; name: string }[]>("/activities/customer-options"),
    staleTime: 60_000,
  });

  const activityDetail = useQuery({
    queryKey: ["activity-detail", selectedActivityId],
    queryFn: () => apiGet<Activity>(`/activities/${selectedActivityId}`),
    enabled: !!selectedActivityId && (detailModal || editModal),
  });

  const openDetail = (id: string) => {
    setSelectedActivityId(id);
    setDetailModal(true);
  };

  const closeDetail = () => {
    setDetailModal(false);
    setSelectedActivityId(null);
  };

  const openEdit = (id: string) => {
    setSelectedActivityId(id);
    setEditModal(true);
  };

  const closeEdit = () => {
    setEditModal(false);
    setSelectedActivityId(null);
  };

  const opportunityOptions = useQuery({
    queryKey: ["activities-opportunity-options", form.customer_id],
    queryFn: () => apiGet<{ id: string; opportunity_id: string; name: string; customer_id: string; stage: string }[]>(`/activities/opportunity-options${form.customer_id ? `?customer_id=${encodeURIComponent(form.customer_id)}` : ""}`),
    staleTime: 30_000,
    enabled: modal,
  });

  const salesOptions = useQuery({
    queryKey: ["activities-sales-options"],
    queryFn: () =>
      apiGet<{ id: string; name: string }[]>("/activities/sales-options"),
    staleTime: 60_000,
  });

  const updateActivity = useMutation({
    mutationFn: (values: {
      subject: string;
      activity_type: string;
      date: string;
      next_follow_up: string | null;
      status: string;
      description: string;
    }) =>
      apiPut<Activity>(`/activities/${selectedActivityId}`, values),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["activities"] });
      qc.invalidateQueries({ queryKey: ["activities-summary"] });
      qc.invalidateQueries({ queryKey: ["activity-detail", selectedActivityId] });
      closeEdit();
      toast.success("Aktivitas berhasil diperbarui");
    },
    onError: () => toast.error("Aktivitas gagal diperbarui"),
  });

  const removeActivity = useMutation({
    mutationFn: (id: string) => apiDelete<void>(`/activities/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["activities"] });
      qc.invalidateQueries({ queryKey: ["activities-summary"] });
      closeDetail();
      toast.success("Aktivitas dihapus");
    },
    onError: () => toast.error("Aktivitas gagal dihapus"),
  });

  const create = useMutation({
    mutationFn: () =>
      apiPost<Activity>("/activities", {
        ...form,
        customer_id: form.customer_id || null,
        opportunity_id: form.opportunity_id || null,
        next_follow_up: form.next_follow_up || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["activities"] });
      qc.invalidateQueries({ queryKey: ["activities-summary"] });
      setModal(false);
      toast.success("Aktivitas berhasil ditambahkan");
    },
    onError: () => toast.error("Aktivitas gagal disimpan"),
  });

  const completeTask = useMutation({
    mutationFn: (id: string) =>
      apiPatch<Task>(`/activities/tasks/${id}?status=Completed`),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const refreshPage = async () => {
    if (mode === "activities") {
      await Promise.all([
        activities.refetch(),
        activitySummary.refetch(),
        salesOptions.refetch(),
        customerOptions.refetch(),
        opportunityOptions.refetch(),
      ]);
      toast.success("Aktivitas Sales berhasil diperbarui");
    } else {
      await tasks.refetch();
      toast.success("Tasks berhasil diperbarui");
    }
  };

  const resetFilters = () => {
    setSearch("");
    setActivityFilter("");
    setActivityType("");
    setStatus("");
    setSalesId("");
    setCustomerId("");
    setPage(1);
  };

  const summary = activitySummary.data ?? {
    today: 0,
    upcoming: 0,
    overdue: 0,
    completed: 0,
  };

  return (
    <div data-testid="activities-page">
      <PageHeader
        title="Aktivitas Sales"
        description="Call, meeting, visit, dan jadwal follow-up"
        action={{
          label: "Tambah Aktivitas",
          onClick: () => setModal(true),
        }}
        onRefresh={refreshPage}
        onExport={() =>
          window.open("/api/v1/exports/activities", "_blank")
        }
      />

      <div className="mb-5 crm-summary-grid">
        {[
          ["HARI INI", summary.today],
          ["FOLLOW-UP MENDATANG", summary.upcoming],
          ["FOLLOW-UP TERLAMBAT", summary.overdue],
          ["SELESAI", summary.completed],
        ].map(([label, value]) => (
          <Card key={label} className="border-slate-200 shadow-none">
            <CardContent className="p-5">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {label}
              </div>
              <div className="mt-8 font-mono text-2xl font-semibold text-slate-900">
                {value}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mb-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <Tabs
          value={mode}
          onValueChange={(value) => {
            setMode(value);
            setPage(1);
          }}
        >
          <TabsList>
            <TabsTrigger value="activities" data-testid="activities-tab">
              Aktivitas
            </TabsTrigger>
            <TabsTrigger value="tasks" data-testid="tasks-tab">
              Tasks
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {mode === "activities" && (
          <>
            <div className="mt-3 crm-filter-grid">
              <Input
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                placeholder="Cari subjek / customer..."
                data-testid="activities-search-input"
              />

              <select
                className={selectClass}
                value={activityFilter}
                onChange={(e) => {
                  setActivityFilter(e.target.value);
                  setPage(1);
                }}
                data-testid="activities-filter"
              >
                <option value="">Semua aktivitas</option>
                <option value="today">Hari ini</option>
                <option value="upcoming">Follow-up mendatang</option>
                <option value="overdue">Follow-up terlambat</option>
                <option value="completed">Selesai</option>
              </select>

              <select
                className={selectClass}
                value={activityType}
                onChange={(e) => {
                  setActivityType(e.target.value);
                  setPage(1);
                }}
                data-testid="activities-type-filter"
              >
                <option value="">Semua tipe</option>
                {ACTIVITY_TYPES.map((type) => (
                  <option key={type}>{type}</option>
                ))}
              </select>

              <select
                className={selectClass}
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  setPage(1);
                }}
                data-testid="activities-status-filter"
              >
                <option value="">Semua status</option>
                <option value="Open">Open</option>
                <option value="Completed">Completed</option>
                <option value="Cancelled">Cancelled</option>
              </select>

              <select
                className={selectClass}
                value={customerId}
                onChange={(e) => {
                  setCustomerId(e.target.value);
                  setPage(1);
                }}
                data-testid="activities-customer-filter"
              >
                <option value="">Semua customer</option>
                {(customerOptions.data ?? []).map((customer) => (
                  <option key={customer.id} value={customer.id}>{customer.name}</option>
                ))}
              </select>

              <select
                className={selectClass}
                value={salesId}
                onChange={(e) => {
                  setSalesId(e.target.value);
                  setPage(1);
                }}
                data-testid="activities-sales-filter"
              >
                <option value="">Semua sales</option>
                {(salesOptions.data ?? []).map((sales) => (
                  <option key={sales.id} value={sales.id}>
                    {sales.name}
                  </option>
                ))}
              </select>
            </div>

            {(search || activityFilter || activityType || status || salesId || customerId) && (
              <div className="mt-3 flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetFilters}
                >
                  Reset filter
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      {mode === "activities" ? (
        <DataTable
          testId="activities-table"
          items={activities.data?.items ?? []}
          loading={activities.isLoading}
          total={activities.data?.total}
          page={page}
          pageSize={pageSize}
          onPage={setPage}
          onPageSize={(size) => {
            setPageSize(size);
            setPage(1);
          }}
          columns={[
            {
              key: "type",
              label: "Tipe",
              render: (item) => (
                <Badge variant="outline">{item.activity_type}</Badge>
              ),
            },
            {
              key: "date",
              label: "Tanggal",
              render: (item) => item.date,
            },
            {
              key: "subject",
              label: "Subjek",
              render: (item) => (
                <span className="font-medium">{item.subject}</span>
              ),
            },
            {
              key: "customer",
              label: "Customer",
              render: (item) => item.customer_name ?? "—",
            },
            {
              key: "sales",
              label: "Sales",
              render: (item) => item.sales_name ?? "—",
            },
            {
              key: "followup",
              label: "Follow-up",
              render: (item) => item.next_follow_up ?? "—",
            },
            {
              key: "status",
              label: "Status",
              render: (item) => (
                <Badge
                  variant={
                    item.status === "Completed" ? "default" : "secondary"
                  }
                >
                  {item.status}
                </Badge>
              ),
            },
            {
              key: "action",
              label: "Aksi",
              render: (item) => (
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => openDetail(item.id)}
                    title="Lihat detail"
                    data-testid={`activity-view-${item.activity_id}`}
                  >
                    <Eye className="size-4 text-blue-600" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => openEdit(item.id)}
                    title="Edit aktivitas"
                    data-testid={`activity-edit-${item.activity_id}`}
                  >
                    <Pencil className="size-4 text-slate-600" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => removeActivity.mutate(item.id)}
                    title="Hapus aktivitas"
                    data-testid={`activity-delete-${item.activity_id}`}
                  >
                    <Trash2 className="size-4 text-red-500" />
                  </Button>
                </div>
              ),
            },
          ]}
        />
      ) : (
        <DataTable
          testId="tasks-table"
          items={tasks.data?.items ?? []}
          loading={tasks.isLoading}
          total={tasks.data?.total}
          page={page}
          pageSize={pageSize}
          onPage={setPage}
          onPageSize={(size) => {
            setPageSize(size);
            setPage(1);
          }}
          columns={[
            {
              key: "title",
              label: "Task",
              render: (item) => (
                <span className="font-medium">{item.title}</span>
              ),
            },
            {
              key: "customer",
              label: "Customer",
              render: (item) => item.customer_name ?? "—",
            },
            {
              key: "due",
              label: "Due Date",
              render: (item) => item.due_date,
            },
            {
              key: "priority",
              label: "Prioritas",
              render: (item) => (
                <Badge variant="outline">{item.priority}</Badge>
              ),
            },
            {
              key: "status",
              label: "Status",
              render: (item) => <Badge>{item.status}</Badge>,
            },
            {
              key: "action",
              label: "Aksi",
              render: (item) => (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={item.status === "Completed"}
                  onClick={() => completeTask.mutate(item.id)}
                  data-testid={`task-complete-${item.id}`}
                >
                  Selesai
                </Button>
              ),
            },
          ]}
        />
      )}

      {detailModal && (
        <Modal title="Detail Aktivitas" onClose={closeDetail}>
          {activityDetail.isLoading ? (
            <div className="py-10 text-center text-slate-500">
              Memuat detail aktivitas...
            </div>
          ) : activityDetail.isError ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              Gagal mengambil detail aktivitas.
            </div>
          ) : activityDetail.data ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <DetailItem label="Activity ID" value={activityDetail.data.activity_id} />
              <DetailItem label="Tipe" value={activityDetail.data.activity_type} />
              <DetailItem label="Tanggal" value={activityDetail.data.date} />
              <DetailItem label="Status" value={activityDetail.data.status} />
              <DetailItem label="Subjek" value={activityDetail.data.subject} />
              <DetailItem label="Customer" value={activityDetail.data.customer_name} />
              <DetailItem label="Sales" value={activityDetail.data.sales_name} />
              <DetailItem label="Next Follow-up" value={activityDetail.data.next_follow_up} />
              <div className="sm:col-span-2">
                <DetailItem label="Deskripsi" value={activityDetail.data.description} />
              </div>
            </div>
          ) : null}
        </Modal>
      )}

      {editModal && (
        <Modal title="Edit Aktivitas" onClose={closeEdit} size="landscape">
          {activityDetail.isLoading ? (
            <div className="py-10 text-center text-slate-500">
              Memuat aktivitas...
            </div>
          ) : activityDetail.isError || !activityDetail.data ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              Gagal mengambil aktivitas.
            </div>
          ) : (
            <EditActivityForm
              activity={activityDetail.data}
              onCancel={closeEdit}
              onSubmit={(values) => updateActivity.mutate(values)}
              saving={updateActivity.isPending}
            />
          )}
        </Modal>
      )}

      {modal && (
        <Modal
          title="Tambah Aktivitas"
          onClose={() => setModal(false)}
          size="landscape"
        >
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              create.mutate();
            }}
            data-testid="activity-create-form"
          >
            <div className="sm:col-span-2">
              <Field label="Subjek" required>
                <Input
                  value={form.subject}
                  onChange={(e) =>
                    setForm({ ...form, subject: e.target.value })
                  }
                  data-testid="activity-subject-input"
                />
              </Field>
            </div>

            <Field label="Tipe">
              <select
                className={selectClass}
                value={form.activity_type}
                onChange={(e) =>
                  setForm({ ...form, activity_type: e.target.value })
                }
                data-testid="activity-type-input"
              >
                {ACTIVITY_TYPES.map((type) => (
                  <option key={type}>{type}</option>
                ))}
              </select>
            </Field>

            <Field label="Tanggal" required>
              <Input
                type="date"
                value={form.date}
                onChange={(e) =>
                  setForm({ ...form, date: e.target.value })
                }
                data-testid="activity-date-input"
              />
            </Field>

            <Field label="Customer">
              <select
                className={selectClass}
                value={form.customer_id}
                onChange={(e) =>
                  setForm({ ...form, customer_id: e.target.value })
                }
                data-testid="activity-customer-input"
              >
                <option value="">— Pilih customer —</option>
                {(customerOptions.data ?? []).map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Opportunity">
              <select
                className={selectClass}
                value={form.opportunity_id}
                onChange={(e) => setForm({ ...form, opportunity_id: e.target.value })}
                data-testid="activity-opportunity-input"
                disabled={!form.customer_id}
              >
                <option value="">— Tanpa opportunity —</option>
                {(opportunityOptions.data ?? []).map((opportunity) => (
                  <option key={opportunity.id} value={opportunity.id}>
                    {opportunity.name} · {opportunity.stage}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Next Follow-up">
              <Input
                type="date"
                value={form.next_follow_up}
                onChange={(e) =>
                  setForm({ ...form, next_follow_up: e.target.value })
                }
                data-testid="activity-followup-input"
              />
            </Field>

            <Field label="Status">
              <select
                className={selectClass}
                value={form.status}
                onChange={(e) =>
                  setForm({ ...form, status: e.target.value })
                }
                data-testid="activity-status-input"
              >
                <option>Open</option>
                <option>Completed</option>
                <option>Cancelled</option>
              </select>
            </Field>

            <div className="sm:col-span-2">
              <Field label="Deskripsi">
                <Textarea
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  data-testid="activity-description-input"
                />
              </Field>
            </div>

            <div className="flex justify-end gap-2 sm:col-span-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setModal(false)}
                data-testid="activity-cancel-button"
              >
                Batal
              </Button>
              <Button
                type="submit"
                disabled={create.isPending}
                data-testid="activity-save-button"
              >
                {create.isPending ? "Menyimpan..." : "Simpan"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </div>
      <div className="text-sm text-slate-800">{value || "—"}</div>
    </div>
  );
}

function EditActivityForm({
  activity,
  onCancel,
  onSubmit,
  saving,
}: {
  activity: Activity;
  onCancel: () => void;
  onSubmit: (values: {
    subject: string;
    activity_type: string;
    date: string;
    next_follow_up: string | null;
    status: string;
    description: string;
  }) => void;
  saving: boolean;
}) {
  const [subject, setSubject] = useState(activity.subject);
  const [activityType, setActivityType] = useState(activity.activity_type);
  const [date, setDate] = useState(activity.date);
  const [nextFollowUp, setNextFollowUp] = useState(activity.next_follow_up ?? "");
  const [status, setStatus] = useState(activity.status);
  const [description, setDescription] = useState(activity.description ?? "");

  return (
    <form
      className="grid gap-4 sm:grid-cols-2"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          subject,
          activity_type: activityType,
          date,
          next_follow_up: nextFollowUp || null,
          status,
          description,
        });
      }}
    >
      <div className="sm:col-span-2">
        <Field label="Subjek" required>
          <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
        </Field>
      </div>

      <Field label="Tipe">
        <select className={selectClass} value={activityType} onChange={(e) => setActivityType(e.target.value)}>
          {ACTIVITY_TYPES.map((type) => (
            <option key={type}>{type}</option>
          ))}
        </select>
      </Field>

      <Field label="Tanggal" required>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </Field>

      <Field label="Customer">
        <Input value={activity.customer_name ?? "—"} disabled />
      </Field>

      <Field label="Sales">
        <Input value={activity.sales_name ?? "—"} disabled />
      </Field>

      <Field label="Next Follow-up">
        <Input
          type="date"
          value={nextFollowUp}
          onChange={(e) => setNextFollowUp(e.target.value)}
        />
      </Field>

      <Field label="Status">
        <select className={selectClass} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option>Open</option>
          <option>Completed</option>
          <option>Cancelled</option>
        </select>
      </Field>

      <div className="sm:col-span-2">
        <Field label="Deskripsi">
          <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
      </div>

      <div className="flex justify-end gap-2 sm:col-span-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Batal
        </Button>
        <Button type="submit" disabled={saving || !subject.trim()}>
          {saving ? "Menyimpan..." : "Simpan"}
        </Button>
      </div>
    </form>
  );
}
