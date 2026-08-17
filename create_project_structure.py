"""Create the complete initial folder structure for the FreshFlow project.

The script is idempotent: it can be executed repeatedly. Missing directories
and files are created, while existing files are preserved without changes.

Examples:
    python create_project_structure.py
    python create_project_structure.py --root C:\\FullStackProjects\\freshflow-b2b-ordering-platform
    python create_project_structure.py --dry-run
"""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_PROJECT_NAME = "freshflow-b2b-ordering-platform"


# Directories are listed explicitly so the intended architecture is easy to
# review and extend as the project grows.
DIRECTORIES: tuple[str, ...] = (
    "admin",
    "client",
    "db",
    "docs",
    "server",
    "server/app",
    "server/app/api",
    "server/app/api/v1",
    "server/app/api/v1/routes",
    "server/app/core",
    "server/app/db",
    "server/app/deps",
    "server/app/models",
    "server/app/schemas",
    "server/app/services",
    "server/migrations",
    "server/migrations/versions",
)


# Each value is written only when its file does not already exist.
FILES: dict[str, str] = {
    "README.md": """# FreshFlow B2B Ordering Platform

B2B ordering platform with a FastAPI backend, MySQL database, customer-facing
React application, and a separate administration application.

## Main directories

- `server/` - FastAPI backend
- `client/` - customer-facing React application
- `admin/` - administration React application
- `db/` - MySQL schema and seed scripts
- `docs/` - architecture and project documentation
""",
    ".gitignore": """# Python
__pycache__/
*.py[cod]
.venv/

# Environment and secrets
.env

# Node.js
node_modules/
dist/

# Editors and operating systems
.vscode/
.idea/
.DS_Store
Thumbs.db
""",
    ".env.example": """APP_NAME=FreshFlow B2B API
APP_ENV=development
DEBUG=true
API_V1_PREFIX=/api/v1
MYSQL_DATABASE=freshflow_b2b
MYSQL_USER=freshflow_app
MYSQL_PASSWORD=change_me
MYSQL_ROOT_PASSWORD=change_root_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
DATABASE_URL=mysql+pymysql://freshflow_app:change_me@localhost:3306/freshflow_b2b
""",
    "docker-compose.yml": """services:
  db:
    image: mysql:8.4
    container_name: freshflow_mysql
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    ports:
      - \"${MYSQL_PORT:-3306}:3306\"
    volumes:
      - freshflow_mysql_data:/var/lib/mysql

volumes:
  freshflow_mysql_data:
""",
    "db/schema.sql": """-- ============================================================
-- FreshFlow database schema
-- Purpose: Define the tables, relationships, indexes and constraints.
-- Run this file before db/seed.sql.
-- ============================================================

-- Add the approved CREATE TABLE statements here.
""",
    "db/seed.sql": """-- ============================================================
-- FreshFlow sample data
-- Purpose: Insert development and testing records.
-- Run db/schema.sql before this file.
-- ============================================================

-- Add the approved INSERT statements here.
""",
    "docs/erd.md": """# FreshFlow Entity Relationship Diagram

This document describes the database entities, relationships, and business
rules. Keep it synchronized with `db/schema.sql` and the SQLAlchemy models.
""",
    "server/requirements.txt": """fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
sqlalchemy>=2.0,<3.0
alembic>=1.13,<2.0
pymysql>=1.1,<2.0
pydantic-settings>=2.0,<3.0
python-dotenv>=1.0,<2.0
""",
    "server/app/__init__.py": "\"\"\"FreshFlow backend application package.\"\"\"\n",
    "server/app/main.py": """\"\"\"FastAPI application entry point.\"\"\"

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings


app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix=settings.api_v1_prefix)
""",
    "server/app/api/__init__.py": "\"\"\"HTTP API package.\"\"\"\n",
    "server/app/api/v1/__init__.py": "\"\"\"Version 1 API package.\"\"\"\n",
    "server/app/api/v1/router.py": """\"\"\"Combine all version 1 endpoint routers.\"\"\"

from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router


api_router = APIRouter()
api_router.include_router(health_router)
""",
    "server/app/api/v1/routes/__init__.py": "\"\"\"Version 1 endpoint modules.\"\"\"\n",
    "server/app/api/v1/routes/health.py": """\"\"\"Health-check endpoint.\"\"\"

from fastapi import APIRouter


router = APIRouter(tags=[\"Health\"])


@router.get(\"/health\")
def health_check() -> dict[str, str]:
    return {\"status\": \"ok\"}
""",
    "server/app/core/__init__.py": "\"\"\"Core configuration and security package.\"\"\"\n",
    "server/app/core/config.py": """\"\"\"Application settings loaded from environment variables.\"\"\"

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = \"FreshFlow B2B Ordering Platform\"
    api_v1_prefix: str = \"/api/v1\"
    database_url: str = \"mysql+pymysql://freshflow_app:change_me@localhost:3306/freshflow_b2b\"

    model_config = SettingsConfigDict(env_file=\".env\", extra=\"ignore\")


settings = Settings()
""",
    "server/app/db/__init__.py": "\"\"\"Database infrastructure package.\"\"\"\n",
    "server/app/db/base.py": """\"\"\"Shared SQLAlchemy declarative base.\"\"\"

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
""",
    "server/app/db/session.py": """\"\"\"SQLAlchemy engine and database-session factory.\"\"\"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
""",
    "server/app/deps/__init__.py": "\"\"\"Reusable FastAPI dependencies.\"\"\"\n",
    "server/app/models/__init__.py": "\"\"\"SQLAlchemy ORM models.\"\"\"\n",
    "server/app/models/enums.py": "\"\"\"Shared database enum values.\"\"\"\n",
    "server/app/models/customer.py": "\"\"\"Customer organization ORM model.\"\"\"\n",
    "server/app/models/user.py": "\"\"\"Authenticated user ORM model.\"\"\"\n",
    "server/app/models/category.py": "\"\"\"Product category ORM model.\"\"\"\n",
    "server/app/models/product.py": "\"\"\"Sellable product ORM model.\"\"\"\n",
    "server/app/models/contract.py": "\"\"\"Customer contract ORM model.\"\"\"\n",
    "server/app/models/contract_price.py": "\"\"\"Negotiated contract-price ORM model.\"\"\"\n",
    "server/app/models/order.py": "\"\"\"Order header ORM model.\"\"\"\n",
    "server/app/models/order_item.py": "\"\"\"Order line-item ORM model.\"\"\"\n",
    "server/app/schemas/__init__.py": "\"\"\"Pydantic request and response schemas.\"\"\"\n",
    "server/app/services/__init__.py": "\"\"\"Application business-logic services.\"\"\"\n",
    "server/alembic.ini": """[alembic]
script_location = %(here)s/migrations
prepend_sys_path = %(here)s
path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""",
    "server/migrations/README": "Alembic migration environment for the FreshFlow database.\n",
    "server/migrations/env.py": "\"\"\"Alembic runtime configuration.\"\"\"\n",
    "server/migrations/script.py.mako": "\"\"\"${message}\"\"\"\n",
    "client/.gitkeep": "",
    "admin/.gitkeep": "",
}


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Create missing FreshFlow project directories and files safely."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd() / DEFAULT_PROJECT_NAME,
        help=(
            "Project root directory. By default, a folder named "
            f"'{DEFAULT_PROJECT_NAME}' is created in the current directory."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned actions without changing the file system.",
    )
    return parser.parse_args()


def create_project(root: Path, dry_run: bool = False) -> tuple[int, int]:
    """Create missing project items and return (created, skipped) counts."""
    root = root.expanduser().resolve()
    created = 0
    skipped = 0

    print(f"Project root: {root}")

    for relative_directory in DIRECTORIES:
        directory = root / relative_directory
        if directory.is_dir():
            print(f"[SKIPPED] Directory exists: {relative_directory}")
            skipped += 1
        elif directory.exists():
            raise FileExistsError(
                f"Cannot create directory because a file exists at: {directory}"
            )
        else:
            print(f"[CREATE ] Directory: {relative_directory}")
            if not dry_run:
                directory.mkdir(parents=True, exist_ok=False)
            created += 1

    for relative_file, initial_content in FILES.items():
        file_path = root / relative_file
        if file_path.is_file():
            print(f"[SKIPPED] File exists: {relative_file}")
            skipped += 1
        elif file_path.exists():
            raise IsADirectoryError(
                f"Cannot create file because a directory exists at: {file_path}"
            )
        else:
            print(f"[CREATE ] File: {relative_file}")
            if not dry_run:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                # Path.write_text() supports the ``newline`` argument only in
                # newer Python versions.  Using Path.open() keeps the script
                # compatible with older Python installations as well.
                with file_path.open("w", encoding="utf-8", newline="\n") as file:
                    file.write(initial_content)
            created += 1

    print(f"\nFinished: {created} item(s) created, {skipped} item(s) skipped.")
    if dry_run:
        print("Dry run only: no changes were made.")

    return created, skipped


def main() -> None:
    """Run the project-structure generator."""
    arguments = parse_arguments()
    create_project(arguments.root, arguments.dry_run)


if __name__ == "__main__":
    main()
