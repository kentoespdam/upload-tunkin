# Upload Tunkin

FastAPI-based REST API for managing payroll KPI (Key Performance Indicator) data uploads and employee information.

## Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: MySQL (via pymysql with connection pooling)
- **Authentication**: JWT (PyJWT)
- **Data Processing**: Pandas, NumPy, OpenPyXL
- **Password Hashing**: Argon2 (via pwdlib)
- **ID Encoding**: Sqids
- **Python**: 3.13+
- **Package Manager**: uv

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- MySQL server (or Docker)

## Getting Started

### 1. Clone & Setup

```bash
git clone <repo-url>
cd upload-tunkin
uv sync
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description | Default |
|---|---|---|
| `DB_HOST` | MySQL host | `localhost` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | MySQL user | `root` |
| `DB_PASS` | MySQL password | |
| `DB_NAME` | Database name | `smartoffice` |
| `KPI_TABLE_NAME` | KPI data table | `salary_kpi` |
| `JWT_SECRET_KEY` | JWT signing key | |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |
| `SQIDS_ALPHABET` | Sqids encoding alphabet | |

Full reference in [`.env.example`](.env.example).

### Run

After `uv sync`, use the CLI scripts:

```bash
uv run dev     # Development server with auto-reload (port 8000)
uv run start   # Production server (port 80)
```

Or run uvicorn directly:

```bash
uv run uvicorn app.main:app --reload --port 8000  # Development
uv run uvicorn app.main:app --host 0.0.0.0 --port 80  # Production
```

### Docker

```bash
docker-compose up --build
```

The app runs on port `8082` (mapped from container port `80`).

## API Endpoints

### Authentication (`/` prefix)

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/token` | Authenticate user, returns tokens | Client credentials |
| POST | `/refresh` | Refresh access token | Refresh token |
| GET | `/me` | Get current user info | `payrollprocess` role |
| OPTIONS | `/validate` | Validate token | — |

### Tunkin Data (`/tunkin` prefix)

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/{periode}` | Fetch paginated KPI data | JWT |
| POST | `/upload` | Upload Excel KPI data file | JWT |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |

## Architecture

```
app/
├── main.py                 # FastAPI app init, middleware, exception handlers
├── core/
│   ├── config.py           # Config, JWT settings, Sqids ID encoding
│   ├── databases.py        # DatabaseHelper with connection pooling
│   ├── cors.py             # CORS configuration
│   └── log_loader.py       # Logging setup (YAML config)
├── models/
│   ├── request_model.py    # Pydantic request models
│   └── response_model.py   # Pydantic response models + ResponseBuilder
├── routers/
│   ├── auth.py             # Authentication endpoints
│   └── tunkin.py           # Tunkin KPI data endpoints
├── repositories/
│   ├── sys_user.py         # User auth, JWT, role checking
│   ├── sys_menu.py         # Menu/permission fetching
│   └── tunkin_repository.py # Excel upload, KPI CRUD
└── services/               # Business logic layer
```

### Response Format

All endpoints return a standardized response via `ResponseBuilder`:

```json
{
  "status": 200,
  "message": "Success",
  "data": { ... },
  "errors": null,
  "timestamp": "2025-01-01T00:00:00",
  "request_id": "..."
}
```

### Authentication Flow

1. Client calls `POST /token` with username/password + client credentials
2. Server returns `access_token` (short-lived) + `refresh_token` (long-lived)
3. Protected endpoints use `Authorization: Bearer <token>` header
4. Role-based access enforced via `require_role()` dependency

## Development

### Install Dev Dependencies

```bash
uv sync --group dev
```

### Running Tests

```bash
uv run pytest
```

## Logging

Configured via `logging_config.yaml`:

- **Console**: INFO level with detailed format
- **Rotating file** (`logs/app.log`): INFO level (100MB max, 5 backups)
- **Error file** (`logs/app-error.log`): ERROR level (10MB max, 3 backups)

## Configuration

All config via environment variables or `.env` file. See [`.env.example`](.env.example).

### Key Tables

- `sys_user` — User login, role mapping
- `employee` — Employee master data
- `sys_role_menu` — Role-to-menu permissions
- `salary_kpi` (configurable) — KPI records with periode, nipam, tunkin, pph21_ter
- `sys_menu` — Menu codes for permission checks

## Security

- JWT tokens use HS256 with configurable expiry
- File uploads validated: extension, MIME type, file size, Excel structure
- Role-based access on all sensitive endpoints
- CORS configurable via environment (default open for development)
