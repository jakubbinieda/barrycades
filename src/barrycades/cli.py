"""The `barrycades` command line interface."""

import argparse
import inspect
import logging
import pathlib
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence

from .exceptions import (
    BarrycadesError,
    InvalidStackError,
    LatexmkNotFoundError,
    PaperBuildError,
    SolverError,
)
from .renderer.latex import Format
from .renderer.tikz import TikzRenderer
from .stack import Stack

logger = logging.getLogger(__name__)

SOLVER = "barrycades-solve"


class Command(ABC):
    """One subcommand: its arguments, and what it does with them."""

    @classmethod
    def add_to(cls, subparsers: argparse._SubParsersAction) -> None:
        """Give `subparsers` a parser for this command."""
        parser = subparsers.add_parser(cls.__name__.lower(), help=inspect.getdoc(cls))
        cls.configure(parser)
        parser.set_defaults(command=cls)

    @classmethod
    @abstractmethod
    def configure(cls, parser: argparse.ArgumentParser) -> None:
        """Declare this command's arguments."""

    @classmethod
    @abstractmethod
    def run(cls, args: argparse.Namespace) -> int:
        """Carry the command out, returning an exit status."""


class Build(Command):
    """Construct a corral as in the proof of Theorem 1, or a barrycade as in the
    proof of Theorem 2, at the least order that proof reaches or any above it"""

    @classmethod
    def configure(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("kind", choices=sorted(Stack.types()))
        parser.add_argument("height", type=int)
        parser.add_argument("order", type=int, nargs="?")
        parser.add_argument(
            "--verify", action="store_true", help="check breakfreeness once built"
        )

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        asked = f"height {args.height}"
        if args.order is not None:
            asked += f" and order {args.order}"
        kind = Stack.types()[args.kind]
        try:
            stack: Stack = kind.construct(args.height, args.order)
        except InvalidStackError as error:
            raise InvalidStackError(
                error, f"the {args.kind} the proof constructs for {asked}"
            ) from None
        print(stack.model_dump(mode="yaml"))
        if args.verify:
            print(stack.describe(), file=sys.stderr)
            if not stack.breakfree:
                return 1
        return 0


class Solve(Command):
    """Search with the C++ annealer for a stack of a given height, at the
    order that height is optimal at"""

    @classmethod
    def configure(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("kind", choices=sorted(Stack.types()))
        parser.add_argument("height", type=int)
        parser.add_argument("--seconds", type=float, help="per restart", default=60.0)
        parser.add_argument(
            "--restarts", type=int, help="before giving up", default=100
        )
        parser.add_argument(
            "--balanced", action="store_true", help="search for a balanced one"
        )
        parser.add_argument(
            "--verify", action="store_true", help="check the result once found"
        )

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        solver = pathlib.Path(sys.executable).parent / SOLVER
        command = [
            str(solver),
            args.kind,
            str(args.height),
            str(args.seconds),
            str(args.restarts),
        ]
        if args.balanced:
            command.append("--balanced")

        logger.debug(f"Running `{' '.join(command)}`")
        completed: subprocess.CompletedProcess[str] = subprocess.run(
            command, stdout=subprocess.PIPE, text=True
        )
        if completed.returncode == 1:
            raise SolverError(
                f"the solver found no {args.kind} of height {args.height}"
            )
        if completed.returncode != 0:
            raise SolverError(
                f"`{' '.join(command)}` failed with exit code {completed.returncode}"
            )

        output: str = completed.stdout
        print(output)
        if args.verify:
            stack = Stack.types()[args.kind].model_validate(output)
            print(stack.describe(args.balanced), file=sys.stderr)
            if not stack.breakfree or (args.balanced and not stack.balanced):
                return 3
        return 0


class Render(Command):
    """Draw a stored stack: `tex` is the TikZ body alone, `pdf` and `svg` are
    that compiled into a standalone document"""

    @classmethod
    def configure(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("path")
        parser.add_argument("output")
        modes = ("tex", *Format.__members__)
        parser.add_argument("--mode", choices=modes, default="tex")

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        renderer = TikzRenderer.for_stack(Stack.from_file(args.path))
        path = pathlib.Path(args.output).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        if args.mode == "tex":
            path.write_text(renderer.render() + "\n")
        else:
            Format[args.mode].build(
                renderer.render(),
                renderer.palette.preamble(),
                renderer.options(),
                path,
            )
        return 0


class Paper(Command):
    """Compile the paper in `paper/` into `paper/main.pdf`"""

    @classmethod
    def configure(cls, parser: argparse.ArgumentParser) -> None:
        pass

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        directory = pathlib.Path(__file__).resolve().parents[2] / "paper"
        if shutil.which("latexmk") is None:
            raise LatexmkNotFoundError
        completed = subprocess.run(
            ["make"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if completed.returncode != 0:
            raise PaperBuildError(completed.returncode, completed.stdout)
        print(directory / "main.pdf")
        return 0


class Verify(Command):
    """Check whether a stored stack is breakfree; with --balanced it is
    checked on balance as well and has to be both to pass"""

    @classmethod
    def configure(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("path")
        parser.add_argument("--balanced", action="store_true")

    @classmethod
    def run(cls, args: argparse.Namespace) -> int:
        stack = Stack.from_file(args.path)
        print(stack.describe(args.balanced))
        holds = stack.breakfree and (not args.balanced or stack.balanced)
        return 0 if holds else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand, defaulting to the arguments the process was given."""
    parser = argparse.ArgumentParser(prog="barrycades")
    parser.add_argument("--debug", action="store_true")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    for command in [Build, Solve, Render, Verify, Paper]:
        command.add_to(subparsers)

    args = parser.parse_args(argv)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

    try:
        return args.command.run(args)
    except BarrycadesError as error:
        print(error.report(), file=sys.stderr)

    return 1
