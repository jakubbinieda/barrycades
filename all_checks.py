#!/usr/bin/env python3

import argparse
import logging
import pathlib
import sys

from fences import Corral, Barrycade
from build_corral import build_corral
from build_barrycade import build_barrycade

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.info('Checking that the corral construction used in the proof of Theorem 1 works for small values of height <=50.')
    for height in range(1,51):
        fence = build_corral(height)
        if fence.height == height and fence.order == 2*height and fence.breakfree:
            logging.debug(f' * confirmed constructed corral of height {height}')
        else:
            logging.critical(f'Check failed for height {height}')
            sys.exit(1)

    logging.info('Checking that the barrycade construction used in the proof of Theorem 2 works for small values of height <=50.')
    for height in range(2,51):
        fence = build_barrycade(height)
        if fence.height == height and fence.order == 2*height+3 and fence.breakfree:
            logging.debug(f' * confirmed constructed barrycade of height {height}')
        else:
            logging.critical(f'Check failed for height {height}')
            sys.exit(1)

    logging.info('Checking that SA generated corrals are of optimal order and breakfree for height <=50 and additionally balanced for height <=20.')
    for height in range(1,51):
        fence = Corral.from_path(f'sa_corrals/corral_{height}.yaml')
        if fence.height == height and fence.order == 2*height-1 and fence.breakfree:
            logging.debug(f' * confirmed optimal corral of height {height}')
        else:
            logging.critical(f'Check failed for height {height}')
            sys.exit(1)
        if fence.height != 3 and fence.height <= 20 and not fence.balanced:
            logging.critical(f'Balance check failed for height {height}')
            sys.exit(1)

    logging.info('Checking that SA generated barrycades are of optimal order and breakfree for height <=50 and additionally balaced for height <=20.')
    for height in range(2,51):
        fence = Barrycade.from_path(f'sa_barrycades/barrycade_{height}.yaml')
        if fence.height == height and fence.order == 2*height-2 and fence.breakfree:
            logging.debug(f' * confirmed optimal barrycade of height {height}')
        else:
            logging.critical(f'Check failed for height {height}')
            sys.exit(1)
        if fence.height <= 20 and not fence.balanced:
            logging.critical(f'Balance check failed for height {height}')
            sys.exit(1)

    logging.info('All checks succesful')

if __name__ == '__main__':
    main()
