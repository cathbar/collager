from PIL import Image
import numpy as np
import pandas as pd
import multiprocessing
from itertools import product
from functools import partial
from functools import reduce
import itertools
from featurize import *
from build import *
import argparse
from build import *
from tile import tile

FEATURIZE_COMMAND = 'featurize'
BUILD_COMMAND = 'build'
TILE_COMMAND = 'tile'

def parse_args():
    parser = argparse.ArgumentParser(description='Process some images.')

    subparser = parser.add_subparsers(dest='command')
    parser_list = subparser.add_parser(FEATURIZE_COMMAND)
    parser_list.add_argument('image_directory', help='the directory where candidate images can be found')
    parser_list.add_argument('output_file', help='the output file where we\'ll store our features')
    parser_list.add_argument('processes', nargs='?', const=4, type=int,
                             help='the directory where candidate images can be found')

    parser_compare = subparser.add_parser(BUILD_COMMAND)
    parser_compare.add_argument('target_image',
                                help='the image we would like to use as our parent image, rebuilding with candidate images')
    parser_compare.add_argument('feature_file', help='the input file from which we\'ll load all our features')
    parser_compare.add_argument('tile_file', help='A file where we can put information about tile choices')
    parser_compare.add_argument('comparison_func', nargs='?', default='rms', const='rms', choices=['rms'],
                                help='What metric function should we use to compare features?')
    parser_compare.add_argument('candidate_choices', nargs='?', type=int,
                                help='How many candidate image options should we store for each tile?', default=9)
    parser_compare.add_argument('tile_width', nargs='?', type=int,
                                help='How many candidate image options should we store for each tile?',
                                default=1992 / 4)
    parser_compare.add_argument('tile_height', nargs='?', type=int,
                                help='How many candidate image options should we store for each tile?',
                                default=1329 / 15)

    parser_tile = subparser.add_parser(TILE_COMMAND)
    parser_tile.add_argument('tile_file', help='A file where we can put information about tile choices')
    parser_tile.add_argument('tiled_image', help='The tiled image')
    parser_tile.add_argument('width', nargs='?', type=int,
                             help='How many candidate image options should we store for each tile?', default=5184)
    parser_tile.add_argument('height', nargs='?', type=int,
                             help='How many candidate image options should we store for each tile?', default=3456)
    parser_tile.add_argument('choice', nargs='?', type=int,
                             help='How many candidate image options should we store for each tile?', default=0)

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    if args.command == FEATURIZE_COMMAND:
        df = featurize_directory(args.image_directory, processes=args.processes, output_csv=args.output_file)
    elif args.command == BUILD_COMMAND:
        df = write_options(args.target_image, args.feature_file, args.tile_file, args.candidate_choices, int(args.tile_width), int(args.tile_height), args.comparison_func)
    elif args.command == TILE_COMMAND:
        tile(args.tile_file, args.tiled_image, args.width, args.height, args.choice)
    else:
        print('Unknown command.')
