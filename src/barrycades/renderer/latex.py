import logging
import pathlib
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from enum import Enum

from ..exceptions import RenderError

logger = logging.getLogger(__name__)


class Format(Enum):
    """How to turn a TikZ picture into one particular output format."""

    pdf = (
        "\\documentclass[border=20pt]{standalone}",
        (("latexmk", "-silent", "-pdflatex", "main"),),
    )
    svg = (
        "\\documentclass[dvisvgm]{minimal}",
        (("latexmk", "-silent", "-dvi", "main"), ("dvisvgm", "main")),
    )

    documentclass: str
    commands: tuple[tuple[str, ...], ...]

    def __init__(
        self, documentclass: str, commands: tuple[tuple[str, ...], ...]
    ) -> None:
        self.documentclass = documentclass
        self.commands = commands

    @property
    def product(self) -> str:
        """What the commands leave behind in the scratch directory."""
        return f"main.{self.name}"

    def document(self, tikz: str, preamble: str) -> str:
        """A standalone LaTeX document drawing the picture `tikz`."""
        return "\n".join(
            [
                self.documentclass,
                "\\usepackage{tikz}",
                "\\usetikzlibrary{fit,backgrounds,patterns}",
                preamble,
                "\\begin{document}",
                "\\begin{tikzpicture}",
                tikz,
                "\\end{tikzpicture}",
                "\\end{document}",
            ]
        )

    def build(self, tikz: str, preamble: str, path: pathlib.Path) -> None:
        """Compile `tikz` into `path`, in a scratch directory thrown away after."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp).resolve()
            (directory / "main.tex").write_text(self.document(tikz, preamble))
            for command in self.commands:
                self.run(command, directory)
            self.collect(directory, path)
        logger.debug(f"Successfully created `{path}`")

    def run(self, command: Sequence[str], cwd: pathlib.Path) -> None:
        """Run `command` in `cwd`, raising if it fails."""
        executable = command[0]
        if shutil.which(executable) is None:
            raise RenderError(
                f"`{executable}` was not found on PATH, "
                f"it is required to render LaTeX output"
            )
        completed = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if completed.returncode != 0:
            raise RenderError(
                f"`{' '.join(command)}` failed with exit code "
                f"{completed.returncode}:\n{completed.stdout}"
            )
        logger.debug(f"`{' '.join(command)}` succeeded")

    def collect(self, directory: pathlib.Path, path: pathlib.Path) -> None:
        """Move what the tools produced out of `directory` and into `path`."""
        product = directory / self.product
        if not product.exists():
            raise RenderError(
                f"LaTeX reported success but produced no `{self.product}`"
            )
        shutil.move(product, path)
