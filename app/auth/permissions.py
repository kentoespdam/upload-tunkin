"""Permission and menu lookup logic — no FastAPI dependencies."""

from abc import ABC, abstractmethod
from typing import Set

from app.core.databases import DatabaseHelper


class MenuLookup(ABC):
    """Interface for resolving menu codes accessible by a role."""

    @abstractmethod
    def menu_codes_for(self, role_id: int) -> Set[str]:
        """Return set of menu_code strings the given role can access."""
        ...


class DBMenuLookup(MenuLookup):
    """Menu lookup backed by the sys_role_menu database table."""

    def __init__(self, db_helper: DatabaseHelper):
        self._db_helper = db_helper

    def menu_codes_for(self, role_id: int) -> Set[str]:
        query = """
            SELECT sm.menu_code
            FROM sys_role_menu AS srm
            INNER JOIN sys_role AS sr ON srm.role_id = sr.role_id
            INNER JOIN sys_menu AS sm ON srm.menu_id = sm.menu_id
            WHERE sr.role_id = %s
        """
        rows = self._db_helper.fetch_data(query, (role_id,))
        if rows is None or rows.empty:
            return set()
        return set(rows["menu_code"].tolist())


class InMemoryMenuLookup(MenuLookup):
    """In-memory menu lookup for testing — seeded with a plain dict."""

    def __init__(self, data: dict[int, Set[str]]):
        self._data = data

    def menu_codes_for(self, role_id: int) -> Set[str]:
        return self._data.get(role_id, set())


class PermissionChecker:
    """Checks whether a role grants access to one or more required menu codes."""

    def __init__(self, menu_lookup: MenuLookup):
        self._menu_lookup = menu_lookup

    def allows(self, role_id: int, required_menu_codes: list[str]) -> bool:
        """Return True if the role grants ALL required menu codes.
        
        Semantics: require_role(["payrollprocess"]) means the user must have
        the "payrollprocess" menu code — at least one match.
        The old implementation used DataFrame.isin() which checks for ANY match.
        """
        if not required_menu_codes:
            return True
        granted = self._menu_lookup.menu_codes_for(role_id)
        return any(code in granted for code in required_menu_codes)