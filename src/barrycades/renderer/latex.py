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
        (("latexmk", "-silent", "-lualatex", "main"),),
    )
    svg = (
        "\\documentclass[dvisvgm,border=20pt]{standalone}",
        (
            ("latexmk", "-silent", "-dvilua", "main"),
            ("dvisvgm", "--no-fonts", "--output=main.svg", "main.dvi"),
        ),
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

    def document(self, tikz: str, preamble: str, options: str) -> str:
        """A standalone LaTeX document drawing the picture `tikz`."""
        return "\n".join(
            [
                self.documentclass,
                "\\usepackage{tikz}",
                "\\usetikzlibrary{fit,backgrounds,patterns}",
                preamble,
                "\\begin{document}",
                f"\\begin{{tikzpicture}}[{options}]",
                tikz,
                "\\end{tikzpicture}",
                "\\end{document}",
            ]
        )

    def build(self, tikz: str, preamble: str, options: str, path: pathlib.Path) -> None:
        """Compile `tikz` into `path`, in a scratch directory thrown away after."""
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp).resolve()
            (directory / "main.tex").write_text(self.document(tikz, preamble, options))
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
        logger.debug(f"`{' '.join(command)}` succeeded:\n{completed.stdout}")

    def collect(self, directory: pathlib.Path, path: pathlib.Path) -> None:
        """Move what the tools produced out of `directory` and into `path`."""
        product = directory / self.product
        if not product.exists():
            left = sorted(item.name for item in directory.iterdir())
            raise RenderError(
                f"LaTeX reported success but produced no `{self.product}`, "
                f"only {', '.join(left) or 'nothing'}"
            )
        shutil.move(product, path)
