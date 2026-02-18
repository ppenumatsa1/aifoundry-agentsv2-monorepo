from insurance_agent.config import get_settings
from insurance_agent.ingest.index import ingest_documents


def main() -> None:
    settings = get_settings()
    ingest_documents(settings)


if __name__ == "__main__":
    main()
