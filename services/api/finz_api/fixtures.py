"""The only repository reading demonstration taxonomy; never inferred SEO evidence."""

import json
from functools import lru_cache

from .config import REPO_ROOT
from .schemas import ContentCode, SourceKeyword, Topic

FIXTURE_RELATIVE_PATH = "fixtures/taxonomy_multi_topic.demo.json"


@lru_cache(maxsize=1)
def fixture_data() -> dict:
    with (REPO_ROOT / FIXTURE_RELATIVE_PATH).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("fixture_type") != "DEMO_ONLY":
        raise ValueError("Nguồn minh họa phải có nhãn DEMO_ONLY.")
    return data


def source_ref(collection: str, index: int) -> str:
    return f"{FIXTURE_RELATIVE_PATH}#/{collection}/{index}"


def demo_topics() -> list[Topic]:
    return [
        Topic(**row, source_ref=source_ref("topics", index))
        for index, row in enumerate(fixture_data()["topics"])
    ]


def demo_payload(topic_code: str) -> dict:
    topic = next((item for item in demo_topics() if item.topic_code == topic_code), None)
    if topic is None:
        raise KeyError(topic_code)
    return {
        "topic": topic.model_dump(),
        "content_codes": [
            ContentCode(**row, source_ref=source_ref("content_codes", index)).model_dump()
            for index, row in enumerate(fixture_data()["content_codes"])
            if row["topic_code"] == topic_code
        ],
        "source_keywords": [
            SourceKeyword(**row, source_ref=source_ref("source_keywords", index)).model_dump()
            for index, row in enumerate(fixture_data()["source_keywords"])
            if row["topic_code"] == topic_code
        ],
        "business_goal": None,
        "target_audience": None,
    }
