import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CryptoRate(Base):
    __tablename__ = "crypto_rates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    coin_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    change_24h: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )