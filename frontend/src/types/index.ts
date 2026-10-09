export type UserRole = 'admin' | 'manager' | 'user';

export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  role: UserRole;
  phone?: string | null;
  department?: string | null;
  position?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  avatar_url?: string | null;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail?: string;
  message?: string;
}

export type ReminderPriority = 'low' | 'medium' | 'high' | 'urgent';
export type ReminderStatus = 'pending' | 'completed' | 'snoozed' | 'cancelled';
export type RequestType = 'payment' | 'approval' | 'document' | 'asset' | 'other';
export type RequestStatus = 'pending' | 'under_review' | 'approved' | 'rejected' | 'completed' | 'cancelled';
export type PaymentStatus = 'pending' | 'due_soon' | 'overdue' | 'paid' | 'cancelled';
export type PaymentMethod = 'bank_transfer' | 'credit_card' | 'cash' | 'check' | 'upi' | 'other';
export type AssetCategory = 'electronics' | 'furniture' | 'vehicle' | 'software' | 'machinery' | 'office_supplies' | 'documents' | 'other';
export type AssetStatus = 'available' | 'assigned' | 'in_maintenance' | 'retired' | 'lost';
export type ChallengeStatus = 'active' | 'completed' | 'expired';
export type WheelEntryType = 'gift' | 'reward' | 'challenge' | 'activity' | 'custom';
export type GiftStatus = 'assigned' | 'in_progress' | 'delivered' | 'cancelled';
export type NotificationType =
  | 'deadline_upcoming'
  | 'deadline_overdue'
  | 'payment_due'
  | 'payment_overdue'
  | 'request_pending'
  | 'request_approved'
  | 'request_rejected'
  | 'challenge_reminder'
  | 'wheel_reminder'
  | 'gift_deadline'
  | 'gift_status_change'
  | 'status_change'
  | 'new_request'
  | 'system';

export type NotificationChannel = 'in_app' | 'email' | 'push';

export interface Reminder {
  id: number;
  title: string;
  description?: string | null;
  deadline: string;
  deadline_time?: string | null;
  priority: ReminderPriority;
  reminder_schedule?: string[];
  is_recurring: boolean;
  recurrence_rule?: string | null;
  related_entity_type?: string | null;
  related_entity_id?: number | null;
  status: ReminderStatus;
  assignee_id?: number | null;
  assignee?: User | null;
  created_by_id?: number | null;
  completed_at?: string | null;
  completed_by_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface RequestItem {
  id: number;
  request_id: string;
  title: string;
  description?: string | null;
  request_type: RequestType;
  status: RequestStatus;
  priority: ReminderPriority;
  requested_date: string;
  due_date?: string | null;
  completed_date?: string | null;
  requester_id?: number | null;
  requester?: User | null;
  assignee_id?: number | null;
  assignee?: User | null;
  metadata?: Record<string, unknown> | null;
  supporting_documents?: string[];
  resolution_notes?: string | null;
  resolved_by_id?: number | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
  status_history?: RequestStatusHistory[];
}

export interface RequestStatusHistory {
  id: number;
  old_status?: RequestStatus | null;
  new_status: RequestStatus;
  notes?: string | null;
  created_at: string;
  changed_by?: User | null;
}

export interface Payment {
  id: number;
  title: string;
  vendor: string;
  amount: number;
  currency: string;
  due_date: string;
  paid_date?: string | null;
  status: PaymentStatus;
  payment_method?: PaymentMethod | null;
  payment_reference?: string | null;
  notes?: string | null;
  supporting_document?: string | null;
  assignee_id?: number | null;
  assignee?: User | null;
  created_by_id?: number | null;
  reminder_sent_due_soon: boolean;
  reminder_sent_overdue: boolean;
  created_at: string;
  updated_at: string;
  status_history?: PaymentStatusHistory[];
}

export interface PaymentStatusHistory {
  id: number;
  old_status?: PaymentStatus | null;
  new_status: PaymentStatus;
  notes?: string | null;
  created_at: string;
  changed_by?: User | null;
}

export interface AssetDocument {
  name: string;
  url: string;
  type: string;
  uploaded_at: string;
}

export interface AssetExternalLink {
  name: string;
  url: string;
  description?: string | null;
}

export interface Asset {
  id: number;
  asset_id: string;
  name: string;
  category: AssetCategory;
  description?: string | null;
  assignee_id?: number | null;
  assignee?: User | null;
  purchase_date?: string | null;
  purchase_cost?: number | null;
  vendor?: string | null;
  warranty_expiry?: string | null;
  status: AssetStatus;
  location?: string | null;
  documents?: AssetDocument[];
  external_links?: AssetExternalLink[];
  notes?: string | null;
  created_at: string;
  updated_at: string;
  status_history?: AssetStatusHistory[];
}

export interface AssetStatusHistory {
  id: number;
  old_status?: AssetStatus | null;
  new_status: AssetStatus;
  notes?: string | null;
  created_at: string;
  changed_by?: User | null;
}

export interface SundayChallenge {
  id: number;
  title: string;
  description?: string | null;
  instructions?: string | null;
  reward?: string | null;
  challenge_date: string;
  status: ChallengeStatus;
  created_by_id?: number | null;
  creator?: User | null;
  created_at: string;
  updated_at: string;
  participations?: ChallengeParticipation[];
}

export interface ChallengeParticipation {
  id: number;
  challenge_id: number;
  user: User;
  status: ChallengeStatus;
  completed_at?: string | null;
  submission_notes?: string | null;
  created_at: string;
}

export interface WheelEntry {
  id: number;
  label: string;
  entry_type: WheelEntryType;
  value?: string | null;
  probability: number;
  is_active: boolean;
  order: number;
  color?: string | null;
  icon?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WheelSpin {
  id: number;
  user?: User | null;
  entry_id?: number | null;
  won_label: string;
  won_value?: string | null;
  won_entry_type: WheelEntryType;
  spin_date: string;
  is_claimed: boolean;
  claimed_at?: string | null;
  created_at: string;
}

export interface Gift {
  id: number;
  gift_id: string;
  name: string;
  description?: string | null;
  recipient_id?: number | null;
  recipient?: User | null;
  assignee_id?: number | null;
  assignee?: User | null;
  assigned_date: string;
  expected_delivery_date?: string | null;
  actual_delivery_date?: string | null;
  status: GiftStatus;
  delivery_notes?: string | null;
  proof_document?: string | null;
  assigned_by_id?: number | null;
  assigned_by?: User | null;
  created_at: string;
  updated_at: string;
  status_history?: GiftStatusHistory[];
}

export interface GiftStatusHistory {
  id: number;
  old_status?: GiftStatus | null;
  new_status: GiftStatus;
  notes?: string | null;
  created_at: string;
  changed_by?: User | null;
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: NotificationType;
  priority: ReminderPriority;
  related_entity_type?: string | null;
  related_entity_id?: number | null;
  channels: NotificationChannel[];
  is_read: boolean;
  read_at?: string | null;
  dedup_key?: string | null;
  created_at: string;
}

export interface DashboardStats {
  pending_requests: number;
  pending_payments: number;
  overdue_payments: number;
  upcoming_deadlines: number;
  total_assets: number;
  active_challenge?: SundayChallenge | null;
  wheel_entries_count: number;
  gifts_assigned: number;
  gifts_in_progress: number;
  gifts_delivered: number;
}

export interface UpcomingDeadlineItem {
  id: number;
  title: string;
  deadline: string;
  deadline_time?: string | null;
  priority: ReminderPriority;
  assignee?: User | null;
  type: 'reminder' | 'payment' | 'gift';
}

export interface DashboardOverview {
  stats: DashboardStats;
  upcoming_deadlines: UpcomingDeadlineItem[];
  pending_requests: RequestItem[];
  payment_overview: PaymentStats;
  gift_distribution: Gift[];
}

export interface PaymentStats {
  total_pending: number;
  total_due_soon: number;
  total_overdue: number;
  total_paid: number;
  total_cancelled: number;
  amount_pending: number;
  amount_paid: number;
  amount_overdue: number;
}

export interface GiftStats {
  total: number;
  assigned: number;
  in_progress: number;
  delivered: number;
  cancelled: number;
  overdue: number;
}
