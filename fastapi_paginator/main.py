from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from sqlalchemy import select

from .helpers import paginate_per_page, paginate_limit_offset, cursor_paginate
from .middlewares import middleware
from .models import db, Todo
from .schemas import TodoSchema, PaginatedPerPageResponse, PaginatedLimitOffsetResponse, CursorPaginatedResponse


@asynccontextmanager
async def initialize_todos(_app) -> None:
    await db.create_all()

    async with db.begin() as session:
        session.add_all([Todo(name=str(i), description=f'task-{i}') for i in range(50)])

    yield
    await db.drop_all()


app = FastAPI(lifespan=initialize_todos, middleware=middleware)


@app.get('/offset-limit', response_model=PaginatedLimitOffsetResponse[TodoSchema])
async def get_offset_limit_todos(
        limit: int = Query(100, ge=0),
        offset: int = Query(0, ge=0)
):
    """Pagination based on a limit/offset model."""
    return await paginate_limit_offset(select(Todo), limit, offset)


@app.get('/per-page', response_model=PaginatedPerPageResponse[TodoSchema])
async def get_per_page_todos(
        page: int = Query(1, ge=1), per_page: int = Query(100, ge=0)
):
    """Pagination based on a page/per_page model."""
    return await paginate_per_page(select(Todo), page, per_page)


@app.get('/cursor', response_model=CursorPaginatedResponse[TodoSchema])
async def get_cursor_todos(
        max_results: int = Query(100, ge=1),
        cursor: str = Query(None)
):
    """Pagination based on a cursor model."""
    return await cursor_paginate(select(Todo), max_results, cursor)
