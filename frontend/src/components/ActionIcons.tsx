import React from "react";
import { Eye, Pencil, Trash2 } from "lucide-react";

export type ActionIconProps = {
  onView?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  canView?: boolean;
  canEdit?: boolean;
  canDelete?: boolean;
};

const iconButtonClass =
  "inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-300";

export default function ActionIcons({
  onView,
  onEdit,
  onDelete,
  canView = true,
  canEdit = true,
  canDelete = true,
}: ActionIconProps) {
  return (
    <div className="flex items-center gap-1">
      {canView && onView && (
        <button type="button" className={iconButtonClass} onClick={onView} title="View" aria-label="View">
          <Eye className="h-4 w-4" />
        </button>
      )}
      {canEdit && onEdit && (
        <button type="button" className={iconButtonClass} onClick={onEdit} title="Edit" aria-label="Edit">
          <Pencil className="h-4 w-4" />
        </button>
      )}
      {canDelete && onDelete && (
        <button type="button" className={iconButtonClass} onClick={onDelete} title="Delete" aria-label="Delete">
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
