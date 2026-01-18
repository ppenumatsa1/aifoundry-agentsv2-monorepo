from __future__ import annotations

import json


def build_instructions(prompt_text: str, schema: dict) -> str:
    return (
        f"{prompt_text}\n\n"
        "Use the File Search tool to answer questions. "
        f"Always return your response as valid JSON matching this schema: {json.dumps(schema)}. "
        "Include answer and top_documents array with doc_id, file_name, and snippet for each document."
    )
