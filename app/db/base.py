from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData
from sqlalchemy.sql import func
from sqlalchemy import Column, DateTime
from app.core.config import settings
import uuid
from sqlalchemy.dialects.postgresql import UUID # Or use sqlalchemy.types.UUID for cross-DB

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True) # echo=True for debugging SQL
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Define naming convention for constraints for Alembic autogenerate
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=convention)

class Base(DeclarativeBase):
    metadata = metadata_obj

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
     DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
         DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session