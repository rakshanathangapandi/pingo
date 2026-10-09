from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class RequestType(str, Enum):
    PAYMENT = "payment"
    APPROVAL = "approval"
    DOCUMENT = "document"
    ASSET = "asset"
    OTHER = "other"


class RequestStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    CHECK = "check"
    UPI = "upi"
    OTHER = "other"


class AssetCategory(str, Enum):
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    VEHICLE = "vehicle"
    SOFTWARE = "software"
    MACHINERY = "machinery"
    OFFICE_SUPPLIES = "office_supplies"
    DOCUMENTS = "documents"
    OTHER = "other"


class AssetStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_MAINTENANCE = "in_maintenance"
    RETIRED = "retired"
    LOST = "lost"


class ChallengeStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class WheelEntryType(str, Enum):
    GIFT = "gift"
    REWARD = "reward"
    CHALLENGE = "challenge"
    ACTIVITY = "activity"
    CUSTOM = "custom"


class GiftStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    DEADLINE_UPCOMING = "deadline_upcoming"
    DEADLINE_OVERDUE = "deadline_overdue"
    PAYMENT_DUE = "payment_due"
    PAYMENT_OVERDUE = "payment_overdue"
    REQUEST_PENDING = "request_pending"
    REQUEST_APPROVED = "request_approved"
    REQUEST_REJECTED = "request_rejected"
    CHALLENGE_REMINDER = "challenge_reminder"
    WHEEL_REMINDER = "wheel_reminder"
    GIFT_DEADLINE = "gift_deadline"
    GIFT_STATUS_CHANGE = "gift_status_change"
    STATUS_CHANGE = "status_change"
    NEW_REQUEST = "new_request"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    created_at: datetime

    class Config:
        from_attributes = True


# Pagination
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Reminder schemas
class ReminderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    deadline: date
    deadline_time: Optional[time] = None
    priority: PriorityEnum = PriorityEnum.MEDIUM
    reminder_schedule: Optional[List[str]] = Field(default_factory=list)
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None


class ReminderCreate(ReminderBase):
    assignee_id: Optional[int] = None


class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    deadline: Optional[date] = None
    deadline_time: Optional[time] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[ReminderStatus] = None
    reminder_schedule: Optional[List[str]] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    assignee_id: Optional[int] = None


class ReminderResponse(ReminderBase):
    id: int
    status: ReminderStatus
    assignee_id: Optional[int] = None
    assignee: Optional[UserResponse] = None
    created_by_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReminderFilter(BaseModel):
    status: Optional[ReminderStatus] = None
    priority: Optional[PriorityEnum] = None
    assignee_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None


# Request schemas
class RequestBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    request_type: RequestType
    priority: PriorityEnum = PriorityEnum.MEDIUM
    due_date: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None
    supporting_documents: Optional[List[str]] = Field(default_factory=list)


class RequestCreate(RequestBase):
    assignee_id: Optional[int] = None


class RequestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    request_type: Optional[RequestType] = None
    priority: Optional[PriorityEnum] = None
    due_date: Optional[date] = None
    status: Optional[RequestStatus] = None
    assignee_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    supporting_documents: Optional[List[str]] = None
    resolution_notes: Optional[str] = None


class RequestStatusHistoryResponse(BaseModel):
    id: int
    old_status: Optional[RequestStatus] = None
    new_status: RequestStatus
    changed_by: Optional[UserResponse] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RequestResponse(RequestBase):
    id: int
    request_id: str
    status: RequestStatus
    requested_date: date
    completed_date: Optional[date] = None
    requester_id: Optional[int] = None
    requester: Optional[UserResponse] = None
    assignee_id: Optional[int] = None
    assignee: Optional[UserResponse] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    status_history: Optional[List[RequestStatusHistoryResponse]] = None

    class Config:
        from_attributes = True


class RequestFilter(BaseModel):
    status: Optional[RequestStatus] = None
    request_type: Optional[RequestType] = None
    priority: Optional[PriorityEnum] = None
    assignee_id: Optional[int] = None
    requester_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None


# Payment schemas
class PaymentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    vendor: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    due_date: date
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    supporting_document: Optional[str] = None


class PaymentCreate(PaymentBase):
    assignee_id: Optional[int] = None


class PaymentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    vendor: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    due_date: Optional[date] = None
    status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    supporting_document: Optional[str] = None
    assignee_id: Optional[int] = None


class PaymentStatusHistoryResponse(BaseModel):
    id: int
    old_status: Optional[PaymentStatus] = None
    new_status: PaymentStatus
    changed_by: Optional[UserResponse] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(PaymentBase):
    id: int
    status: PaymentStatus
    paid_date: Optional[date] = None
    assignee_id: Optional[int] = None
    assignee: Optional[UserResponse] = None
    created_by_id: Optional[int] = None
    reminder_sent_due_soon: bool
    reminder_sent_overdue: bool
    created_at: datetime
    updated_at: datetime
    status_history: Optional[List[PaymentStatusHistoryResponse]] = None

    class Config:
        from_attributes = True


class PaymentFilter(BaseModel):
    status: Optional[PaymentStatus] = None
    assignee_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


class PaymentStatsResponse(BaseModel):
    total_pending: int
    total_due_soon: int
    total_overdue: int
    total_paid: int
    total_cancelled: int
    amount_pending: float
    amount_paid: float
    amount_overdue: float


# Asset schemas
class AssetDocument(BaseModel):
    name: str
    url: str
    type: str  # "pdf", "image", "certificate", "warranty", "other"
    uploaded_at: datetime


class AssetExternalLink(BaseModel):
    name: str
    url: str
    description: Optional[str] = None


class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: AssetCategory
    description: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_expiry: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    documents: Optional[List[AssetDocument]] = Field(default_factory=list)
    external_links: Optional[List[AssetExternalLink]] = Field(default_factory=list)


class AssetCreate(AssetBase):
    asset_id: str = Field(..., min_length=1, max_length=50)
    assignee_id: Optional[int] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[AssetCategory] = None
    description: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_expiry: Optional[date] = None
    location: Optional[str] = None
    status: Optional[AssetStatus] = None
    assignee_id: Optional[int] = None
    notes: Optional[str] = None
    documents: Optional[List[AssetDocument]] = None
    external_links: Optional[List[AssetExternalLink]] = None


class AssetStatusHistoryResponse(BaseModel):
    id: int
    old_status: Optional[AssetStatus] = None
    new_status: AssetStatus
    changed_by: Optional[UserResponse] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AssetResponse(AssetBase):
    id: int
    asset_id: str
    status: AssetStatus
    assignee_id: Optional[int] = None
    assignee: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    status_history: Optional[List[AssetStatusHistoryResponse]] = None

    class Config:
        from_attributes = True


class AssetFilter(BaseModel):
    category: Optional[AssetCategory] = None
    status: Optional[AssetStatus] = None
    assignee_id: Optional[int] = None
    search: Optional[str] = None


# Sunday Challenge schemas
class SundayChallengeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    reward: Optional[str] = None
    challenge_date: date


class SundayChallengeCreate(SundayChallengeBase):
    pass


class SundayChallengeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    reward: Optional[str] = None
    status: Optional[ChallengeStatus] = None


class ChallengeParticipationResponse(BaseModel):
    id: int
    challenge_id: int
    user: UserResponse
    status: ChallengeStatus
    completed_at: Optional[datetime] = None
    submission_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SundayChallengeResponse(SundayChallengeBase):
    id: int
    status: ChallengeStatus
    created_by_id: Optional[int] = None
    creator: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    participations: Optional[List[ChallengeParticipationResponse]] = None

    class Config:
        from_attributes = True


# Wheel schemas
class WheelEntryBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    entry_type: WheelEntryType = WheelEntryType.GIFT
    value: Optional[str] = None
    probability: float = Field(1.0, ge=0)
    is_active: bool = True
    order: int = 0
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None


class WheelEntryCreate(WheelEntryBase):
    pass


class WheelEntryUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=255)
    entry_type: Optional[WheelEntryType] = None
    value: Optional[str] = None
    probability: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    order: Optional[int] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None


class WheelEntryResponse(WheelEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WheelSpinCreate(BaseModel):
    # No input needed - server picks randomly based on probabilities
    pass


class WheelSpinResponse(BaseModel):
    id: int
    user: Optional[UserResponse] = None
    entry_id: Optional[int] = None
    won_label: str
    won_value: Optional[str] = None
    won_entry_type: WheelEntryType
    spin_date: date
    is_claimed: bool
    claimed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Gift schemas
class GiftBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    recipient_id: Optional[int] = None
    assignee_id: Optional[int] = None
    expected_delivery_date: Optional[date] = None
    delivery_notes: Optional[str] = None


class GiftCreate(GiftBase):
    gift_id: str = Field(..., min_length=1, max_length=50)


class GiftUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    recipient_id: Optional[int] = None
    assignee_id: Optional[int] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[GiftStatus] = None
    delivery_notes: Optional[str] = None
    proof_document: Optional[str] = None


class GiftStatusHistoryResponse(BaseModel):
    id: int
    old_status: Optional[GiftStatus] = None
    new_status: GiftStatus
    changed_by: Optional[UserResponse] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GiftResponse(GiftBase):
    id: int
    gift_id: str
    status: GiftStatus
    assigned_date: date
    actual_delivery_date: Optional[date] = None
    proof_document: Optional[str] = None
    assigned_by_id: Optional[int] = None
    assigned_by: Optional[UserResponse] = None
    recipient: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    status_history: Optional[List[GiftStatusHistoryResponse]] = None

    class Config:
        from_attributes = True


class GiftFilter(BaseModel):
    status: Optional[GiftStatus] = None
    recipient_id: Optional[int] = None
    assignee_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    search: Optional[str] = None


class GiftStatsResponse(BaseModel):
    total: int
    assigned: int
    in_progress: int
    delivered: int
    cancelled: int
    overdue: int


# Notification schemas
class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: NotificationType
    priority: PriorityEnum = PriorityEnum.MEDIUM
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    channels: List[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.IN_APP])


class NotificationCreate(NotificationBase):
    user_id: int
    dedup_key: Optional[str] = None


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    dedup_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationFilter(BaseModel):
    is_read: Optional[bool] = None
    notification_type: Optional[NotificationType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# Dashboard schemas
class DashboardStats(BaseModel):
    pending_requests: int
    pending_payments: int
    overdue_payments: int
    upcoming_deadlines: int
    total_assets: int
    active_challenge: Optional[SundayChallengeResponse] = None
    gifts_assigned: int
    gifts_in_progress: int
    gifts_delivered: int


class UpcomingDeadlineItem(BaseModel):
    id: int
    title: str
    deadline: date
    deadline_time: Optional[time] = None
    priority: PriorityEnum
    assignee: Optional[UserResponse] = None
    type: str  # "reminder", "payment", "gift"


class DashboardOverview(BaseModel):
    stats: DashboardStats
    upcoming_deadlines: List[UpcomingDeadlineItem]
    pending_requests: List[RequestResponse]
    payment_overview: PaymentStatsResponse
    gift_distribution: List[GiftResponse]


# Audit log
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user: Optional[UserResponse] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True