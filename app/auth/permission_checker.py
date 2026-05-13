"""PermissionChecker — pure authorization logic, no FastAPI."""
from typing import Set, List

from app.auth.menu_lookup import MenuLookup


class PermissionChecker:
    """Checks whether a role grants access to one or more required menu codes."""

    def __init__(self, menu_lookup: MenuLookup):
        self._menu_lookup = menu_lookup

    def allows(self, role_id: int, required_menu_codes: List[str]) -> bool:
        """Return True if the role grants ALL required menu codes.
        
        Semantics: require_role(["payrollprocess"]) means the user must have
        the "payrollprocess" menu code — at least one match.
        The old implementation used DataFrame.isin() which checks for ANY match.
        """
        if not required_menu_codes:
            return True
        granted = self._menu_lookup.menu_codes_for(role_id)
        return any(code in granted for code in required_menu_codes)