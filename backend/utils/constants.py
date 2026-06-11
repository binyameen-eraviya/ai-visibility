import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    """Fetch a required env var, failing fast with a clear message if unset."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            f"See backend/.env.example and copy it to backend/.env."
        )
    return value


class Constants:
    # JWT Configuration (all required; the API cannot sign/verify tokens without them)
    ALGORITHM = _require("JWT_ALGORITHM")
    SECRET_KEY = _require("JWT_SECRET_KEY")
    TOKEN_EXPIRE_DAYS = _require("JWT_TOKEN_EXPIRE_DAYS")