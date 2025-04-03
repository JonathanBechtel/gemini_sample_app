import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # For PostgreSQL specific UUID type
from sqlalchemy import UUID as Standard_UUID # Standard, use if cross-DB compatibility is key

from app.db.base import Base
import enum

class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    pending_verification = "pending_verification"

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=True) # Nullable if email is primary login
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True) # Nullable for OAuth-only users
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.pending_verification, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    oauth_accounts = relationship("UserOAuthAccount", back_populates="user", cascade="all, delete-orphan")

class UserOAuthAccount(Base):
    __tablename__ = "user_oauth_accounts"

    oauth_account_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # e.g., 'google', 'github'
    provider_user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False) # ID from the provider
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # Optional: access_token, refresh_token (encrypted!), expires_at, scopes

    user = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        # Unique constraint for a user from a specific provider
        UniqueConstraint('provider_name', 'provider_user_id', name='uq_provider_user'),
    )

# Add other models here as needed (PasswordResets, EmailVerifications, Sessions, AuditLogs)
# Example Session Model Stub:
class Session(Base):
    __tablename__ = "sessions"
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False) # Hash of refresh token
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user = relationship("User")