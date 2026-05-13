"""Unit tests for PermissionChecker — no FastAPI import.

Run: uv run python test_permission_checker.py
"""
from app.auth.menu_lookup import InMemoryMenuLookup
from app.auth.permission_checker import PermissionChecker


def make_checker(data: dict = None):
    return PermissionChecker(InMemoryMenuLookup(data or {}))


def test_role_with_required_code_returns_true():
    pc = make_checker({1: {"payrollprocess", "reports"}})
    assert pc.allows(1, ["payrollprocess"]) is True


def test_role_without_required_code_returns_false():
    pc = make_checker({1: {"reports", "settings"}})
    assert pc.allows(1, ["payrollprocess"]) is False


def test_role_not_registered_returns_false():
    pc = make_checker({})
    assert pc.allows(42, ["payrollprocess"]) is False


def test_any_code_matching_is_enough():
    pc = make_checker({1: {"payrollprocess", "settings"}})
    assert pc.allows(1, ["reports", "payrollprocess"]) is True


def test_none_of_codes_match_returns_false():
    pc = make_checker({1: {"payrollprocess"}})
    assert pc.allows(1, ["admin", "superadmin"]) is False


def test_empty_required_list_returns_true():
    pc = make_checker({1: {"payrollprocess"}})
    assert pc.allows(1, []) is True


def test_empty_menu_set_returns_false():
    pc = make_checker({1: set()})
    assert pc.allows(1, ["payrollprocess"]) is False


if __name__ == "__main__":
    tests = [
        test_role_with_required_code_returns_true,
        test_role_without_required_code_returns_false,
        test_role_not_registered_returns_false,
        test_any_code_matching_is_enough,
        test_none_of_codes_match_returns_false,
        test_empty_required_list_returns_true,
        test_empty_menu_set_returns_false,
    ]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print("\nAll PermissionChecker unit tests passed!")
