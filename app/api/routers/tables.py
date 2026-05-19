from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db.session import get_db
from app.db.models import Table, User
from app.schemas import TableCreate, TableOut

router = APIRouter(prefix="/tables", tags=["tables"])


@router.post("", response_model=TableOut, status_code=201)
async def create_table(
    req: TableCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    table = Table(**req.model_dump(), owner_id=user.id)
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table


@router.get("", response_model=list[TableOut])
async def list_tables(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Table).where(Table.owner_id == user.id))
    return result.scalars().all()


@router.get("/{table_id}", response_model=TableOut)
async def get_table(
    table_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Table).where(Table.id == table_id, Table.owner_id == user.id)
    )
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(404, "Table not found")
    return table


@router.delete("/{table_id}", status_code=204)
async def delete_table(
    table_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Table).where(Table.id == table_id, Table.owner_id == user.id)
    )
    table = result.scalar_one_or_none()
    if not table:
        raise HTTPException(404, "Table not found")
    await db.delete(table)
    await db.commit()
