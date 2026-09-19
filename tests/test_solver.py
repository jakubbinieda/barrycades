import argparse

import pytest

from barrycades.cli import Solve
from barrycades.exceptions import SolverError
from barrycades.stack import Stack

SECONDS = 3
RESTARTS = 20

HEIGHTS = {
    "barrycade": [(h, 2 * h - 2) for h in range(2, 7)],
    "corral": [(h, 2 * h - 1) for h in range(1, 7)],
}


def args(kind: str, height: int, balanced: bool = False) -> argparse.Namespace:
    """What `Solve.configure` would have parsed, for calling `Solve.run` directly."""
    return argparse.Namespace(
        kind=kind,
        height=height,
        seconds=SECONDS,
        restarts=RESTARTS,
        balanced=balanced,
        verify=False,
    )


@pytest.mark.parametrize(
    ("kind", "height", "order"),
    [(kind, h, n) for kind, heights in HEIGHTS.items() for h, n in heights],
)
def test_the_solver_finds_a_breakfree_stack(
    kind: str, height: int, order: int, capsys: pytest.CaptureFixture[str]
) -> None:
    Solve.run(args(kind, height))
    stack = Stack.types()[kind].model_validate(capsys.readouterr().out)
    assert stack.height == height
    assert stack.order == order
    assert stack.breakfree


@pytest.mark.parametrize(
    ("kind", "height"),
    [
        (kind, h)
        for kind, heights in HEIGHTS.items()
        for h, _ in heights
        if not (kind == "corral" and h == 3)  # no balanced corral of height 3 exists
    ],
)
def test_the_solver_finds_a_balanced_stack(
    kind: str, height: int, capsys: pytest.CaptureFixture[str]
) -> None:
    Solve.run(args(kind, height, balanced=True))
    stack = Stack.types()[kind].model_validate(capsys.readouterr().out)
    assert stack.breakfree
    assert stack.balanced


def test_the_corral_that_cannot_be_balanced_is_not_searched_for() -> None:
    """No corral of height 3 and order 5 is balanced (Nakamigawa), so the search
    refuses outright instead of hunting for one."""
    with pytest.raises(SolverError) as caught:
        Solve.run(args("corral", 3, balanced=True))
    assert "failed with exit code 2" in str(caught.value)
