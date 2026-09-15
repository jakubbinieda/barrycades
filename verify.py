#!/usr/bin/env python3

import argparse
import logging
import pathlib
import sys

from fences import Fence

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--balanced', action='store_true')
    parser.add_argument('path')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    fence = Fence.from_path(args.path)
    breakfree = fence.breakfree
    balanced = fence.balanced
    print(f'{type(fence).__name__} of order {fence.order} and height {fence.height} is{" " if breakfree else " NOT "}breakfree and{" " if balanced else " NOT "}balanced')
    if breakfree:
        if args.balanced and not balanced:
            sys.exit(1)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
