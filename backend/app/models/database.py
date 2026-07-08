"""
SQLAlchemy async models for VetAI.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

from app.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def init_db():
    """Create all tables if they don't exist, and migrate schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate: add 'provider' column to usage_log if missing
        try:
            await conn.execute(text("ALTER TABLE usage_log ADD COLUMN provider VARCHAR(20)"))
        except Exception:
            pass  # Column already exists
        # Migrate: add 'rating' column to diagnoses if missing
        try:
            await conn.execute(text("ALTER TABLE diagnoses ADD COLUMN rating INTEGER"))
        except Exception:
            pass  # Column already exists
        # Migrate: create chat_feedback table if missing
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    message_text TEXT NOT NULL,
                    reaction VARCHAR(10) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
        except Exception:
            pass
        # Migrate: add 'reminder_sent' column to users if missing
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN reminder_sent BOOLEAN DEFAULT 0"))
        except Exception:
            pass
        # Migrate: retention + referral columns on users
        for _stmt in (
            "ALTER TABLE users ADD COLUMN last_reminder_at DATETIME",
            "ALTER TABLE users ADD COLUMN streak_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN last_active_date VARCHAR(10)",
            "ALTER TABLE users ADD COLUMN referred_by INTEGER",
            "ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN source VARCHAR(40)",
        ):
            try:
                await conn.execute(text(_stmt))
            except Exception:
                pass  # Column already exists
        # Index for analytics/funnel queries
        for _idx in (
            "CREATE INDEX IF NOT EXISTS ix_usage_log_used_at ON usage_log(used_at)",
            "CREATE INDEX IF NOT EXISTS ix_analytics_event_created_at ON analytics_event(created_at)",
            "CREATE INDEX IF NOT EXISTS ix_analytics_event_telegram_id ON analytics_event(telegram_id)",
        ):
            try:
                await conn.execute(text(_idx))
            except Exception:
                pass


async def get_session():
    """Async generator for dependency injection of DB sessions."""
    async with async_session() as session:
        yield session


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=True)
    username = Column(String(100), nullable=True)
    language_code = Column(String(10), default="ru")
    is_premium = Column(Boolean, default=False)
    platform = Column(String(20), nullable=True)  # ios | android | desktop | web
    login_count = Column(Integer, default=1)
    last_login = Column(DateTime, default=datetime.utcnow)
    city = Column(String(100), nullable=True)
    subscription_tier = Column(String(20), default="beta")  # beta | free | monthly | annual
    subscription_expires = Column(DateTime, nullable=True)
    daily_limit_override = Column(Integer, nullable=True)  # if set, overrides default daily limit
    reminder_sent = Column(Boolean, default=False)
    last_reminder_at = Column(DateTime, nullable=True)  # last re-engagement reminder sent
    # Retention: daily-usage streak
    streak_count = Column(Integer, default=0)
    last_active_date = Column(String(10), nullable=True)  # ISO date of last usage
    # Referral / viral loop
    referred_by = Column(Integer, nullable=True)  # telegram_id of the referrer
    referral_count = Column(Integer, default=0)  # how many users this user invited
    source = Column(String(40), nullable=True)  # acquisition: organic | referral | src_<channel>
    created_at = Column(DateTime, default=datetime.utcnow)

    pets = relationship("Pet", back_populates="owner")
    diagnoses = relationship("Diagnosis", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100))
    species = Column(String(20))  # cat | dog
    breed = Column(String(100), nullable=True)
    age_months = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    photo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="pets")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)
    type = Column(String(20))  # photo | lab_results | chat
    input_url = Column(String(500), nullable=True)  # S3 URL for uploaded file
    result_json = Column(Text)  # JSON with diagnosis details
    condition = Column(String(200), nullable=True)
    confidence = Column(Float, nullable=True)
    severity = Column(String(20), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="diagnoses")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)
    messages_json = Column(Text)  # JSON array of messages
    preliminary_assessment = Column(Text, nullable=True)
    urgency = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feature = Column(String(20), nullable=False)  # "photo" | "chat" | "lab"
    provider = Column(String(20), nullable=True)  # "groq" | "claude" | None
    used_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="usage_logs")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_text = Column(Text, nullable=False)  # bot message that was rated
    reaction = Column(String(10), nullable=False)  # "like" | "dislike"
    created_at = Column(DateTime, default=datetime.utcnow)


class ErrorLog(Base):
    __tablename__ = "error_log"

    id = Column(Integer, primary_key=True)
    error_type = Column(String(50), nullable=False)  # "groq_rate_limit" | "all_providers_down" | "chat_error" | "photo_error" | "lab_error"
    feature = Column(String(20), nullable=True)  # "chat" | "photo" | "lab"
    message = Column(Text, nullable=False)
    telegram_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalyticsEvent(Base):
    """Lightweight product-analytics events (funnel, activation, retention)."""
    __tablename__ = "analytics_event"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=True, index=True)
    event = Column(String(50), nullable=False)  # app_open | onboarding_start | onboarding_complete | ai_start | ai_success | ai_failure | invite_click | share_click | referral_landed | paywall_view | ...
    props = Column(Text, nullable=True)  # JSON string with extra context (feature, urgency, provider, session_id)
    session_id = Column(String(40), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Referral(Base):
    """Audit trail of successful referrals (one row per invited user)."""
    __tablename__ = "referral"

    id = Column(Integer, primary_key=True)
    referrer_telegram_id = Column(Integer, nullable=False, index=True)
    invitee_telegram_id = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PendingAttribution(Base):
    """Source captured from a bot /start <param> before the user registers.
    Applied to User.source at /auth time (robust attribution for t.me/<bot>?start=src_X links)."""
    __tablename__ = "pending_attribution"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    source = Column(String(40), nullable=False)  # "src_<channel>" | "referral"
    created_at = Column(DateTime, default=datetime.utcnow)
