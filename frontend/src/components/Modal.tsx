import { X } from "lucide-react";

export default function Modal({
  title,
  children,
  onClose,
  size = "default",
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  size?: "default" | "landscape";
}) {
  const widthClass = size === "landscape" ? "max-w-7xl" : "max-w-2xl";

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/50 p-3 sm:p-4"
      role="dialog"
      aria-modal="true"
      data-testid="modal-overlay"
    >
      <div
        className={`max-h-[94vh] w-full ${widthClass} overflow-y-auto rounded-xl border border-slate-200 bg-white p-5 shadow-2xl sm:p-6`}
      >
        <div className="mb-6 flex items-center justify-between">
          <h2 className="font-heading text-xl font-semibold" data-testid="modal-title">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-2 text-slate-500 hover:bg-slate-100"
            data-testid="modal-close-button"
            aria-label="Close"
          >
            <X className="size-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}