from PIL import Image
import numpy as np
import pandas as pd
import multiprocessing
from itertools import product
from functools import partial
from functools import reduce
import itertools
from featurization import *
import argparse

histograms = {}
ars = {}

def factors(n):
    return set(reduce(list.__add__,
                      ([i, n // i] for i in range(1, int(n ** 0.5) + 1) if n % i == 0)))

def children_dimension_options(img):
    widths = factors(img.size[0])
    heights = factors(img.size[1])
    aspect_ratios = {}
    for element in itertools.product(*[widths, heights]):
        ar = round(element[0] / element[1], 4)
        aspect_ratios[ar] = aspect_ratios.get(ar, []) + [element]
    return aspect_ratios

def get_resize_options(parent_image, ars_df):
    #     child_ars = set([get_aspect_ratio(img) for img in child_images])
    child_ars = ars_df.unique()
    if len(child_ars) > 1:
        print("ERR: Different shaped children!")
        print(child_ars)
    #         return
    children_ar = child_ars[0]

    new_dim_options = children_dimension_options(parent_image).get(children_ar)
    if new_dim_options is None:
        print(f"ERR: No possible dimensions with the aspect ratio: {children_ar}")
        return
    new_dim_options.sort(key=lambda tup: tup[0] * tup[1], reverse=True)
    return new_dim_options

def crop(im, width, height):
    tiles = []
    imgwidth, imgheight = im.size
    rows = []
    for i in range(0,imgheight,height):
        columns = []
        for j in range(0,imgwidth,width):
            box = (j, i, j+width, i+height)
            a = im.crop(box)
            columns.append(a)
        rows.append(columns)
    return rows

def get_closest_child_quick(img, children_histograms):
    """
    POC
    Uses histograms, whereas something else might be more effective in the future.
    """
    rmss = []
    img_histogram = np.array(img.histogram()) / (img.size[0] * img.size[1])
    rmss = [rms(img_histogram, child_histogram) for child_histogram in children_histograms.values]
    return children_histograms.index[np.argmin(rmss)]

def tiler(parent_img, dimension_tuples, children_histograms):
    results = []
    for dimension_tuple in dimension_tuples[12:]:
        tiles = crop(parent_img, dimension_tuple[0], dimension_tuple[1])
        result = Image.new('RGB', parent_img.size)
        total_tiles = len(tiles) * len(tiles[0])
        for r, row in enumerate(tiles):
            for c, tile in enumerate(row):
                print(
                    f"{r*len(tiles[0]) + c} / {total_tiles} ({round(float(r*len(tiles[0]) + c) / total_tiles,3)*100}%)")

                result.paste(
                    im=resize_image(Image.open(get_closest_child_quick(tile, children_histograms)), width=tile.size[0]),
                    box=(c * dimension_tuple[0], r * dimension_tuple[1]))
        resized = resize_image(result, width=600)
        result.save(f'tiled_{dimension_tuple[0]}_{dimension_tuple[1]}.jpg')
        resized.show()
        results.append(resized)
    return results

if __name__ == '__main__':
    # Inputs
    parent_image_filename = 'MeganandDylan-0427.jpg'
    CHILD_IMG_DIR = 'E:\\Photos\Vacations'
    input_feature_file = 'features.csv'
    output_feature_file = 'features.csv'
    input_feature_file = None

    parser = argparse.ArgumentParser(description='Process some images.')

    subparser = parser.add_subparsers()
    parser_list = subparser.add_parser('featurize')
    parser_list.add_argument('output_file', help='the output file where we\'ll store our features')

    parser_create = subparser.add_parser('tile')
    parser_create.add_argument('input_file', help='the input file from which we\'ll load all our features')
    parser_create.add_argument('-c', '--candidate_choices', type=int, help='How many candidate image options should we store for each tile?', default=9)


    args = parser.parse_args()

    # parser.add_argument('--list',
    #                     default='featurize',
    #                     const='featurize',
    #                     nargs='?',
    #                     choices=('featurize', 'tile', 'generate'),
    #                     help='list servers, storage, or both (default: %(default)s)')
    #
    # parser.add_argument("action", help="Specify ")
    #
    # parser.add_argument('integers', metavar='N', type=int, nargs='+',
    #                     help='an integer for the accumulator')
    # parser.add_argument('--sum', dest='accumulate', action='store_const',
    #                     const=sum, default=max,
    #                     help='sum the integers (default: find the max)')

    args = parser.parse_args()
    # print(args.accumulate(args.integers))

    # Featurize candidate images if necessary
    # df = pd.DataFrame()
    # if input_feature_file:
    #     df = pd.read_csv(input_feature_file)
    # elif output_feature_file:
    #     df = featurize_directory(CHILD_IMG_DIR, processes=4, output_csv=output_feature_file)

