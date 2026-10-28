import uuid

from sqlalchemy import CheckConstraint, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Reward(Base):
    __tablename__ = "rewards"
    __table_args__ = (
        CheckConstraint("cost_points > 0", name="ck_rewards_cost_points_positive"),
        CheckConstraint("stock >= 0", name="ck_rewards_stock_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000))
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cost_points: Mapped[int] = mapped_column(Integer)
    stock: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
