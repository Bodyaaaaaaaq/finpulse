import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GameItemStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COLLECTED = "COLLECTED"


class GameItem(Base):
    __tablename__ = "game_items"
    __table_args__ = (Index("ix_game_items_lat_lng", "latitude", "longitude"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    points: Mapped[int] = mapped_column(Integer)
    status: Mapped[GameItemStatus] = mapped_column(
        Enum(GameItemStatus, name="game_item_status"),
        default=GameItemStatus.ACTIVE,
        server_default=GameItemStatus.ACTIVE.value,
        index=True,
    )
    collected_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )