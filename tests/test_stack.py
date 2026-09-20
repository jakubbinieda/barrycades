import pathlib
from itertools import accumulate
from typing import Any

import pytest

from barrycades.barrycade import Barrycade
from barrycades.corral import Corral
from barrycades.exceptions import InvalidStackError, UnreadableCertificateError
from barrycades.stack import Stack

INVALID = [
    (
        {"order": 6, "height": 3, "permutations": [[1, 2, 3, 4, 5, 6]]},
        "expected 3 permutations, got 1",
    ),
    (
        {"order": 6, "height": 1, "permutations": [[1, 2, 3]]},
        "permutation 0 has length 3, expected 6",
    ),
    (
        {"order": 3, "height": 1, "permutations": [[1, 2, 9]]},
        "permutation 0 contains 9, outside 1..3",
    ),
    (
        {"order": 3, "height": 1, "permutations": [[0, 1, 2]]},
        "permutation 0 contains 0, outside 1..3",
    ),
    (
        {"order": 3, "height": 1, "permutations": [[1, 2, 2]]},
        "permutation 0 repeats a value, expected 3 distinct",
    ),
    (
        {"order": 0, "height": 1, "permutations": [[]]},
        "order 0 and height 1 must both be positive",
    ),
    (
        {"order": 3, "height": 0, "permutations": []},
        "order 3 and height 0 must both be positive",
    ),
]


@pytest.mark.parametrize(("fields", "expected"), INVALID)
def test_a_broken_invariant_is_reported_without_a_pydantic_wrapper(
    fields: dict[str, Any], expected: str
) -> None:
    with pytest.raises(InvalidStackError) as caught:
        Barrycade(**fields)
    assert str(caught.value) == expected


def test_shift_count_must_match_height() -> None:
    with pytest.raises(InvalidStackError) as caught:
        Corral(order=2, height=1, permutations=[[1, 2]], shifts=[0, 1])
    assert str(caught.value) == "expected 1 shifts, got 2"


def test_a_key_the_kind_has_no_use_for_is_refused_rather_than_dropped() -> None:
    with pytest.raises(InvalidStackError, match="Extra inputs are not permitted"):
        Stack.model_validate(
            "barrycade:\n"
            "  order: 2\n"
            "  height: 2\n"
            "  permutations: [[1, 2], [2, 1]]\n"
            "  widths: [1, 2]\n"
        )


def test_a_stack_with_ends_cannot_shift_its_rows_off_them() -> None:
    with pytest.raises(InvalidStackError, match="cannot shift its rows"):
        Stack.model_validate(
            "barrycade:\n"
            "  order: 2\n"
            "  height: 2\n"
            "  permutations: [[1, 2], [2, 1]]\n"
            "  shifts: [0, 1]\n"
        )


@pytest.mark.usefixtures("kinds_restored")
def test_a_kind_that_does_not_say_whether_it_closes_is_unusable() -> None:
    class Fence(Stack):
        @classmethod
        def construct(cls, height: int, order: int | None = None) -> "Fence":
            raise NotImplementedError

    with pytest.raises(AttributeError, match="no attribute 'closed'"):
        Fence(order=2, height=1, permutations=[[1, 2]])


def test_stack_itself_is_abstract() -> None:
    with pytest.raises(TypeError, match="abstract"):
        Stack(order=2, height=1, permutations=[[1, 2]])


@pytest.mark.parametrize(
    "text", ["{}", "null", "[]", "stack: {}", "corral: {}\nbarrycade: {}"]
)
def test_a_certificate_without_exactly_one_known_kind_is_rejected(text: str) -> None:
    with pytest.raises(InvalidStackError, match="top-level key"):
        Stack.model_validate(text)


@pytest.mark.parametrize("kind", [Corral, Barrycade])
@pytest.mark.parametrize("text", ["null", "[]", "not a certificate at all"])
def test_a_kind_asked_for_by_name_still_reports_text_naming_no_kind(
    kind: type[Stack], text: str
) -> None:
    with pytest.raises(InvalidStackError, match="top-level key"):
        kind.model_validate(text)


@pytest.mark.parametrize(
    ("text", "place"),
    [
        ("corral: [1, 2\n", "line 2, column 1"),
        ("a:\n- b\n  c: d\n", "line 3, column 4"),
    ],
)
def test_text_that_never_parses_is_rejected_naming_where_it_broke(
    text: str, place: str
) -> None:
    with pytest.raises(InvalidStackError) as caught:
        Stack.model_validate(text)
    assert str(caught.value).startswith("not valid YAML: ")
    assert str(caught.value).endswith(place)


@pytest.mark.parametrize("height", [2, 3, 5, 10])
@pytest.mark.parametrize("kind", [Corral, Barrycade])
def test_a_stack_written_out_and_read_back_is_the_same_one(
    kind: type[Stack], height: int
) -> None:
    stack = kind.construct(height)
    written = stack.model_dump(mode="yaml")
    assert Stack.model_validate(written) == stack


def test_types_names_every_kind_there_is() -> None:
    assert Stack.types() == {"corral": Corral, "barrycade": Barrycade}


@pytest.mark.parametrize("kind", [Corral, Barrycade])
def test_dumping_to_python_or_json_gives_the_fields(kind: type[Stack]) -> None:
    stack = kind.construct(3)
    assert stack.model_dump() == {
        "order": stack.order,
        "height": stack.height,
        "permutations": stack.permutations,
        "shifts": stack.shifts,
    }
    assert stack.model_dump(mode="json") == {
        "order": stack.order,
        "height": stack.height,
        "permutations": [list(row) for row in stack.permutations],
        "shifts": list(stack.shifts),
    }


def test_only_the_certificate_leaves_out_an_open_kinds_shifts() -> None:
    barrycade = Barrycade.construct(3)
    assert "shifts" not in barrycade.model_dump(mode="yaml")
    assert "shifts" in barrycade.model_dump()
    assert "shifts" in barrycade.model_dump(mode="json")


@pytest.mark.parametrize("kind", [Corral, Barrycade])
def test_a_row_is_kept_to_one_line_however_wide(kind: type[Stack]) -> None:
    stack = kind.construct(10)
    lines = stack.model_dump(mode="yaml").splitlines()
    header = 4  # kind, order, height, "permutations:"
    assert len(lines) == header + stack.height + stack.closed


def test_from_file_reads_a_file(tmp_path: pathlib.Path) -> None:
    stack = Corral.construct(4)
    path = tmp_path / "corral.yaml"
    path.write_text(stack.model_dump(mode="yaml"))
    assert Stack.from_file(path) == stack


def test_a_kind_reads_only_itself(tmp_path: pathlib.Path) -> None:
    corral = Corral.construct(4)
    path = tmp_path / "stack.yaml"
    path.write_text(corral.model_dump(mode="yaml"))
    assert Corral.from_file(path) == corral

    path.write_text(Barrycade.construct(4).model_dump(mode="yaml"))
    with pytest.raises(InvalidStackError, match="expected a corral, got a barrycade"):
        Corral.from_file(path)


def test_a_certificate_that_cannot_be_read_names_the_path(
    tmp_path: pathlib.Path,
) -> None:
    with pytest.raises(
        UnreadableCertificateError, match=r"gone\.yaml cannot be read: No such file"
    ):
        Stack.from_file(tmp_path / "gone.yaml")


@pytest.mark.parametrize(
    ("permutations", "expected"),
    [
        ([[1, 2], [2, 1]], "is breakfree and is balanced."),
        ([[1, 2], [1, 2]], "is NOT breakfree and is balanced."),
    ],
)
def test_describe_gives_each_claim_its_own_verb(
    permutations: list[list[int]], expected: str
) -> None:
    assert (
        Barrycade(order=2, height=2, permutations=permutations)
        .describe(balanced=True)
        .endswith(expected)
    )


def test_describe_leaves_out_balance_unless_it_is_asked_for() -> None:
    assert (
        Barrycade(order=2, height=2, permutations=[[1, 2], [2, 1]])
        .describe()
        .endswith("is breakfree.")
    )


def test_breakfree_rejects_a_shared_sum(breaks_in_line: Barrycade) -> None:
    assert not breaks_in_line.breakfree


def test_breakfree_accepts_staggered_sums(breakfree_and_balanced: Barrycade) -> None:
    assert breakfree_and_balanced.breakfree


@pytest.mark.parametrize(("kind", "spare"), [(Corral, 0), (Barrycade, 1)])
def test_only_an_open_end_is_not_a_sum(kind: type[Stack], spare: int) -> None:
    stack = kind.construct(4)
    for index in range(stack.height):
        assert len(stack.partial_sums(index)) == stack.order - spare


def test_a_closed_stack_wraps_its_sums() -> None:
    corral = Corral(
        order=6,
        height=3,
        permutations=[[5, 1, 3, 6, 2, 4], [2, 4, 5, 1, 3, 6], [6, 2, 4, 5, 1, 3]],
        shifts=[0, 1, 2],
    )
    assert corral.partial_sums(0) == (5, 6, 9, 15, 17, 0)
    assert corral.partial_sums(1) == (3, 7, 12, 13, 16, 1)
    assert corral.partial_sums(2) == (8, 10, 14, 19, 20, 2)
    assert corral.breakfree
    assert set(range(corral.width)) - {
        total for index in range(corral.height) for total in corral.partial_sums(index)
    } == {4, 11, 18}


def test_a_closed_stack_counts_the_seam() -> None:
    corral = Corral(order=2, height=2, permutations=[[1, 2], [2, 1]], shifts=[0, 0])
    assert corral.partial_sums(0) == (1, 0)
    assert corral.partial_sums(1) == (2, 0)
    assert not corral.breakfree


def test_balanced_rejects_two_sums_in_one_block() -> None:
    barrycade = Barrycade(
        order=4,
        height=3,
        permutations=[[1, 3, 2, 4], [2, 3, 4, 1], [3, 4, 1, 2]],
    )
    assert barrycade.partial_sums(0) == (1, 4, 6)
    assert barrycade.breakfree
    assert not barrycade.balanced


def test_balanced_accepts_spread_sums(breakfree_and_balanced: Barrycade) -> None:
    assert breakfree_and_balanced.balanced


def test_balanced_rejects_a_row_whose_blocks_are_distinct_but_incomplete() -> None:
    stack = Barrycade.construct(2)
    blocks = [(total - 1) // stack.height for total in stack.partial_sums(0)]
    assert len(set(blocks)) == len(blocks)
    assert not stack.balanced


@pytest.mark.parametrize(
    ("permutations", "balanced"),
    [([[3, 1, 2], [1, 3, 2]], True), ([[1, 2, 3], [1, 3, 2]], False)],
)
def test_a_closed_stack_counts_its_blocks_from_zero_not_one(
    permutations: list[list[int]], balanced: bool
) -> None:
    corral = Corral(order=3, height=2, permutations=permutations, shifts=[0, 1])
    assert corral.balanced is balanced


def test_an_unshifted_open_row_puts_its_only_zero_at_the_end_it_finishes_on() -> None:
    barrycade = Barrycade.construct(5)
    assert not any(barrycade.shifts)
    for index in range(barrycade.height):
        totals = list(accumulate(barrycade.permutations[index]))
        assert totals[-1] == barrycade.width
        assert 0 not in totals[:-1]
        assert barrycade.partial_sums(index) == tuple(totals[:-1])


@pytest.mark.parametrize("index", [-1, 3])
@pytest.mark.parametrize("kind", [Corral, Barrycade])
def test_row_index_must_be_in_range(kind: type[Stack], index: int) -> None:
    with pytest.raises(IndexError, match=r"outside 0\.\.2"):
        kind.construct(3).partial_sums(index)
