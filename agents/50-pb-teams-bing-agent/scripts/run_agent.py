from pathlib import Path
import sys

import uvicorn

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from teams_bing_agent.config import get_settings  # type: ignore[import-not-found]  # noqa: E402


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "teams_bing_agent.app:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
    )


if __name__ == "__main__":
    main()
