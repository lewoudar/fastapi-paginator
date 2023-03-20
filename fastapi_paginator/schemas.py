from datetime import datetime
from typing import Optional, Generic, TypeVar, List

from pydantic import BaseModel, Field, AnyHttpUrl
from pydantic.generics import GenericModel


class TodoSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    done: bool
    created_at: datetime

    class Config:
        orm_mode = True


M = TypeVar('M')


class PaginatedLimitOffsetResponse(GenericModel, Generic[M]):
    count: int = Field(description='Number of total items')
    items: List[M] = Field(description='List of items returned in a paginated response')


class PaginatedPerPageResponse(GenericModel, Generic[M]):
    count: int = Field(description='Number of total items')
    next_page: Optional[AnyHttpUrl] = Field(None, description='url of the next page if it exists')
    previous_page: Optional[AnyHttpUrl] = Field(None, description='url of the previous page if it exists')
    items: List[M] = Field(description='List of items returned in a paginated response')


class CursorPaginatedResponse(GenericModel, Generic[M]):
    count: int = Field(description='number of items returned')
    next_cursor: Optional[str] = Field(None, description='token to get items after the current page if any')
    next_page: Optional[AnyHttpUrl] = Field(None, description='url of the next page if it exists')
    previous_cursor: Optional[str] = Field(None, description='token to get items before the current page if any')
    previous_page: Optional[AnyHttpUrl] = Field(None, description='url of the previous page if it exists')
    items: List[M] = Field(description='List of items returned in a paginated response')
