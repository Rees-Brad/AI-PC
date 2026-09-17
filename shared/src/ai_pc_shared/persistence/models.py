from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    # Full CharacterSheet, serialized (abilities, hp, ac, slots, features, ...).
    sheet_data: Mapped[dict] = mapped_column(JSON)
    # System-specific extras that don't belong on the generic sheet.
    dnd5e_data: Mapped[dict] = mapped_column(JSON, default=dict)

    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    conditions: Mapped[list["ConditionRow"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    name: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(default=1)
    equipped: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(String, default="")

    character: Mapped["Character"] = relationship(back_populates="inventory_items")


class ConditionRow(Base):
    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    name: Mapped[str] = mapped_column(String)
    duration: Mapped[str | None] = mapped_column(String, nullable=True)

    character: Mapped["Character"] = relationship(back_populates="conditions")


class SessionLog(Base):
    __tablename__ = "session_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    session_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    role: Mapped[str] = mapped_column(String)  # "user" | "assistant" | "tool"
    content: Mapped[dict] = mapped_column(JSON)


class SessionSummary(Base):
    __tablename__ = "session_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    session_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    summary_text: Mapped[str] = mapped_column(String)
