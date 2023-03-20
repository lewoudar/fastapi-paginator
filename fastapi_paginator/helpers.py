import typing

from cryptography.fernet import Fernet
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .middlewares import request_object
from .models import db, Todo

# In a production environment, you should generate it once
# and store it in a secure place
secret_key = Fernet.generate_key()
f = Fernet(secret_key)


def encode_id(identifier: int) -> str:
    encoded_identifier = f.encrypt(str(identifier).encode())
    return encoded_identifier.decode()


def decode_id(token: str) -> int:
    encoded_identifier = f.decrypt(token.encode())
    return int(encoded_identifier.decode())


class PagePaginator:
    def __init__(self, session: AsyncSession, query: Select, page: int, per_page: int):
        self.session = session
        self.query = query
        self.page = page
        self.per_page = per_page
        self.limit = per_page * page
        self.offset = (page - 1) * per_page
        self.request = request_object.get()
        # computed later
        self.number_of_pages = 0
        self.next_page = ''
        self.previous_page = ''

    def _get_next_page(self) -> typing.Optional[str]:
        if self.page >= self.number_of_pages:
            return

        url = self.request.url.include_query_params(page=self.page + 1)
        return str(url)

    def _get_previous_page(self) -> typing.Optional[str]:
        if self.page == 1 or self.page > self.number_of_pages + 1:
            return

        url = self.request.url.include_query_params(page=self.page - 1)
        return str(url)

    async def get_response(self) -> dict:
        return {
            'count': await self._get_total_count(),
            'next_page': self._get_next_page(),
            'previous_page': self._get_previous_page(),
            'items': [todo for todo in await self.session.scalars(self.query.slice(self.offset, self.limit))]
        }

    def _get_number_of_pages(self, count: int) -> int:
        rest = count % self.per_page
        quotient = count // self.per_page
        return quotient if not rest else quotient + 1

    async def _get_total_count(self) -> int:
        count = await self.session.scalar(select(func.count()).select_from(self.query.subquery()))
        self.number_of_pages = self._get_number_of_pages(count)
        return count


class CursorPaginator:
    def __init__(self, session: AsyncSession, query: Select, max_results: int, cursor: typing.Optional[str]):
        self.session = session
        self.query = query
        self.max_results = max_results
        self.cursor = cursor
        self.request = request_object.get()
        # computed later
        self.next_cursor: typing.Optional[str] = None
        self.previous_cursor: typing.Optional[str] = None

    async def _get_next_todos(self, query: Select) -> typing.List[Todo]:
        # if we requested 10 items and when fetching 10 + 1, we have 10 or less
        # this means there are no more items, so we don't set self.next_cursor
        initial_todos = [item for item in await self.session.scalars(query)]
        if len(initial_todos) < self.max_results + 1:
            return initial_todos
        else:
            todos = initial_todos[:-1]
            self.next_cursor = encode_id(todos[-1].id)
            return todos

    async def get_response(self):
        if self.cursor is None:
            query = self.query.limit(self.max_results + 1)
        else:
            ident = decode_id(self.cursor)
            query = self.query.where(Todo.id > ident).limit(self.max_results + 1)

        todos = await self._get_next_todos(query)

        return {
            'count': len(todos),
            'previous_page': await self._get_previous_page(),
            'next_page': self._get_next_page(),
            # order is important, self.previous_cursor is computed in method self._get_previous_page
            'previous_cursor': self.previous_cursor,
            'next_cursor': self.next_cursor,
            'items': todos
        }

    def _get_url(self, cursor: str) -> str:
        # we don't use request.url facilities because it will escape some characters (=) :D
        url = self.request.url
        return f'{url.scheme}://{url.netloc}{url.path}?max_results={self.max_results}&cursor={cursor}'

    def _get_next_page(self) -> typing.Optional[str]:
        if self.next_cursor is None:
            return
        return self._get_url(self.next_cursor)

    async def _get_previous_todos(self, last_todo_id: int) -> typing.List[Todo]:
        query = self.query.where(Todo.id < last_todo_id).order_by(Todo.id.desc()).limit(self.max_results)
        todos = [todo for todo in await self.session.scalars(query)]
        return todos

    async def _get_first_todo(self) -> Todo:
        results = await self.session.scalars(self.query)
        return results.first()

    async def _get_previous_url(self, todos: typing.List[Todo]) -> typing.Optional[str]:
        if not todos:
            return
        # for the first page, the cursor is 1, but we select items > 1,
        # so we will lose the first item, to avoid this we need to decrease the cursor by 1
        cursor_todo_id = todos[-1].id
        first_todo = await self._get_first_todo()
        if first_todo.id == cursor_todo_id:
            cursor_todo_id -= 1
        self.previous_cursor = encode_id(cursor_todo_id)
        return self._get_url(self.previous_cursor)

    async def _get_previous_page(self) -> typing.Optional[str]:
        if self.cursor is None:
            return
        else:
            last_todo_id = decode_id(self.cursor)
            previous_todos = await self._get_previous_todos(last_todo_id)
            return await self._get_previous_url(previous_todos)


async def paginate_limit_offset(query: Select, limit: int, offset: int) -> dict:
    async with db.Session() as session:
        return {
            'count': await session.scalar(select(func.count()).select_from(query.subquery())),
            'items': [todo for todo in await session.scalars(query.slice(offset, limit))]
        }


async def paginate_per_page(query: Select, page: int, per_page: int) -> dict:
    async with db.Session() as session:
        paginator = PagePaginator(session, query, page, per_page)
        return await paginator.get_response()


async def cursor_paginate(query: Select, max_results: int, cursor: typing.Optional[str]) -> dict:
    async with db.Session() as session:
        paginator = CursorPaginator(session, query, max_results, cursor)
        return await paginator.get_response()
