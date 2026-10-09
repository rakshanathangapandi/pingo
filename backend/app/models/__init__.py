import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Time, Boolean,
    ForeignKey, Enum, JSON, Index, UniqueConstraint, CheckConstraint, Float
)
from sqlalchemy.orm import relationship, declarative_base
from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    reminders = relationship("Reminder", back_populates="assignee", foreign_keys="Reminder.assignee_id")
    created_reminders = relationship("Reminder", back_populates="creator", foreign_keys="Reminder.created_by_id")
    requests = relationship("Request", back_populates="requester", foreign_keys="Request.requester_id")
    assigned_requests = relationship("Request", back_populates="assignee", foreign_keys="Request.assignee_id")
    payments = relationship("Payment", back_populates="assignee", foreign_keys="Payment.assignee_id")
    assets = relationship("Asset", back_populates="assignee", foreign_keys="Asset.assignee_id")
    gifts = relationship("Gift", back_populates="recipient", foreign_keys="Gift.recipient_id")
    assigned_gifts = relationship("Gift", back_populates="assignee", foreign_keys="Gift.assignee_id")
    notifications = relationship("Notification", back_populates="user", foreign_keys="Notification.user_id")
    challenge_participations = relationship("ChallengeParticipation", back_populates="user")
    wheel_spins = relationship("WheelSpin", back_populates="user")

    # Web push subscriptions
    push_subscriptions = relationship("PushSubscription", back_populates="user")


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="push_subscriptions")

    __table_args__ = (UniqueConstraint("user_id", "endpoint", name="uq_user_endpoint"),)


class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(Date, nullable=False)
    deadline_time = Column(Time, nullable=True)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM, nullable=False)
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING, nullable=False)

    # Assignment
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Reminder schedule (JSON array of dates/times to remind before deadline)
    reminder_schedule = Column(JSON, nullable=True, default=list)  # e.g., ["3 days before", "1 day before", "on deadline"]

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(100), nullable=True)  # e.g., "weekly", "monthly", "yearly"

    # Source entity this reminder was auto-collected from (payment, gift, challenge, wheel, etc.)
    related_entity_type = Column(String(50), nullable=True, index=True)
    related_entity_id = Column(Integer, nullable=True, index=True)

    # Completion
    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assignee = relationship("User", back_populates="reminders", foreign_keys=[assignee_id])
    creator = relationship("User", back_populates="created_reminders", foreign_keys=[created_by_id])
    completer = relationship("User", foreign_keys=[completed_by_id])
    notification_logs = relationship("ReminderNotificationLog", back_populates="reminder")


class ReminderNotificationLog(Base):
    __tablename__ = "reminder_notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)  # "email", "push", "in_app"
    scheduled_for = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # "pending", "sent", "failed"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reminder = relationship("Reminder", back_populates="notification_logs")

    __table_args__ = (Index("ix_reminder_notif_scheduled_status", "scheduled_for", "status"),)


class RequestType(str, enum.Enum):
    PAYMENT = "payment"
    APPROVAL = "approval"
    DOCUMENT = "document"
    ASSET = "asset"
    OTHER = "other"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., REQ-2024-001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    request_type = Column(Enum(RequestType), nullable=False, index=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False, index=True)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM, nullable=False)

    # Dates
    requested_date = Column(Date, default=datetime.utcnow().date(), nullable=False)
    due_date = Column(Date, nullable=True, index=True)
    completed_date = Column(Date, nullable=True)

    # Assignment
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metadata
    request_metadata = Column(JSON, nullable=True, default=dict)  # Flexible fields for different request types
    supporting_documents = Column(JSON, nullable=True, default=list)  # Array of document URLs

    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    requester = relationship("User", back_populates="requests", foreign_keys=[requester_id])
    assignee = relationship("User", back_populates="assigned_requests", foreign_keys=[assignee_id])
    resolver = relationship("User", foreign_keys=[resolved_by_id])
    status_history = relationship("RequestStatusHistory", back_populates="request")


class RequestStatusHistory(Base):
    __tablename__ = "request_status_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(Enum(RequestStatus), nullable=True)
    new_status = Column(Enum(RequestStatus), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    request = relationship("Request", back_populates="status_history")
    changed_by = relationship("User")


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    CHECK = "check"
    UPI = "upi"
    OTHER = "other"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    vendor = Column(String(255), nullable=False)  # Vendor/Company/Person
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    due_date = Column(Date, nullable=False, index=True)
    paid_date = Column(Date, nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_reference = Column(String(255), nullable=True)  # Transaction ID, check number, etc.

    # Assignment
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Details
    notes = Column(Text, nullable=True)
    supporting_document = Column(String(500), nullable=True)  # URL to invoice/receipt

    # Reminder settings
    reminder_sent_due_soon = Column(Boolean, default=False)
    reminder_sent_overdue = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assignee = relationship("User", back_populates="payments", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[created_by_id])
    status_history = relationship("PaymentStatusHistory", back_populates="payment")


class PaymentStatusHistory(Base):
    __tablename__ = "payment_status_history"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(Enum(PaymentStatus), nullable=True)
    new_status = Column(Enum(PaymentStatus), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    payment = relationship("Payment", back_populates="status_history")
    changed_by = relationship("User")


class AssetCategory(str, enum.Enum):
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    VEHICLE = "vehicle"
    SOFTWARE = "software"
    MACHINERY = "machinery"
    OFFICE_SUPPLIES = "office_supplies"
    DOCUMENTS = "documents"
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_MAINTENANCE = "in_maintenance"
    RETIRED = "retired"
    LOST = "lost"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., AST-2024-001
    name = Column(String(255), nullable=False)
    category = Column(Enum(AssetCategory), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Assignment
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Purchase info
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Float, nullable=True)
    vendor = Column(String(255), nullable=True)
    warranty_expiry = Column(Date, nullable=True)

    # Status & Location
    status = Column(Enum(AssetStatus), default=AssetStatus.AVAILABLE, nullable=False, index=True)
    location = Column(String(255), nullable=True)

    # Documents & Links
    documents = Column(JSON, nullable=True, default=list)  # Array of {name, url, type, uploaded_at}
    external_links = Column(JSON, nullable=True, default=list)  # Array of {name, url, description}

    # Notes
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assignee = relationship("User", back_populates="assets", foreign_keys=[assignee_id])
    status_history = relationship("AssetStatusHistory", back_populates="asset")


class AssetStatusHistory(Base):
    __tablename__ = "asset_status_history"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(Enum(AssetStatus), nullable=True)
    new_status = Column(Enum(AssetStatus), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    asset = relationship("Asset", back_populates="status_history")
    changed_by = relationship("User")


class ChallengeStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SundayChallenge(Base):
    __tablename__ = "sunday_challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    reward = Column(String(255), nullable=True)

    # Challenge date (the Sunday this challenge is for)
    challenge_date = Column(Date, unique=True, index=True, nullable=False)

    # Status
    status = Column(Enum(ChallengeStatus), default=ChallengeStatus.ACTIVE, nullable=False)

    # Admin who created/configured
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User")
    participations = relationship("ChallengeParticipation", back_populates="challenge")


class ChallengeParticipation(Base):
    __tablename__ = "challenge_participations"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("sunday_challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Participation status
    status = Column(Enum(ChallengeStatus), default=ChallengeStatus.ACTIVE, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    submission_notes = Column(Text, nullable=True)  # User's submission/completion notes

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    challenge = relationship("SundayChallenge", back_populates="participations")
    user = relationship("User", back_populates="challenge_participations")

    __table_args__ = (UniqueConstraint("challenge_id", "user_id", name="uq_challenge_user"),)


class WheelEntryType(str, enum.Enum):
    GIFT = "gift"
    REWARD = "reward"
    CHALLENGE = "challenge"
    ACTIVITY = "activity"
    CUSTOM = "custom"


class WheelEntry(Base):
    __tablename__ = "wheel_entries"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(255), nullable=False)  # Display text on wheel
    entry_type = Column(Enum(WheelEntryType), default=WheelEntryType.GIFT, nullable=False)
    value = Column(String(255), nullable=True)  # Description/value of the entry
    probability = Column(Float, default=1.0, nullable=False)  # Relative probability weight
    is_active = Column(Boolean, default=True, nullable=False)
    order = Column(Integer, default=0, nullable=False)  # Display order
    color = Column(String(7), nullable=True)  # Hex color for wheel segment
    icon = Column(String(100), nullable=True)  # Icon name

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class WheelSpin(Base):
    __tablename__ = "wheel_spins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    entry_id = Column(Integer, ForeignKey("wheel_entries.id", ondelete="SET NULL"), nullable=True)

    # Result
    won_label = Column(String(255), nullable=False)
    won_value = Column(String(255), nullable=True)
    won_entry_type = Column(Enum(WheelEntryType), nullable=False)

    # Spin metadata
    spin_date = Column(Date, default=datetime.utcnow().date(), nullable=False, index=True)
    is_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="wheel_spins")
    entry = relationship("WheelEntry")


class GiftStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Gift(Base):
    __tablename__ = "gifts"

    id = Column(Integer, primary_key=True, index=True)
    gift_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., GFT-2024-001
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Recipient & Assignment
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # Person responsible for delivery

    # Dates
    assigned_date = Column(Date, default=datetime.utcnow().date(), nullable=False)
    expected_delivery_date = Column(Date, nullable=True, index=True)
    actual_delivery_date = Column(Date, nullable=True)

    # Status
    status = Column(Enum(GiftStatus), default=GiftStatus.ASSIGNED, nullable=False, index=True)

    # Details
    delivery_notes = Column(Text, nullable=True)
    proof_document = Column(String(500), nullable=True)  # URL to proof of delivery (image, signature, etc.)

    # Admin who assigned
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    recipient = relationship("User", back_populates="gifts", foreign_keys=[recipient_id])
    assignee = relationship("User", back_populates="assigned_gifts", foreign_keys=[assignee_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    status_history = relationship("GiftStatusHistory", back_populates="gift")


class GiftStatusHistory(Base):
    __tablename__ = "gift_status_history"

    id = Column(Integer, primary_key=True, index=True)
    gift_id = Column(Integer, ForeignKey("gifts.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(Enum(GiftStatus), nullable=True)
    new_status = Column(Enum(GiftStatus), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    gift = relationship("Gift", back_populates="status_history")
    changed_by = relationship("User")


class NotificationType(str, enum.Enum):
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


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM, nullable=False)

    # Related entity (polymorphic)
    related_entity_type = Column(String(50), nullable=True)  # "reminder", "request", "payment", "gift", "challenge", "wheel"
    related_entity_id = Column(Integer, nullable=True, index=True)

    # Delivery channels
    channels = Column(JSON, default=["in_app"], nullable=False)  # ["in_app", "email", "push"]

    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Deduplication key (to avoid duplicate notifications)
    dedup_key = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_notif_user_unread", "user_id", "is_read"),
        Index("ix_notif_dedup", "dedup_key"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., "create_reminder", "update_payment"
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., "reminder", "payment"
    entity_id = Column(Integer, nullable=True, index=True)

    # Changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Request info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (Index("ix_audit_entity", "entity_type", "entity_id"),)