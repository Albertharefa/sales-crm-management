import { Eye, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export type ActionIconProps = {
  onView?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  canView?: boolean;
  canEdit?: boolean;
  canDelete?: boolean;
  viewTitle?: string;
  editTitle?: string;
  deleteTitle?: string;
  viewTestId?: string;
  editTestId?: string;
  deleteTestId?: string;
};

export default function ActionIcons({
  onView,
  onEdit,
  onDelete,
  canView = true,
  canEdit = true,
  canDelete = true,
  viewTitle = "View",
  editTitle = "Edit",
  deleteTitle = "Delete",
  viewTestId,
  editTestId,
  deleteTestId,
}: ActionIconProps) {
  return (
    <div className="flex items-center gap-1">
      {canView && onView && (
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={onView}
          title={viewTitle}
          aria-label={viewTitle}
          data-testid={viewTestId}
        >
          <Eye className="size-4 text-blue-600" />
        </Button>
      )}
      {canEdit && onEdit && (
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={onEdit}
          title={editTitle}
          aria-label={editTitle}
          data-testid={editTestId}
        >
          <Pencil className="size-4 text-slate-600" />
        </Button>
      )}
      {canDelete && onDelete && (
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={onDelete}
          title={deleteTitle}
          aria-label={deleteTitle}
          data-testid={deleteTestId}
        >
          <Trash2 className="size-4 text-red-500" />
        </Button>
      )}
    </div>
  );
}
