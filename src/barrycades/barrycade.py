"""Representation of a barrycade."""

from typing import ClassVar, Self

from .exceptions import UnreachableOrderError
from .stack import Stack


class Barrycade(Stack):
    closed: ClassVar[bool] = False

    @classmethod
    def construct(cls, height: int, order: int | None = None) -> Self:
        """The breakfree barrycade built in the proof of Theorem 2."""
        least = 2 * height + 3
        if order is None:
            order = least
        if order < least:
            raise UnreachableOrderError(cls, height, least, order)
        if height == 1:
            return cls(order=order, height=1, permutations=[tuple(range(1, order + 1))])

        padding = list(range(least + 1, order + 1))
        rows: list[list[int]] = [[] for _ in range(height)]

        for row in range(1, height):
            rows[row] += [row]
        for row in range(height):
            rows[row] += padding

        for start in range(height):
            brick = 1
            for step in range(height):
                row = (start + step) % height
                if brick == row or least - brick == row:
                    rows[row] += [least]
                else:
                    rows[row] += [least - brick, brick]
                brick += 2
                if brick in (height, height + 3):
                    brick += 2
            rows[start] += [height]

        for row in range(height):
            rows[row] += [height + 3, least - row]

        return cls(order=order, height=height, permutations=rows)
