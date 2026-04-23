/** Tipos compartilhados do Open Clinic AI Frontend */

export type UserRole = "admin" | "secretary";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

export type LeadStatus =
  | "novo"
  | "em_contato"
  | "orcamento_enviado"
  | "negociando"
  | "convertido"
  | "perdido";

export type LeadChannel =
  | "telegram"
  | "whatsapp"
  | "google_ads"
  | "meta_ads"
  | "instagram"
  | "site"
  | "indicacao"
  | "outro";

export interface Lead {
  id: string;
  full_name: string | null;
  phone: string;
  email: string | null;
  channel: LeadChannel;
  utm_source: string | null;
  utm_campaign: string | null;
  specialty_id: string | null;
  description: string | null;
  quote_value: number | null;
  status: LeadStatus;
  assigned_to: string | null;
  sla_deadline: string;
  contacted_at: string | null;
  is_overdue: boolean;
  next_followup_at: string | null;
  created_at: string;
}

export interface LeadInteraction {
  id: string;
  lead_id: string;
  user_id: string;
  type: "nota" | "ligacao" | "whatsapp" | "email" | "reuniao" | "outro";
  content: string;
  next_action: string | null;
  interacted_at: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  specialty_id: string;
  starts_at: string;
  ends_at: string;
  status: "scheduled" | "confirmed" | "completed" | "cancelled" | "no_show";
  source: "ai_chat" | "secretary" | "patient_link";
  notes: string | null;
}

export interface Doctor {
  id: string;
  full_name: string;
  crm: string | null;
  specialty_id: string;
  scheduling_provider: "google_calendar" | "local_db";
  slot_duration_minutes: number;
  is_active: boolean;
}

export interface Specialty {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

// Tipos de relatório
export interface FunnelItem {
  status: LeadStatus;
  total: number;
}

export interface LeadsBySource {
  channel: LeadChannel;
  utm_campaign: string | null;
  total_leads: number;
  converted: number;
  conversion_rate: number;
}

export interface SLAReport {
  total: number;
  within_sla: number;
  overdue: number;
  sla_rate: number;
}
