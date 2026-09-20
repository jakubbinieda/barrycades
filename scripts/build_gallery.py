#!/usr/bin/env python3
"""Generate an offline-friendly SVG gallery with certificate balance diagrams."""

import argparse
import json
import os
import re
from collections import Counter
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import quote

from barrycades import Stack
from barrycades.exceptions import BarrycadesError

ROOT = Path(__file__).resolve().parents[1]


def balance_diagram(stack: Stack) -> str:
    """Draw a row-by-block joint-count matrix using the verifier's positions."""
    first = 0 if stack.closed else 1
    blocks = (stack.width - first + stack.height - 1) // stack.height
    counts_by_row = []
    for row in range(stack.height):
        counts = Counter(
            (position - first) // stack.height
            for position in stack.partial_sums(row)
        )
        counts_by_row.append([counts[block] for block in range(blocks)])
    data = escape(json.dumps(counts_by_row, separators=(",", ":")))
    return (
        f'<div class="matrix-data" data-counts="{data}"'
        f' data-first="{first}" data-height="{stack.height}"'
        f' data-width="{stack.width}"></div>'
        '<noscript>Enable JavaScript to explore the joint-count diagram.</noscript>'
    )



def natural_key(path: Path) -> list[tuple[int, int | str]]:
    """Put height 2 before height 10, with stable ordering for other filenames."""
    return [
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"(\d+)", path.as_posix())
    ]


def relative_url(path: Path, output: Path) -> str:
    return escape(quote(Path(os.path.relpath(path, output.parent)).as_posix()))


def build_gallery(images: Path, output: Path, certificates: Path) -> int:
    images, output, certificates = (
        path.resolve() for path in (images, output, certificates)
    )
    if not images.is_dir():
        raise ValueError(f"Image folder does not exist: {images}")
    files = sorted(
        (p for p in images.rglob("*") if p.is_file() and p.suffix.lower() == ".svg"),
        key=lambda p: natural_key(p.relative_to(images)),
    )
    cards = []
    groups = set()
    for index, path in enumerate(files):
        relative = path.relative_to(images)
        group = relative.parts[0] if len(relative.parts) > 1 else "Other"
        groups.add(group)
        title = escape(path.stem.replace("_", " ").replace("-", " ").capitalize())
        match = re.fullmatch(r"(?:barrycade|corral)_(\d+)", path.stem)
        height = match.group(1) if match else ""
        url = relative_url(path, output)
        certificate = certificates / relative.with_suffix(".yaml")
        status = '<span class="badge unknown">Balance not checked</span>'
        diagram = ""
        if certificate.is_file():
            stack = Stack.from_file(certificate)
            height = str(stack.height)
            balanced = stack.balanced
            label = "✓ Balanced" if balanced else "Not balanced"
            tone = "balanced" if balanced else "unbalanced"
            status = f'<span class="badge {tone}">{label}</span>'
            breakfree = "Breakfree" if stack.breakfree else "Not breakfree"
            status += f'<span class="verification">{breakfree}</span>'
            diagram = f'''<details class="balance-details">
              <summary>Inspect balance · order {stack.order}, height {stack.height}
              </summary>
              <p>Each cell counts joints in one row and one block of
                {stack.height} consecutive positions. Balanced means every
                cell is 1. Rows run down; blocks run across.
                Green: 1 joint. Orange: 0 or multiple joints.
                {'The loop seam is included.' if stack.closed else
                 'The two ends are excluded.'}</p>
              <div class="matrix" tabindex="0"
                aria-label="Scrollable balance diagram">{balance_diagram(stack)}</div>
              <p>Status is computed from the linked certificate.</p>
            </details>'''
        certificate_link = (
            f'<a href="{relative_url(certificate, output)}">Certificate ↗</a>'
            if certificate.is_file() else ""
        )
        loading = "eager" if index == 0 else "lazy"
        cards.append(f'''<article class="construction" data-group="{escape(group)}"
            data-height="{height}">
          <div class="card-heading">
            <div><span class="category">{escape(group)}</span>
              <h2>{title}</h2></div>
            <div class="statuses">{status}</div>
            <div class="links">{certificate_link}<a href="{url}">Open SVG ↗</a></div>
          </div>
          <div class="preview"><a href="{url}" aria-label="Open {title} SVG">
            <img src="{url}" alt="{title}: brick arrangement"
              loading="{loading}" decoding="async">
          </a></div>
          <div class="card-footer">
            <span>{f'Height {height}' if height else escape(relative.as_posix())}</span>
            <label><input type="checkbox" class="zoom"> Native-size view</label>
          </div>
          {diagram}
        </article>''')
    options = "".join(
        f'<option value="{escape(group)}">{escape(group.capitalize())}</option>'
        for group in sorted(groups)
    )
    template = Path(__file__).with_name("gallery.html").read_text(encoding="utf-8")
    html = Template(template).substitute(
        count=len(files), options=options, cards="\n".join(cards),
        empty_hidden="hidden" if files else "",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, default=ROOT / "images")
    parser.add_argument("--output", type=Path, default=ROOT / "gallery.html")
    parser.add_argument("--certificates", type=Path, default=ROOT / "certificates")
    args = parser.parse_args()
    try:
        count = build_gallery(args.images, args.output, args.certificates)
    except (OSError, ValueError, BarrycadesError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Wrote {args.output} ({count} SVG images)")


if __name__ == "__main__":
    main()
