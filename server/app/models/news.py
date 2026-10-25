import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NewsCategory(str, enum.Enum):
    CURRENCY = "CURRENCY"
    CRYPTO = "CRYPTO"
    ECONOMY = "ECONOMY"


class News(Base):
    __tablename__ = "news"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(String(300))
    category: Mapped[NewsCategory] = mapped_column(
        Enum(NewsCategory, name="news_category"), index=True
    )
    source_url: Mapped[str] = mapped_column(String(1000), unique=True)
    source_name: Mapped[str] = mapped_column(String(100))
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
