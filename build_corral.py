#!/usr/bin/env python3

import argparse
import logging
import pathlib
import sys

from fences import Corral

def build_corral(height):
    order = 2*height
    permutations = [ list() for i in range(height) ]

    shifts = range(height)

    for h in range(height):
        for i in range(height):
            r = (h+i)%height
            if 2*i < height:
                s = 2*i
            else:
                s = 2*i+1
            permutations[r] += [ a for a in [ 2*height-s, s ] if a != 0 ]
        permutations[h] += [ height, ]

    return Corral(order=order, height=height, permutations=permutations, shifts=shifts)

def main():
    parser = argparse.ArgumentParser(description='Constructs a Corral of specified height H and order 2*H as in the proof of Theorem 1')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--output', default='-')
    parser.add_argument('height', type=int)
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    fence = build_corral(args.height)
    logging.debug(f'{type(fence).__name__} of order {fence.order} and height {fence.height} is{" " if fence.breakfree else " NOT "}breakfree')

    fence.to_auto(args.output)
    logging.debug(f'{type(fence).__name__} saved to {args.output}')

if __name__ == '__main__':
    main()
