# How to Construct High Barrycades

This repository is an artifact of the *How to Construct High Barrycades* article (available soon).

The paper proves that constructions of certain kind exist and can be built; this repository lets you build them, check them, and draw them.

## What are corrals and barrycades?

A **stack** of order *n* and height *h* is a stack of *h* rows. Every row is a permutation of bricks with widths `[1,n]`.

A place where two bricks in a row meet is a **joint**.

We divide stacks into two classes, which differ in where a row ends:

- a **corral** closes into a loop, so positions wrap around the width and the seam where a row meets itself is a joint like any other. Each row also has a **shift** saying how far around the loop it starts.
- a **barrycade** has two ends. Those ends are not joints, because nothing can break against them.

A stack can have two properties

- it is **breakfree** when no two rows have a joint in the same position
- it is **balanced** when every row puts exactly one joint in each block, the blocks being *h* consecutive positions each. This only means something at the **optimal** order where the joints fill every position exactly once.

## Installation

The project is managed with [uv](https://docs.astral.sh/uv/) and needs Python
3.12 or later, and a C++17 compiler for the solver.

To build it, you need to run:
```sh
uv sync
```

## Usage 

The best way to get started is running:
```sh
uv run barrycades --help
```

Each of the constructing commands prints the result to stdout and everything else to stderr, so storing the output requires only a redirection to a file, i.e. `> output.yaml`

Furthermore, `build` and `solve` can be run with the `--verify` flag to check if the result matches the constraints.

### Build
Build a barrycade or a corral of the given height according to the construction given in the paper. You can additionally pass a specific order rather than the minimal one that the construction defaults to.

```sh
uv run barrycades build corral 4 # height 4, order 8
uv run barrycades build barrycade 6 # height 6, order 15
uv run barrycades build barrycade 4 12 # height 4, order 12
```

### Solve
Run a simulated annealing algorithm to find breakfree corrals or barrycades of a given height and the **optimal** order. You can also pass the `--balanced` flag to look for balanced solutions. Additionally, you can also pass `--seconds` and `--restarts` flags to specify how much time it can spend on a single run and how many runs to perform.

```sh
uv run barrycades solve barrycade 7
uv run barrycades solve corral 7
uv run barrycades solve corral 7 --seconds 30 --restarts 200
uv run barrycades solve barrycade 5 --balanced
```

The exit code is 1 when the search comes up empty, which says only that this search yielded no result. In that case, try giving it more time or restarts and try again. It is 2 when the arguments are refused, and 3 when a stack was found but `--verify` rejected it.

Note that there doesn't exist a balanced corral of height 3, so asking for one is one of the refused cases.

### Verify
Verify that stored construction is breakfree. You can also pass a `--balanced` flag to check that too.

```sh
uv run barrycades verify certificates/barrycades/barrycade_12.yaml
uv run barrycades verify certificates/barrycades/barrycade_12.yaml --balanced
```

The exit code is 0 when every claim asked for holds and 1 when one of them fails. A stack above the optimal order fails `--balanced`, since a row there has too few joints to reach every block.

### Render
Convert a stored construction into a picture. `--mode tex`, the default, gives the TikZ body alone. `pdf` and `svg` compile a standalone document and need `latexmk` (and `dvisvgm` for SVG).

```sh
uv run barrycades render certificates/corrals/corral_7.yaml corral_7.tex
uv run barrycades render certificates/corrals/corral_7.yaml corral_7.pdf --mode pdf
```
## Certificates

A certificate is a YAML file representing a construction:

```yaml
corral:
  order: 4
  height: 2
  permutations:
  - [4, 2, 1, 3]
  - [1, 3, 4, 2]
  shifts: [0, 1]
```

All certificates constructed by us are located inside the `certificates` folder. 

## Verifying 

There are several ways to check our solutions and your own. Firstly, you can use the verify command as described above. Secondly, you can run `uv run pytest -m claims` to verify claims made in the paper. Thirdly, you can just look at GitHub actions, where we run all the tests automatically after every change.

## Visualizations

You can see visualizations [here](images/).

## Repository structure

| Path | |
| --- | --- |
| `src/barrycades/` | the package: constructions, certificates, the command line |
| `src/barrycades/renderer/` | the pictures renderer |
| `certificates/` | the best constructions found, as certificates — corrals of height 1–50, barrycades of height 2–51 |
| `src/solver/` | the C++ simulated annealer that searched for optimal constructions |
| `tests/` | the paper's claims, checked one test per height, and the package's own behaviour |

## Annealer
uv manages the C++ part of the project for your convenience but it can also be run separately without Python.

```sh
cmake -S src/solver -B build/cmake && cmake --build build/cmake
./build/cmake/barrycades-solve barrycade 7
```