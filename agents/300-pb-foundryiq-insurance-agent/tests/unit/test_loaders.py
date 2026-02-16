from insurance_agent.ingest.loaders import split_text


def test_split_text_respects_chunk_size() -> None:
    text = "a" * 120
    chunks = split_text(text, chunk_size=50, chunk_overlap=10)
    assert len(chunks) == 3
    assert len(chunks[0]) == 50
    assert len(chunks[1]) == 50
    assert len(chunks[2]) == 40
