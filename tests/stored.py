"""The stored certificates in `certificates/`, which the paper's claims are about."""

import functools
import pathlib

from barrycades.stack import Stack

CERTIFICATES = pathlib.Path(__file__).resolve().parents[1] / "certificates"


def directory(kind: type[Stack]) -> pathlib.Path:
    """Where the certificates for `kind` are kept."""
    return CERTIFICATES / f"{kind.__name__.lower()}s"


def path(kind: type[Stack], height: int) -> pathlib.Path:
    """The path to the certificate for `kind` at `height`."""
    name = kind.__name__.lower()
    return directory(kind) / f"{name}_{height}.yaml"


def heights(kind: type[Stack]) -> list[int]:
    """Every height `kind` has a certificate for, as found on disk."""
    name = kind.__name__.lower()
    return sorted(
        int(file.stem.removeprefix(f"{name}_"))
        for file in directory(kind).glob(f"{name}_*.yaml")
    )


@functools.lru_cache
def load[C: Stack](kind: type[C], height: int) -> C:
    """Loads the certificate for `kind` at `height`."""
    return kind.from_file(path(kind, height))
