import { useState } from "react";
import { Download, Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

type PageHeaderProps = {
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
  onRefresh?: () => void | Promise<void>;
  onExport?: () => void;
};

export default function PageHeader({ title, description, action, onRefresh, onExport }: PageHeaderProps) {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    if (!onRefresh || refreshing) return;
    setRefreshing(true);
    window.location.reload();
  };

  return (
    <div className="mb-7 flex flex-col justify-between gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end">
      <div>
        <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600" data-testid="page-overline">CRM SALES MANAGEMENT</div>
        <h1 className="font-heading text-3xl font-bold tracking-tight text-slate-900" data-testid={`page-title-${title.toLowerCase().replaceAll(" ", "-")}`}>{title}</h1>
        <p className="mt-2 text-sm text-slate-500" data-testid="page-description">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        {onRefresh && (
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing} data-testid="page-refresh-button">
            <RefreshCw className={`mr-2 size-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Memuat..." : "Refresh"}
          </Button>
        )}
        {onExport && <Button variant="outline" size="sm" onClick={onExport} data-testid="page-export-button"><Download className="mr-2 size-4" />Export CSV</Button>}
        {action && <Button size="sm" onClick={action.onClick} data-testid="page-primary-action"><Plus className="mr-2 size-4" />{action.label}</Button>}
      </div>
    </div>
  );
}
