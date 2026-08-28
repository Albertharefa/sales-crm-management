export interface User {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: string;
  manager_id?: string;
  phone?: string;
  status: string;
  last_login?: string;
}

export interface Customer {
  id: string;
  customer_id: string;
  name: string;
  industry: string;
  city: string;
  province?: string;
  phone?: string;
  email?: string;
  pic_name?: string;
  pic_position?: string;
  source?: string;
  status: string;
  sales_id?: string;
  sales_name?: string;
  address?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Contact {
  id: string;
  contact_id: string;
  customer_id: string;
  customer_name: string;
  first_name: string;
  last_name?: string;
  position?: string;
  department?: string;
  email?: string;
  mobile?: string;
  contact_type: string;
  is_decision_maker: boolean;
  status: string;
  notes?: string;
  created_at: string;
}

export interface Opportunity {
  id: string;
  opportunity_id: string;
  name: string;
  customer_id: string;
  customer_name: string;
  sales_name?: string;
  value: number;
  probability: number;
  stage: string;
  target_close?: string;
  brand?: string;
  product?: string;
  next_action?: string;
  description?: string;
  loss_reason?: string;
  created_at: string;
}

export interface Activity {
  id: string;
  activity_id: string;
  subject: string;
  activity_type: string;
  date: string;
  customer_name?: string;
  sales_name?: string;
  next_follow_up?: string;
  status: string;
  description?: string;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  due_date: string;
  priority: string;
  status: string;
  customer_name?: string;
  opportunity_name?: string;
  assigned_user?: string;
  created_at: string;
}

export interface Product {
  id: string;
  code: string;
  name: string;
  brand?: string;
  category: string;
  unit: string;
  default_price: number;
  supplier?: string;
  status: string;
  description?: string;
  created_at: string;
}

export interface QuotationItem {
  product_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount: number;
  tax: number;
}

export interface Quotation {
  id: string;
  number: string;
  date: string;
  customer_id: string;
  customer_name: string;
  sales_name?: string;
  items: QuotationItem[];
  subtotal: number;
  discount_total: number;
  tax_total: number;
  grand_total: number;
  status: string;
  created_at: string;
}

export interface PurchaseOrderItem {
  product_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  date: string;
  customer_id: string;
  customer_name: string;
  quotation_number?: string;
  sales_name?: string;
  items: PurchaseOrderItem[];
  total: number;
  status: string;
  eta?: string;
  supplier?: string;
  document_name?: string;
  created_at: string;
}

export interface DashboardMetrics {
  total_customer: number;
  open_pipeline: number;
  weighted_pipeline: number;
  won_value: number;
  total_quotation: number;
  total_po: number;
  po_value: number;
  activities: number;
  open_orders: number;
  completed_orders: number;
  overdue_orders: number;
  pipeline_by_stage: { stage: string; count: number; value: number }[];
}

export interface AuditLog {
  id: string;
  user_name: string;
  action: string;
  module: string;
  record_id?: string;
  changes?: Record<string, unknown>;
  created_at: string;
}

export interface Paginated<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface Options {
  customers: { id: string; name: string }[];
  products: { id: string; name: string; default_price?: number }[];
  users: { id: string; name: string; role: string }[];
}

export interface SalesTeamMetric {
  sales: string;
  role: string;
  manager: string;
  open_pipeline: number;
  weighted: number;
  won: number;
  po: number;
  po_value: number;
  activities: number;
  indent: number;
  overdue: number;
}

export type AIContextType = "dashboard" | "customer" | "opportunity" | "quotation";
export type AICapability = "sales_copilot" | "report_analyst" | "quotation_writer";

export interface AIMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  capability: AICapability;
  context_type: AIContextType;
  context_id?: string | null;
  created_at: string;
}

export interface AIConversationDetail {
  id: string;
  title: string;
  context_type: AIContextType;
  context_id?: string | null;
  messages: AIMessage[];
  created_at: string;
  updated_at: string;
}

export interface AIContextOption {
  id: string;
  name: string;
  description?: string | null;
}

export interface AISavedNote {
  id: string;
  target_type: AIContextType;
  target_id?: string | null;
  title: string;
  content: string;
  created_by: string;
  created_at: string;
}