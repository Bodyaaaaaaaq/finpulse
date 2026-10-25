import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AssetType(str, enum.Enum):
    CURRENCY = "CURRENCY"
    CRYPTO = "CRYPTO"
    METAL = "METAL"


class ConversionHistory(Base):
    __tablename__ = "conversion_history"
    __table_args__ = (Index("ix_conversion_history_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE")
    )
    from_type: Mapped[AssetType] = mapped_column(Enum(AssetType, name="asset_type"))
    to_type: Mapped[AssetType] = mapped_column(Enum(AssetType, name="asset_type"))
    from_code: Mapped[str] = mapped_column(String(20))
    to_code: Mapped[str] = mapped_column(String(20))
    amount_from: Mapped[Decimal] = mapped_column(Numeric(30, 10))
    amount_to: Mapped[Decimal] = mapped_column(Numeric(30, 10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )