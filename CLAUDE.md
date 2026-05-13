# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Upload Tunkin** is a FastAPI-based REST API for managing payroll KPI (Key Performance Indicator) data uploads and employee information. The system handles Excel file uploads, user authentication via JWT, role-based access control, and integrates with a MySQL database.

## Tech Stack

- **Framework**: FastAPI 0.121.2+
- **Server**: Uvicorn
- **Database**: MySQL (via pymysql with connection pooling)
- **Authentication**: JWT (PyJWT)
- **Data Processing**: Pandas, NumPy, OpenPyXL
- **Password Hashing**: Argon2 (via pwdlib)
- **ID Encoding**: Sqids
- **Python**: 3.13+
- **Package Manager**: uv

## Development Commands

### Setup & Installation
```bash
uv sync                    # Install dependencies
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running the Application
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 80    # Production
uv run uvicorn app.main:app --reload --port 8000         # Development with auto-reload
```

### Docker
```bash
docker-compose up --build    # Build and run with Docker
```

The app runs on port 8082 (mapped from container port 80) when using docker-compose.

## Architecture

### Directory Structure
```
app/
├── main.py                 # FastAPI app initialization, middleware, exception handlers
├── core/
│   ├── config.py          # Configuration, JWT settings, SqidsHelper for ID encoding
│   ├── databases.py       # DatabaseHelper with connection pooling, query execution
│   └── log_loader.py      # Logging setup from YAML config
├── models/
│   ├── request_model.py   # Pydantic request models (PaginationQuery, TunkinRequest)
│   └── response_model.py  # Pydantic response models, ResponseBuilder for consistent API responses
├── routers/
│   ├── auth.py            # Authentication endpoints (/token, /refresh, /me, /validate)
│   └── tunkin.py          # Tunkin data endpoints (GET /{periode}, POST /upload)
└── repositories/
    ├── sys_user.py        # User authentication, JWT token creation/validation, role checking
    ├── sys_menu.py        # Menu/permission fetching by role
    └── tunkin_repository.py # Excel upload processing, KPI data fetching
```

### Key Architectural Patterns

**Response Standardization**: All endpoints return responses via `ResponseBuilder`, which wraps data in a consistent format with status, message, errors, timestamp, and request_id.

**Database Layer**: `DatabaseHelper` abstracts all database operations with connection pooling. Methods include:
- `fetch_data()` - returns pandas DataFrame
- `fetchone()` - returns single dict
- `fetch_page()` - returns paginated results with metadata
- `save_update()` / `save_update_single()` - INSERT/UPDATE operations

**Authentication Flow**:
1. Client calls `/token` with username/password and client credentials
2. `TokenHelper.create_access_token()` generates JWT with user data and role
3. Protected endpoints use `require_role()` dependency to check permissions
4. Role validation queries `sys_role_menu` to verify user has required menu code

**ID Encoding**: `SqidsHelper` encodes numeric IDs to obfuscated strings using Sqids. Used in pagination results to encode database IDs.

### Configuration

Environment variables (`.env`):
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME` - MySQL connection
- `KPI_TABLE_NAME` - Table for salary KPI data (default: `salary_kpi`)
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - JWT settings
- `JWT_CLIENT_ID`, `JWT_CLIENT_SECRET` - Client credentials for token endpoint
- `SQIDS_ALPHABET`, `SQIDS_MIN_LENGTH` - Sqids encoding configuration
- `POOL_SIZE`, `MAX_POOL_SIZE` - Database connection pool settings

## API Endpoints

### Authentication (`/` prefix)
- `POST /token` - Authenticate user, returns access_token + refresh_token
- `POST /refresh` - Refresh access token using refresh_token
- `GET /me` - Get current user info (requires `payrollprocess` role)
- `OPTIONS /validate` - Validate token without authentication

### Tunkin Data (`/tunkin` prefix)
- `GET /{periode}` - Fetch paginated KPI data for a period (query: `page`, `size`, `nipam`)
- `POST /upload` - Upload Excel file with KPI data

## Common Development Tasks

### Adding a New Endpoint
1. Create route in `app/routers/` with `@router.get/post/etc()`
2. Use `Depends(require_role([...]))` for role-based access
3. Return via `ResponseBuilder` (e.g., `response_builder.ok(data=...)`)
4. Add exception handling for HTTPException and general exceptions

### Modifying Database Queries
- Edit query in repository class (e.g., `TunkinRepository.fetch_page_data()`)
- Use parameterized queries with `%s` placeholders and pass params tuple
- Call appropriate `DatabaseHelper` method: `fetch_data()`, `fetchone()`, `fetch_page()`, or `save_update()`

### Handling File Uploads
- See `TunkinRepository.upload()` for validation pattern
- Validates: file extension, file size, content type, Excel structure
- Processes via pandas, validates columns, then bulk inserts via `save_update()`

### Adding New Roles/Permissions
- Create menu entry in `sys_menu` table with `menu_code`
- Add role-menu mapping in `sys_role_menu`
- Use `require_role(["menu_code"])` in endpoint

## Logging

Configured via `logging_config.yaml`:
- **Console**: INFO level with detailed format
- **File** (`logs/app.log`): INFO level, rotating (100MB max, 5 backups)
- **Error File** (`logs/app-error.log`): ERROR level, rotating (10MB max, 3 backups)

Access logger: `from app.core.config import LOGGER`

## Database Schema Notes

Key tables referenced:
- `sys_user` - User login, role_id, employee reference
- `employee` - Employee master data
- `emp_profile` - Employee name, email
- `position` - Job title, organization reference
- `organization` - Org hierarchy
- `sys_reference` - Lookup values (e.g., emp_flag)
- `sys_role_menu` - Role-to-menu permissions
- `salary_kpi` (configurable) - KPI data with periode, nipam, nominal

## Security Considerations

- JWT tokens use HS256 with a secret key from environment
- Passwords validated via MySQL `PASSWORD()` function (legacy; consider bcrypt/argon2 for new systems)
- CORS is open (`allow_origins=['*']`) — restrict in production
- File uploads validated for extension, size, and content type
- Role-based access control enforced via `require_role()` dependency
- Client credentials required for `/token` endpoint

## Testing Notes

No test framework currently configured. To add tests:
- Use `pytest` with `pytest-asyncio` for async endpoint testing
- Mock `DatabaseHelper` or use test database
- Test file upload validation in `TunkinRepository`
- Test JWT token creation/validation in `TokenHelper`


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
