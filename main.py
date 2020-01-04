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
    parser_compare.add_argument('--comparison_func', nargs='?', default='rms', const='rms', choices=['rms'],
                                help='What metric function should we use to compare features?')
    parser_compare.add_argument('--candidate_choices', nargs='?', type=int,
                                help='How many candidate image options should we store for each tile?', default=9)
    parser_compare.add_argument('--tiles_per_row', nargs='?', type=int,
                                help='How many tiles should go into each row',
                                default=16)
    parser_compare.add_argument('--tile_aspect_ratio', nargs='?', type=float,
                                help='What aspect ratio should the tiles have?',
                                default=1.5)
    parser_compare.add_argument('--processes', nargs='?', type=int,
                                help='How many concurrent processes should we put towards this?',
                                default=4)

    parser_tile = subparser.add_parser(TILE_COMMAND)
    parser_tile.add_argument('tile_file', help='A file where we can put information about tile choices')
    parser_tile.add_argument('tiled_image', help='The tiled image')
    parser_tile.add_argument('width', nargs='?', type=int,
                             help='How many candidate image options should we store for each tile?', default=1992)
    parser_tile.add_argument('height', nargs='?', type=int,
                             help='How many candidate image options should we store for each tile?', default=1329)
    parser_tile.add_argument('--choice', nargs='?', type=int,
                             help='How many candidate image options should we store for each tile?', default=0)
    parser_tile.add_argument('--tile_aspect_ratio', nargs='?', type=float,
                                help='What aspect ratio should the tiles have?',
                                default=1.5)
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    if args.command == FEATURIZE_COMMAND:
        df = featurize_directory(args.image_directory, args.output_file, processes=args.processes)
    elif args.command == BUILD_COMMAND:
        df = write_options(args.target_image, args.feature_file, args.tile_file, args.candidate_choices,
                           int(args.tiles_per_row), float(args.tile_aspect_ratio), args.comparison_func, processes=args.processes)
    elif args.command == TILE_COMMAND:
        tile(args.tile_file, args.tiled_image, args.width, args.height, args.tile_aspect_ratio, args.choice)
    else:
        print('Unknown command.')
