import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRewardStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ISSUED = "ISSUED"


class UserReward(Base):
    __tablename__ = "user_rewards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    reward_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rewards.id", ondelete="RESTRICT")
    )
    status: Mapped[UserRewardStatus] = mapped_column(
        Enum(UserRewardStatus, name="user_reward_status"),
        default=UserRewardStatus.REQUESTED,
        server_default=UserRewardStatus.REQUESTED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )