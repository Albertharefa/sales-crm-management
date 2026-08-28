import { X } from "lucide-react";

export default function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/50 p-4" role="dialog" aria-modal="true" data-testid="modal-overlay"><div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-slate-200 bg-white p-6 shadow-2xl"><div className="mb-6 flex items-center justify-between"><h2 className="font-heading text-xl font-semibold" data-testid="modal-title">{title}</h2><button onClick={onClose} className="rounded-md p-2 text-slate-500 hover:bg-slate-100" data-testid="modal-close-button" aria-label="Close"><X className="size-4" /></button></div>{children}</div></div>;
}