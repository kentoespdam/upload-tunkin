"""Unit tests for SqidsHelper — encode/decode determinism.

Run: uv run python test_sqids.py
"""
from app.core.config import SqidsHelper


def test_encode_is_deterministic():
    """Same input must produce same output every time."""
    h = SqidsHelper()
    v1 = h.encode(123)
    v2 = h.encode(123)
    v3 = h.encode(123)
    assert v1 == v2 == v3, f"encode is not deterministic: {v1} vs {v2} vs {v3}"
    print("PASS: encode(123) -> same output 3 times")


def test_encode_decode_roundtrip():
    """Encode then decode must return the original integer."""
    h = SqidsHelper()
    for n in [1, 42, 123, 9999, 123456]:
        encoded = h.encode(n)
        decoded = h.decode(encoded)
        assert decoded == n, f"Round-trip failed for {n}: encoded={encoded}, decoded={decoded}"
    print("PASS: encode/decode round-trip for [1, 42, 123, 9999, 123456]")


def test_different_numbers_different_ids():
    """Different integers must produce different IDs."""
    h = SqidsHelper()
    ids = [h.encode(n) for n in range(1, 21)]
    assert len(set(ids)) == 20, "All IDs should be unique for range 1..20"
    print("PASS: 20 different numbers produce 20 unique IDs")


def test_decode_returns_original_number():
    """Decode must return the original integer, not a shifted index."""
    h = SqidsHelper()
    for n in [7, 100, 999]:
        encoded = h.encode(n)
        decoded = h.decode(encoded)
        assert decoded == n, f"Expected {n}, got {decoded}"
    print("PASS: decode returns original number for [7, 100, 999]")


def test_multiple_encodes_same_timestamp():
    """Multiple encodes at different times must be identical (no datetime noise)."""
    import time
    h = SqidsHelper()
    v1 = h.encode(555)
    time.sleep(0.01)  # Small delay
    v2 = h.encode(555)
    assert v1 == v2, f"Time-based noise detected: {v1} vs {v2}"
    print("PASS: encode(555) same before and after delay")


if __name__ == "__main__":
    tests = [
        test_encode_is_deterministic,
        test_encode_decode_roundtrip,
        test_different_numbers_different_ids,
        test_decode_returns_original_number,
        test_multiple_encodes_same_timestamp,
    ]
    for t in tests:
        t()
    print("\nAll SqidsHelper unit tests passed!")