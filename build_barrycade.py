#!/usr/bin/env python3

import argparse
import logging
import pathlib
import sys

from fences import Barrycade

def build_barrycade(height):
    order = 2*height+3
    permutations = [ list() for i in range(height) ]

    for h in range(1, height):
        permutations[h] += [ h, ]

    for h in range(height):
        s = 1
        for i in range(height):
            r = (h+i)%height
            if s != r and 2*height+3-s != r:
                permutations[r] += [ 2*height+3-s, s ]
            else:
                permutations[r] += [ 2*height+3, ]
            s += 2
            if s == height or s == height+3:
                s += 2
        permutations[h] += [ height, ]

    for h in range(height):
        permutations[h] += [ height+3, 2*height+3-h, ]

    return Barrycade(order=order, height=height, permutations=permutations)

def main():
    parser = argparse.ArgumentParser(description='Constructs a Barrycade of specified height H and order 2*H+3 as in the proof of Theorem 2')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--output', default='-')
    parser.add_argument('height', type=int)
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    fence = build_barrycade(args.height)
    logging.debug(f'{type(fence).__name__} of order {fence.order} and height {fence.height} is{" " if fence.breakfree else " NOT "}breakfree')

    fence.to_auto(args.output)
    logging.debug(f'{type(fence).__name__} saved to {args.output}')

if __name__ == '__main__':
    main()
