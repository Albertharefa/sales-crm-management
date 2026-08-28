import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";
import { Bot, Check, ChevronDown, FilePenLine, Gauge, MessageSquareText, Plus, Send, Sparkles, X } from "lucide-react";
import { toast } from "sonner";

import { apiGet, apiPost, apiStream } from "@/lib/api";
import type { ApiStreamEvent } from "@/lib/api";
import type { AICapability, AIContextOption, AIContextType, AIConversationDetail, AIMessage, AISavedNote } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { selectClass } from "@/components/Field";

const capabilityMeta: Record<AICapability, { label: string; description: string; icon: typeof Sparkles; prompts: string[] }> = {
  sales_copilot: { label: "Sales Copilot", description: "Ringkasan, follow-up, next action, dan deal risk", icon: Sparkles, prompts: ["Ringkas konteks ini dan beri 3 next action", "Buat draft follow-up WhatsApp profesional", "Analisis risiko deal dan mitigasinya"] },
  report_analyst: { label: "Report Analyst", description: "Tanya jawab KPI, pipeline, dan forecast", icon: Gauge, prompts: ["Jelaskan kesehatan pipeline saat ini", "Deal mana yang perlu diprioritaskan?", "Berikan ringkasan manajemen singkat"] },
  quotation_writer: { label: "Quotation Writer", description: "Draft scope, item description, dan commercial notes", icon: FilePenLine, prompts: ["Perbaiki deskripsi item quotation", "Buat commercial notes yang profesional", "Susun scope, asumsi, dan exclusions"] },
};

function routeContext(pathname: string): { type: AIContextType; capability: AICapability; label: string } {
  if (pathname.startsWith("/customers")) return { type: "customer", capability: "sales_copilot", label: "Customer" };
  if (pathname.startsWith("/pipeline")) return { type: "opportunity", capability: "sales_copilot", label: "Opportunity" };
  if (pathname.startsWith("/quotations")) return { type: "quotation", capability: "quotation_writer", label: "Quotation" };
  return { type: "dashboard", capability: "report_analyst", label: "Dashboard & Pipeline" };
}

function pendingMessage(id: string, capability: AICapability, contextType: AIContextType, contextId: string): AIMessage {
  return { id, conversation_id: "", role: "assistant", content: "", capability, context_type: contextType, context_id: contextId || null, created_at: new Date().toISOString() };
}

export default function AICopilot() {
  const location = useLocation();
  const context = useMemo(() => routeContext(location.pathname), [location.pathname]);
  const [open, setOpen] = useState(false);
  const [capability, setCapability] = useState<AICapability>(context.capability);
  const [contextId, setContextId] = useState("");
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [conversationId, setConversationId] = useState(() => window.localStorage.getItem("crm-ai-conversation") ?? "");

  useEffect(() => { setCapability(context.capability); setContextId(""); }, [context.capability, context.type]);

  const options = useQuery({
    queryKey: ["ai-context-options", context.type],
    queryFn: () => apiGet<AIContextOption[]>(`/ai/context-options?context_type=${context.type}`),
    enabled: open && context.type !== "dashboard",
    staleTime: 60_000,
  });
  const history = useQuery({
    queryKey: ["ai-conversation", conversationId],
    queryFn: () => apiGet<AIConversationDetail>(`/ai/conversations/${conversationId}`),
    enabled: open && Boolean(conversationId) && messages.length === 0,
    retry: false,
  });
  useEffect(() => { if (history.data && messages.length === 0) setMessages(history.data.messages); }, [history.data, messages.length]);

  const send = useMutation({
    mutationFn: async (text: string) => {
      const userMessage: AIMessage = { id: `user-${Date.now()}`, conversation_id: conversationId, role: "user", content: text, capability, context_type: context.type, context_id: contextId || null, created_at: new Date().toISOString() };
      let streamId = `assistant-${Date.now()}`;
      setMessages(current => [...current, userMessage, pendingMessage(streamId, capability, context.type, contextId)]);
      await apiStream("/ai/chat/stream", { prompt: text, conversation_id: conversationId || null, capability, context_type: context.type, context_id: contextId || null }, (event: ApiStreamEvent) => {
        if (event.type === "meta") {
          if (event.conversation_id) { setConversationId(event.conversation_id); window.localStorage.setItem("crm-ai-conversation", event.conversation_id); }
          if (event.assistant_message_id) {
            const previousId = streamId;
            const nextId = event.assistant_message_id;
            setMessages(current => current.map(message => message.id === previousId ? { ...message, id: nextId, conversation_id: event.conversation_id ?? conversationId } : message));
            streamId = nextId;
          }
        } else if (event.type === "delta" && event.content) {
          setMessages(current => current.map(message => message.id === streamId ? { ...message, content: message.content + event.content } : message));
        } else if (event.type === "error") {
          setMessages(current => current.map(message => message.id === streamId ? { ...message, content: event.message ?? "AI sedang tidak tersedia." } : message));
          throw new Error(event.message ?? "AI stream failed");
        }
      });
    },
    onError: () => toast.error("AI sedang tidak dapat merespons. Silakan coba lagi."),
  });
  const save = useMutation({
    mutationFn: (message: AIMessage) => apiPost<AISavedNote>("/ai/notes/confirm", { conversation_id: conversationId, message_id: message.id, target_type: context.type, target_id: context.type === "dashboard" ? null : contextId, title: `${capabilityMeta[capability].label} — ${context.label}` }),
    onSuccess: () => toast.success("Draft AI disimpan sebagai catatan setelah konfirmasi"),
    onError: () => toast.error("Catatan AI gagal disimpan"),
  });

  const requiresSelection = context.type !== "dashboard";
  const canSend = prompt.trim().length >= 2 && (!requiresSelection || Boolean(contextId)) && !send.isPending;
  const lastAssistant = [...messages].reverse().find(message => message.role === "assistant" && message.content);

  function startNewChat() {
    setConversationId(""); setMessages([]); window.localStorage.removeItem("crm-ai-conversation");
  }
  function submitPrompt() {
    const text = prompt.trim();
    if (!text) return;
    setPrompt("");
    send.mutate(text);
  }

  return <>
    <button onClick={() => setOpen(true)} className="fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700" data-testid="ai-copilot-open-button"><Sparkles className="size-4" />Ask AI</button>
    {open && <button className="fixed inset-0 z-[70] bg-slate-950/30" onClick={() => setOpen(false)} aria-label="Close AI Copilot" data-testid="ai-copilot-overlay" />}
    <aside className={`fixed inset-y-0 right-0 z-[80] flex w-full max-w-[460px] flex-col border-l border-slate-200 bg-white shadow-2xl transition-opacity duration-200 ${open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`} data-testid="ai-copilot-drawer">
      <header className="border-b border-slate-200 px-5 py-4"><div className="flex items-start justify-between"><div className="flex items-center gap-3"><div className="flex size-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Bot className="size-5" /></div><div><div className="flex items-center gap-2"><h2 className="font-heading text-lg font-semibold" data-testid="ai-copilot-title">CRM AI Copilot</h2><Badge variant="outline">GPT-5.4</Badge></div><p className="mt-0.5 text-xs text-slate-500">Data terpilih saja · simpan setelah konfirmasi</p></div></div><button className="rounded-md p-2 text-slate-500 hover:bg-slate-100" onClick={() => setOpen(false)} data-testid="ai-copilot-close-button"><X className="size-5" /></button></div></header>
      <div className="space-y-3 border-b border-slate-200 bg-slate-50 px-5 py-4">
        <div className="grid grid-cols-3 gap-2">{(Object.keys(capabilityMeta) as AICapability[]).map(key => { const Icon = capabilityMeta[key].icon; return <button key={key} onClick={() => setCapability(key)} className={`rounded-lg border p-2 text-left ${capability === key ? "border-blue-300 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-600"}`} data-testid={`ai-capability-${key}`}><Icon className="mb-1 size-4" /><span className="block text-[10px] font-semibold leading-tight">{capabilityMeta[key].label}</span></button>; })}</div>
        {requiresSelection ? <div>
          <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-slate-500">Konteks {context.label}</label>
          <div className="relative">
            <select className={`${selectClass} pr-9`} value={contextId} onChange={event => setContextId(event.target.value)} data-testid="ai-context-select">
              <option value="" label={`— Pilih ${context.label.toLowerCase()} —`} />
              {options.data?.map(option => <option key={option.id} value={option.id} label={`${option.name} — ${option.description ?? ""}`} />)}
            </select>
            <ChevronDown className="pointer-events-none absolute right-3 top-3 size-4 text-slate-400" />
          </div>
        </div> : <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-700" data-testid="ai-dashboard-context">Konteks aktif: dashboard dan pipeline yang dapat Anda akses</div>}
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5" data-testid="ai-message-list">{messages.length === 0 ? <div className="py-8 text-center"><div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500"><MessageSquareText className="size-5" /></div><h3 className="mt-4 font-heading font-semibold">{capabilityMeta[capability].label}</h3><p className="mx-auto mt-2 max-w-xs text-sm leading-relaxed text-slate-500">{capabilityMeta[capability].description}</p><div className="mt-5 space-y-2">{capabilityMeta[capability].prompts.map((item, index) => <button key={item} className="block w-full rounded-lg border border-slate-200 px-3 py-2 text-left text-xs text-slate-600 hover:border-blue-300 hover:bg-blue-50" onClick={() => setPrompt(item)} data-testid={`ai-prompt-suggestion-${index}`}>{item}</button>)}</div></div> : messages.map(message => <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`} data-testid={`ai-message-${message.id}`}><div className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${message.role === "user" ? "rounded-br-md bg-blue-600 text-white" : "rounded-bl-md border border-slate-200 bg-slate-50 text-slate-700"}`}><div className="whitespace-pre-wrap">{message.content || <span className="animate-pulse text-slate-400">Menganalisis data CRM...</span>}</div></div></div>)}{lastAssistant && !send.isPending && <div className="flex justify-start"><Button variant="outline" size="sm" onClick={() => save.mutate(lastAssistant)} disabled={save.isPending || (requiresSelection && !contextId)} data-testid="ai-confirm-save-button">{save.isSuccess ? <Check className="mr-2 size-4 text-green-600" /> : <Plus className="mr-2 size-4" />}{save.isPending ? "Menyimpan..." : "Konfirmasi & simpan catatan"}</Button></div>}</div>
      <footer className="border-t border-slate-200 bg-white p-4"><div className="mb-2 flex items-center justify-between"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{capabilityMeta[capability].label}</span><button onClick={startNewChat} className="text-xs font-medium text-blue-600 hover:text-blue-700" data-testid="ai-new-chat-button">Percakapan baru</button></div><div className="relative"><Textarea value={prompt} onChange={event => setPrompt(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); if (canSend) submitPrompt(); } }} placeholder={requiresSelection && !contextId ? `Pilih ${context.label.toLowerCase()} terlebih dahulu` : "Tanyakan sesuatu tentang data CRM terpilih..."} className="min-h-24 resize-none pr-12" disabled={requiresSelection && !contextId} data-testid="ai-prompt-input" /><Button size="icon" className="absolute bottom-2 right-2" onClick={submitPrompt} disabled={!canSend} data-testid="ai-send-button"><Send className="size-4" /></Button></div><p className="mt-2 text-[10px] text-slate-400">AI dapat keliru. Tinjau hasil sebelum menyimpannya ke CRM.</p></footer>
    </aside>
  </>;
}