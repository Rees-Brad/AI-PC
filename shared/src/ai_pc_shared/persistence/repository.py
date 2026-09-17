from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_pc_shared.character.sheet import CharacterSheet
from ai_pc_shared.character.sheet import Condition as SheetCondition
from ai_pc_shared.character.sheet import InventoryItem as SheetInventoryItem
from ai_pc_shared.persistence import models


def get_character_row(session: Session, name: str) -> models.Character | None:
    return session.scalar(select(models.Character).where(models.Character.name == name))


def load_character_sheet(session: Session, name: str) -> CharacterSheet | None:
    row = get_character_row(session, name)
    if row is None:
        return None
    data = dict(row.sheet_data)
    data["inventory"] = [
        SheetInventoryItem(
            name=item.name, quantity=item.quantity, equipped=item.equipped, notes=item.notes
        ).model_dump()
        for item in row.inventory_items
    ]
    data["conditions"] = [
        SheetCondition(name=cond.name, duration=cond.duration).model_dump()
        for cond in row.conditions
    ]
    return CharacterSheet.model_validate(data)


def save_character_sheet(session: Session, sheet: CharacterSheet) -> models.Character:
    row = get_character_row(session, sheet.name)
    sheet_data = sheet.model_dump(mode="json", exclude={"inventory", "conditions"})

    if row is None:
        row = models.Character(name=sheet.name, sheet_data=sheet_data)
        session.add(row)
    else:
        row.sheet_data = sheet_data

    row.inventory_items = [
        models.InventoryItem(
            name=item.name, quantity=item.quantity, equipped=item.equipped, notes=item.notes
        )
        for item in sheet.inventory
    ]
    row.conditions = [
        models.ConditionRow(name=cond.name, duration=cond.duration) for cond in sheet.conditions
    ]

    session.commit()
    return row


def append_session_log(
    session: Session, character_id: int, session_id: str, role: str, content: dict
) -> None:
    session.add(
        models.SessionLog(
            character_id=character_id, session_id=session_id, role=role, content=content
        )
    )
    session.commit()


def get_session_log(
    session: Session, character_id: int, session_id: str, limit: int = 50
) -> list[models.SessionLog]:
    stmt = (
        select(models.SessionLog)
        .where(
            models.SessionLog.character_id == character_id,
            models.SessionLog.session_id == session_id,
        )
        .order_by(models.SessionLog.created_at.desc())
        .limit(limit)
    )
    return list(reversed(session.scalars(stmt).all()))


def save_session_summary(
    session: Session, character_id: int, session_id: str, summary_text: str
) -> None:
    session.add(
        models.SessionSummary(
            character_id=character_id, session_id=session_id, summary_text=summary_text
        )
    )
    session.commit()


def get_session_summaries(session: Session, character_id: int) -> list[models.SessionSummary]:
    stmt = (
        select(models.SessionSummary)
        .where(models.SessionSummary.character_id == character_id)
        .order_by(models.SessionSummary.created_at.asc())
    )
    return list(session.scalars(stmt).all())
