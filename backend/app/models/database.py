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


class ErrorLog(Base):
    __tablename__ = "error_log"

    id = Column(Integer, primary_key=True)
    error_type = Column(String(50), nullable=False)  # "groq_rate_limit" | "all_providers_down" | "chat_error" | "photo_error" | "lab_error"
    feature = Column(String(20), nullable=True)  # "chat" | "photo" | "lab"
    message = Column(Text, nullable=False)
    telegram_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
