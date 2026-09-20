import pytest

from barrycades.barrycade import Barrycade
from barrycades.exceptions import UnreachableOrderError

BUILT = [
    Barrycade(
        order=7, height=2, permutations=[[6, 1, 2, 4, 3, 5, 7], [1, 4, 3, 7, 2, 5, 6]]
    ),
    Barrycade(
        order=9,
        height=3,
        permutations=[
            [8, 1, 3, 2, 7, 4, 5, 6, 9],
            [1, 4, 5, 9, 3, 2, 7, 6, 8],
            [2, 9, 4, 5, 8, 1, 3, 6, 7],
        ],
    ),
]


@pytest.mark.parametrize(
    "expected", BUILT, ids=lambda barrycade: f"height-{barrycade.height}"
)
def test_the_proof_builds_this_exact_barrycade(expected: Barrycade) -> None:
    assert Barrycade.construct(expected.height) == expected


def test_an_order_below_the_proof_is_refused() -> None:
    with pytest.raises(
        UnreachableOrderError, match="reaches order 11 at height 4, not 10"
    ):
        Barrycade.construct(4, 10)
