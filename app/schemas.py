from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScriptBase(BaseModel):
    title: str
    body: str
    submitted_by: str
    font_face: Optional[str] = None
    font_size: Optional[str] = None


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    submitted_by: Optional[str] = None
    font_face: Optional[str] = None
    font_size: Optional[str] = None


class ScriptListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    submitted_by: str
    created_at: datetime


class ScriptDetail(ScriptListItem):
    body: str
    font_face: Optional[str] = None
    font_size: Optional[str] = None


# Queue schemas

class QueueBase(BaseModel):
    name: str


class QueueCreate(QueueBase):
    pass


class QueueUpdate(BaseModel):
    name: Optional[str] = None


class QueueItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    script_id: int
    position: int
    script: ScriptListItem


class QueueDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    scripts: list[QueueItemSchema]


class QueueListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class AddScriptToQueue(BaseModel):
    script_id: int
    position: Optional[int] = 0


class ReorderItem(BaseModel):
    script_id: int
    position: int


class StageState(BaseModel):
    active_queue_id: Optional[int] = None
    active_script_id: Optional[int] = None
    scroll_position: float = 0.0
    auto_scroll_speed: float = 3.0
    is_scrolling: bool = False


class InstanceConfigRead(BaseModel):
    instance_name: str


class InstanceConfigUpdate(BaseModel):
    instance_name: str = Field(min_length=1, max_length=64)


PEDAL_ACTIONS = {"", "toggle_scroll", "scroll_up", "scroll_down", "page_up", "page_down"}


class PedalMapping(BaseModel):
    key: str = Field(min_length=1, max_length=32)
    action: str = Field(default="")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in PEDAL_ACTIONS:
            raise ValueError(f"action must be one of: {sorted(PEDAL_ACTIONS)}")
        return v


class PedalMappingsRead(BaseModel):
    mappings: list[PedalMapping]


class PedalMappingsUpdate(BaseModel):
    mappings: list[PedalMapping]
