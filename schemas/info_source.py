from typing import List

from pydantic import BaseModel


class MarkdownInfo(BaseModel):
    content: List
    source: str
    title: str
    location: str