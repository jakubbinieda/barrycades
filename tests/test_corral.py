import pytest

from barrycades.corral import Corral
from barrycades.exceptions import UnreachableOrderError

BUILT = [
    Corral(order=4, height=2, permutations=[[4, 2, 1, 3], [1, 3, 4, 2]], shifts=[0, 1]),
    Corral(
        order=6,
        height=3,
        permutations=[[6, 3, 1, 5, 4, 2], [4, 2, 6, 3, 1, 5], [1, 5, 4, 2, 6, 3]],
        shifts=[0, 1, 2],
    ),
]


@pytest.mark.parametrize(
    "expected", BUILT, ids=lambda corral: f"height-{corral.height}"
)
def test_the_proof_builds_this_exact_corral(expected: Corral) -> None:
    assert Corral.construct(expected.height) == expected


def test_an_order_below_the_proof_is_refused() -> None:
    with pytest.raises(
        UnreachableOrderError, match="reaches order 8 at height 4, not 7"
    ):
        Corral.construct(4, 7)
