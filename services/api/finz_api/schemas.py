from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)


class DemoLoad(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    topic_code: str = Field(min_length=1, max_length=80)


class Topic(BaseModel):
    topic_code: str
    topic_name: str
    pillar: str
    topic_type: str
    pillar_axis: str
    main_topics: list[str]
    source_ref: str


class ContentCode(BaseModel):
    topic_code: str
    content_code: str
    content_topic: str
    original_title: str
    source_ref: str


class SourceKeyword(BaseModel):
    topic_code: str
    content_code: str
    keyword: str
    role: str
    funnel: str
    volume: None = None
    kd: None = None
    intent: None = None
    serp: None = None
    source_ref: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    status: Literal["DRAFT"]
    mode: Literal["DEMO"]
    topic: Topic | None
    content_codes: list[ContentCode]
    source_keywords: list[SourceKeyword]
    business_goal: None = None
    target_audience: None = None
    created_at: str
    updated_at: str
    snapshot_id: str
    version: int


class ProjectList(BaseModel):
    projects: list[ProjectResponse]


class TopicList(BaseModel):
    topics: list[Topic]
