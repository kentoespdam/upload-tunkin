"""Repositories package — legacy shim (kept for now for backward compat).

All repositories have moved to their respective domain modules:
- app/tunkin/repository.py (TunkinRepository, KPIRepository)
- app/auth/repository.py (SysUserRepository, SysMenuRepository)
"""

# Legacy re-exports
from app.tunkin.repository import TunkinRepository, get_tunkin_repository, KPIRepository, get_kpi_repository

__all__ = [
    "TunkinRepository",
    "get_tunkin_repository",
    "KPIRepository",
    "get_kpi_repository",
]
