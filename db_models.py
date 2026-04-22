"""ORM models for persistent storage."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ParkingConfiguration(Base):
    """Persisted parking lot configuration."""

    __tablename__ = "parking_configurations"

    uuid: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    parking_lot_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parking_lot_address: Mapped[str] = mapped_column(String(512), nullable=False)
    vacant_lot: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
