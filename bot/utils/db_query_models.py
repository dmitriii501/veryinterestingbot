from typing import List, Optional, Union, Literal, Any
from pydantic import BaseModel, Field, field_validator

FilterOperator = Literal[
    'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'like', 'ilike', 'is', 'in', 'cs', 'cd'
]

class FilterCondition(BaseModel):
    column: str
    operator: FilterOperator
    value: Any

class OrderByCondition(BaseModel):
    column: str
    direction: Literal['asc', 'desc'] = 'asc'

class DatabaseQuery(BaseModel):
    table: str
    select_columns: Union[str, List[str]] = Field(default="*")
    filters: Optional[List[FilterCondition]] = None
    order_by: Optional[OrderByCondition] = None
    limit: Optional[int] = Field(default=None, gt=0)

    @field_validator('select_columns')
    @classmethod
    def format_select_columns(cls, v: Union[str, List[str]]) -> str:
        if isinstance(v, list):
            return ", ".join(v)
        return v

    @field_validator('order_by', mode='before')
    @classmethod
    def format_order_by(cls, v: Optional[Dict]) -> Optional[Tuple[str, str]]:
        if v and isinstance(v, dict) and 'column' in v:
            return (v['column'], v.get('direction', 'asc'))
        return None