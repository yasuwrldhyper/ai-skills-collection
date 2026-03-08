"""Tests for calculator module (partial coverage - only add and subtract)."""

from app.calculator import add, subtract


def test_add_positive_numbers():
    assert add(2, 3) == 5


def test_add_negative_numbers():
    assert add(-1, -4) == -5


def test_add_zero():
    assert add(0, 5) == 5


def test_subtract_positive_numbers():
    assert subtract(10, 3) == 7


def test_subtract_negative_numbers():
    assert subtract(-2, -5) == 3


def test_subtract_to_zero():
    assert subtract(5, 5) == 0
