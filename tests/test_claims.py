import pytest

import stored
from barrycades.barrycade import Barrycade
from barrycades.corral import Corral
from barrycades.stack import Stack

pytestmark = pytest.mark.claims

KINDS: list[type[Stack]] = [Corral, Barrycade]
MAX_HEIGHT = 50
MAX_BALANCED_HEIGHT = 20
UNBALANCED_CORRAL_HEIGHTS = {3}
STACK_HEIGHTS = range(1, MAX_HEIGHT + 1)

CLAIMED_HEIGHTS: dict[type[Stack], range] = {
    Corral: range(1, MAX_HEIGHT + 1),
    Barrycade: range(2, MAX_HEIGHT + 1),
}

BALANCED_CORRAL_HEIGHTS = sorted(
    set(range(1, MAX_BALANCED_HEIGHT + 1)) - UNBALANCED_CORRAL_HEIGHTS
)
BALANCED_BARRYCADE_HEIGHTS = range(2, MAX_BALANCED_HEIGHT + 1)
OPTIMAL_ORDER_OFFSET: dict[type[Stack], int] = {Corral: -1, Barrycade: -2}


type Case = tuple[type[Stack], int]


def ids(cases: list[Case]) -> list[str]:
    """What pytest should call each `(kind, height)` pair."""
    return [f"{kind.__name__.lower()}-{height}" for kind, height in cases]


CLAIMED_CASES: list[Case] = [
    (kind, height) for kind in KINDS for height in CLAIMED_HEIGHTS[kind]
]
STORED_CASES: list[Case] = [
    (kind, height) for kind in KINDS for height in stored.heights(kind)
]


@pytest.mark.parametrize("height", STACK_HEIGHTS)
def test_theorem_1_builds_a_breakfree_corral_of_order_twice_the_height(
    height: int,
) -> None:
    corral = Corral.construct(height)
    assert corral.height == height
    assert corral.order == 2 * height
    assert corral.breakfree


@pytest.mark.parametrize("height", STACK_HEIGHTS)
def test_theorem_2_builds_a_breakfree_barrycade_of_order_twice_the_height_plus_three(
    height: int,
) -> None:
    barrycade = Barrycade.construct(height)
    assert barrycade.height == height
    assert barrycade.order == 2 * height + 3
    assert barrycade.breakfree


@pytest.mark.parametrize(("kind", "height"), CLAIMED_CASES, ids=ids(CLAIMED_CASES))
def test_a_solution_is_stored_for_every_height_the_paper_claims_one_for(
    kind: type[Stack], height: int
) -> None:
    assert stored.path(kind, height).exists()


@pytest.mark.parametrize(("kind", "height"), STORED_CASES, ids=ids(STORED_CASES))
def test_a_stored_solution_is_breakfree_at_the_optimal_order(
    kind: type[Stack], height: int
) -> None:
    stack = stored.load(kind, height)
    assert stack.height == height
    assert stack.order == 2 * height + OPTIMAL_ORDER_OFFSET[kind]
    assert stack.breakfree


@pytest.mark.parametrize("height", BALANCED_CORRAL_HEIGHTS)
def test_a_stored_corral_is_balanced(height: int) -> None:
    assert stored.load(Corral, height).balanced


@pytest.mark.parametrize("height", BALANCED_BARRYCADE_HEIGHTS)
def test_a_stored_barrycade_is_balanced(height: int) -> None:
    assert stored.load(Barrycade, height).balanced


@pytest.mark.parametrize("height", sorted(UNBALANCED_CORRAL_HEIGHTS))
def test_a_corral_exempt_from_balance_is_genuinely_unbalanced(height: int) -> None:
    assert not stored.load(Corral, height).balanced
