import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MetalType(str, enum.Enum):
    GOLD = "GOLD"
    SILVER = "SILVER"
    PLATINUM = "PLATINUM"
    PALLADIUM = "PALLADIUM"


class MetalRate(Base):
    __tablename__ = "metal_rates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    metal: Mapped[MetalType] = mapped_column(
        Enum(MetalType, name="metal_type"), unique=True
    )
    price_per_gram_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    previous_price_per_gram_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )