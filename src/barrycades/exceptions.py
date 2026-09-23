"""Exception types raised by this package."""

import yaml
from pydantic import ValidationError

type Cause = str | ValidationError | yaml.YAMLError | InvalidStackError


class BarrycadesError(Exception):
    """Base class for every error raised by barrycades."""

    def report(self) -> str:
        """This failure as the command line should show it."""
        return f"error: {self}"


class InvalidStackError(BarrycadesError):
    """A stack violates one of its structural invariants."""

    def __init__(self, cause: Cause, source: str | None = None) -> None:
        self.source = source
        self.invariants: tuple[tuple[str, str], ...] = self._unwrap(cause)
        super().__init__("; ".join(message for _, message in self.invariants))

    @staticmethod
    def _unwrap(cause: Cause) -> tuple[tuple[str, str], ...]:
        """The plain `(location, message)` pairs behind `cause`."""
        if isinstance(cause, InvalidStackError):
            return cause.invariants
        if isinstance(cause, ValidationError):
            return tuple(
                (".".join(str(part) for part in detail["loc"]), detail["msg"])
                for detail in cause.errors()
            )
        if isinstance(cause, yaml.YAMLError):
            problem = getattr(cause, "problem", None) or "could not be parsed"
            place = ""
            if mark := getattr(cause, "problem_mark", None):
                place = f" at line {mark.line + 1}, column {mark.column + 1}"
            return (("", f"not valid YAML: {problem}{place}"),)
        return (("", cause),)

    def report(self) -> str:
        """Every invariant broken, against the stack `source` names."""
        if self.source is None:
            return super().report()
        return "\n".join(
            [f"{self.source} is not valid:"]
            + [
                f"  {location}: {message}" if location else f"  {message}"
                for location, message in self.invariants
            ]
        )


class UnreadableCertificateError(BarrycadesError):
    """A certificate could not be read from the path it was asked for."""

    def __init__(self, path: str, cause: OSError | UnicodeDecodeError) -> None:
        self.path = path
        detail = getattr(cause, "strerror", None) or "cannot be decoded as text"
        super().__init__(f"{path} cannot be read: {detail}")


class UnreachableOrderError(BarrycadesError):
    """A stack was asked for an order below the one its proof reaches."""

    def __init__(self, kind: type, height: int, least: int, order: int) -> None:
        super().__init__(
            f"the {kind.__name__.lower()} stack reaches order "
            f"{least} at height {height}, not {order}"
        )


class RenderError(BarrycadesError):
    """Turning a stack into TikZ source, a PDF or an SVG failed."""


class LatexmkNotFoundError(BarrycadesError):
    """`latexmk` is not on PATH, so the paper cannot be compiled."""

    def __init__(self) -> None:
        super().__init__(
            "`latexmk` was not found on PATH, it is required to compile the paper"
        )


class PaperBuildError(BarrycadesError):
    """`make` ran in `paper/` but did not produce the paper."""

    def __init__(self, returncode: int, output: str) -> None:
        self.returncode = returncode
        super().__init__(
            f"compiling the paper failed with exit code {returncode}:\n{output}"
        )


class SolverError(BarrycadesError):
    """The C++ solver could not be run, or ran without finding a stack."""
