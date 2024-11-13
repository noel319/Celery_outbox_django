import datetime as dt
from functools import cached_property
from datetime import datetime
from typing import Any
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

class Event(BaseModel):
    event_type: str
    event_date_time: datetime
    environment:str
    event_context:dict[str, Any]
    metadata_version:int = 1
