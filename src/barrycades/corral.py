"""Representation of a corral."""

from typing import ClassVar, Self

from .exceptions import UnreachableOrderError
from .stack import Stack


class Corral(Stack):
    closed: ClassVar[bool] = True

    @classmethod
    def construct(cls, height: int, order: int | None = None) -> Self:
        """The breakfree corral built in the proof of Theorem 1."""
        least = 2 * height
        if order is None:
            order = least
        if order < least:
            raise UnreachableOrderError(cls, height, least, order)

        rows: list[list[int]] = [
            list(range(least + 1, order + 1)) for _ in range(height)
        ]

        for start in range(height):
            rows[start] += [least, height]
            for step in range(1, height):
                brick = 2 * step if 2 * step < height else 2 * step + 1
                rows[(start + step) % height] += [least - brick, brick]

        return cls(
            order=order,
            height=height,
            permutations=rows,
            shifts=tuple(range(height)),
        )
