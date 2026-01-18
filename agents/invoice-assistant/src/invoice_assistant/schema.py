from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class TopDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc_id: str = Field(..., description="Document identifier")
    file_name: str = Field(..., description="Source file name")
    snippet: str = Field(..., description="Relevant snippet")


class InvoiceAssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(..., description="Direct answer to the user question.")
    top_documents: List[TopDocument] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Top documents returned by File Search.",
    )

    @classmethod
    def json_schema(cls) -> dict:
        return cls.model_json_schema()
