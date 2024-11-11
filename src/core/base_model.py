import datetime as dt
from functools import cached_property

from pydantic import BaseModel


class Model(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            dt.date: lambda v: v.isoformat(),
            dt.datetime: lambda v: v.isoformat(),
            Exception: lambda e: str(e),
        }
        allow_mutation = True
        keep_untouched = (cached_property,)
