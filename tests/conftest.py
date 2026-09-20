"""Fixtures shared by the test modules."""

import gc
from collections.abc import Iterator

import pytest

from barrycades.barrycade import Barrycade
from barrycades.stack import Stack


@pytest.fixture
def breakfree_and_balanced() -> Barrycade:
    """The smallest barrycade meeting both claims."""
    return Barrycade(order=2, height=2, permutations=[[1, 2], [2, 1]])


@pytest.fixture
def breaks_in_line() -> Barrycade:
    """The smallest barrycade that is not breakfree: both rows break after one brick."""
    return Barrycade(order=2, height=2, permutations=[[1, 2], [1, 2]])


@pytest.fixture
def kinds_restored() -> Iterator[None]:
    """Undoes any `Stack` subclass the test defines."""
    before = set(Stack.types())
    yield
    gc.collect()
    assert set(Stack.types()) == before
