"""A base class for corrals and a barrycade."""

import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping
from itertools import accumulate
from pathlib import Path
from typing import Any, ClassVar, Self

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    ValidationError,
    ValidatorFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from .exceptions import InvalidStackError, UnreadableCertificateError


class Stack(BaseModel, ABC):
    """A stack of `height` rows, each a permutation of the brick widths 1..order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    closed: ClassVar[bool]  # Whether the stack closes into a loop.

    order: int
    height: int
    permutations: tuple[tuple[int, ...], ...]
    shifts: tuple[int, ...] = Field(
        default_factory=lambda data: (0,) * data.get("height", 0)
    )  # Where each row begins, defaults to zero for open stacks.

    @staticmethod
    def types() -> dict[str, type["Stack"]]:
        """Every kind there is. A kind is named by its class, lowercased."""

        found: dict[str, type[Stack]] = {}
        pending = Stack.__subclasses__()
        while pending:
            kind = pending.pop()
            pending += kind.__subclasses__()
            if not inspect.isabstract(kind):
                found[kind.__name__.lower()] = kind
        return found

    @model_validator(mode="after")
    def validate_permutations(self) -> Self:
        if self.order < 1 or self.height < 1:
            raise InvalidStackError(
                f"order {self.order} and height {self.height} must both be positive"
            )
        if len(self.permutations) != self.height:
            raise InvalidStackError(
                f"expected {self.height} permutations, got {len(self.permutations)}"
            )
        for index, perm in enumerate(self.permutations):
            if len(perm) != self.order:
                raise InvalidStackError(
                    f"permutation {index} has length {len(perm)}, expected {self.order}"
                )
            for elem in perm:
                if elem < 1 or elem > self.order:
                    raise InvalidStackError(
                        f"permutation {index} contains {elem}, outside 1..{self.order}"
                    )
            if len(set(perm)) != self.order:
                raise InvalidStackError(
                    f"permutation {index} repeats a value, "
                    f"expected {self.order} distinct"
                )
        return self

    @model_validator(mode="after")
    def validate_shifts(self) -> Self:
        if len(self.shifts) != self.height:
            raise InvalidStackError(
                f"expected {self.height} shifts, got {len(self.shifts)}"
            )
        if not self.closed and any(self.shifts):
            raise InvalidStackError(
                f"a {self.__class__.__name__.lower()} has ends and so cannot "
                f"shift its rows off them"
            )
        return self

    @model_validator(mode="wrap")
    @classmethod
    def validate_stack(cls, data: Any, handler: ValidatorFunctionWrapHandler) -> Self:
        """The stack `data` describes, read however it arrives."""
        if isinstance(data, str):
            try:
                data = yaml.safe_load(data)
            except yaml.YAMLError as error:
                raise InvalidStackError(error) from None
        types = Stack.types()
        keys = list(data) if isinstance(data, Mapping) else []
        present = sorted(set(keys) & set(types))
        settled = cls is not Stack and isinstance(data, Mapping | Stack)
        if not present and settled:
            return handler(data)
        if len(present) != 1:
            raise InvalidStackError(
                f"expected exactly one of {sorted(types)} as the top-level "
                f"key, got {sorted(keys)}"
            )
        kind = types[present[0]]
        if not issubclass(kind, cls):
            raise InvalidStackError(
                f"expected a {cls.__name__.lower()}, got a {present[0]}"
            )
        try:
            return kind.model_validate(data[present[0]])
        except ValidationError as error:
            raise InvalidStackError(error) from None

    @model_serializer(mode="wrap")
    def serialize_stack(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> Any:
        """This stack in whichever form `info.mode` asks for.

        `python` and `json` give the fields themselves, as pydantic would, and
        `yaml` is the text of its certificate."""
        if info.mode == "yaml":
            fields = handler(self)
            if not self.closed:
                del fields["shifts"]
            return yaml.safe_dump(
                data={self.__class__.__name__.lower(): fields},
                sort_keys=False,
                default_flow_style=None,
                width=10**9,
            )
        return handler(self)

    @classmethod
    def from_file(cls, path: str | Path) -> Self:
        """The stack stored in a file at `path`."""
        try:
            text = Path(path).read_text()
        except (OSError, UnicodeDecodeError) as error:
            raise UnreadableCertificateError(str(path), error) from None
        try:
            return cls.model_validate(text)
        except InvalidStackError as error:
            raise InvalidStackError(error, str(path)) from None

    @classmethod
    @abstractmethod
    def construct(  # ty: ignore[invalid-method-override]
        cls, height: int, order: int | None = None
    ) -> Self:
        """The corral or barrycade of `height` and `order` this kind builds."""

    def describe(self, balanced: bool = False) -> str:
        """A sentence naming this and the claims it does or does not meet,
        the balance claim among them only when `balanced` is set."""
        claims = [("breakfree", self.breakfree)]
        if balanced:
            claims.append(("balanced", self.balanced))
        held = (f"is {'' if holds else 'NOT '}{name}" for name, holds in claims)
        return (
            f"This {self.__class__.__name__.lower()} of order {self.order} "
            f"and height {self.height} {' and '.join(held)}."
        )

    def partial_sums(self, index: int) -> tuple[int, ...]:
        """The positions where the bricks of row `index` meet."""
        if not 0 <= index < self.height:
            raise IndexError(f"row {index} outside 0..{self.height - 1}")
        totals = accumulate(self.permutations[index], initial=self.shifts[index])
        places = (total % self.width for total in tuple(totals)[1:])
        return tuple(place for place in places if place != 0 or self.closed)

    @property
    def width(self) -> int:
        return self.order * (self.order + 1) // 2

    @property
    def balanced(self) -> bool:
        """True when each row puts one partial sum in every block of `height`."""
        first = 0 if self.closed else 1
        blocks = (self.width - first) // self.height
        return all(
            sorted((place - first) // self.height for place in self.partial_sums(index))
            == list(range(blocks))
            for index in range(self.height)
        )

    @property
    def breakfree(self) -> bool:
        """True when no partial sum occurs in more than one row."""
        seen: set[int] = set()
        for index in range(self.height):
            totals = set(self.partial_sums(index))
            if seen & totals:
                return False
            seen |= totals
        return True
