import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _default_db_path():
    """Local, non-cloud-synced home for the dev SQLite file.

    The project directory itself may live inside a OneDrive/Dropbox/Google
    Drive synced folder, and those services can lock or silently revert a
    SQLite file while it's being written to, corrupting the schema. Default
    to a per-user local data directory instead; still overridable via the
    DATABASE_URL env var for anything other than local dev.
    """
    local_appdata = os.environ.get("LOCALAPPDATA")
    data_dir = Path(local_appdata) / "NexusAthlete" if local_appdata else Path.home() / ".nexus_athlete"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "nexus.db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{_default_db_path()}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    # Without this, Jinja caches compiled templates in memory when DEBUG is
    # off, so template edits silently don't show up until the process restarts.
    TEMPLATES_AUTO_RELOAD = True
