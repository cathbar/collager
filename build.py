import numpy as np
import pandas as pd
from featurize import featurize_image
from image_utils import *
import metrics
import tqdm
import math
import multiprocessing
from functools import partial

def get_closest_children_old(tile, children_features, choices, metric_func):
    """
    Deprecated. This was fine for when we were single threaded. I switched things to be a little more compartmentalized/opaque when I went parallelized. Not ideal, but it's a side project.
    :param tile:
    :param children_features:
    :param choices:
    :param metric_func:
    :return:
    """

    img_features = featurize_image(tile).get('features') # Featurize the target tile
    distances = [metric_func(img_features, child_feature) for child_feature in children_features.values] # Compute distances between tile and all candidates
    if choices < 1:
        print("Must provide a positive choice count.")
    return np.argpartition(np.array(distances), choices)[:choices] # Return the closest `choices` number of image indices

def get_closest_children(tile_dict, children_filenames, children_features, choices, metric_func):
    """
    A function to get the closest `choices` number of children for a tile. I ended up throwing around some loaded data structures here, like a dictionary full of values, because pool.imap(partial) always screws me up and I want to go to bed. I think you'd use a starmap or whatever and that's annoying.
    :param tile_dict: A dictionary that has everything we need for a tile. This is the variable part of the function. Everything else would be standardized across every multiprocess and is therefore handled by the partial.
    :param children_filenames: A list of filenames that corresponds to the children_features.
    :param children_features: A list of features that corresponds to the children_filenames.
    :param choices: How many top choices you want to keep for each tile. 1 means the top choice, 5 should ensure no self-adjacent images with the current tiler, 9 ensures that you'll never risk self-adjacency for most (all?) future tilers.
    :param metric_func: What metric function to use
    :return: A `choices`-size list of dictionaries that has all the info for each choice
    """

    result_dicts = []
    r = tile_dict['row']
    c = tile_dict['column']
    tile_id = tile_dict['tile_id']
    tile = tile_dict['tile']

    img_features = featurize_image(tile).get('features') # Featurize the target tile
    distances = metric_func(img_features, children_features)
    if choices < 1:
        print("Must provide a positive choice count.")

    best_candidates_for_tile = np.argpartition(np.array(distances), choices)[:choices] # Return the closest `choices` number of image indices
    for choice, candidate in enumerate(best_candidates_for_tile):
        result_dicts.append({'tile_id': tile_id, 'row': r, 'col': c, 'choice': choice,
                             'filename': children_filenames[candidate]})
    return result_dicts

def _compute_options_(target_image, candidate_features: str, candidate_choices: int, tile_width:int, tile_height: int, metric_func):
    """
    Deprecated comparison function. This was when we were still single processed. Not very cash money.
    :param target_image:
    :param candidate_features:
    :param candidate_choices:
    :param tile_width:
    :param tile_height:
    :param metric_func:
    :return:
    """

    tiles = split_img_into_tiles(target_image, tile_width, tile_height)
    total_tile_count = len(tiles) * len(tiles[0])
    result_dicts = []
    pbar = tqdm.tqdm(total=total_tile_count)

    for r, row in enumerate(tiles):
        for c, tile in enumerate(row):
            best_candidates_for_tile = get_closest_children(tile, candidate_features, candidate_choices, metric_func)
            for choice, candidate in enumerate(best_candidates_for_tile):
                result_dicts.append({'tile_id': r*len(tiles[0]) + c, 'row': r, 'col': c, 'choice': choice, 'filename': candidate_features.index[candidate]})
            pbar.update(1)
    return pd.DataFrame(result_dicts)

def _compute_options_concurrent_(target_image, children_filenames, candidate_features: str, candidate_choices: int, tile_width: int,
                          tile_height: int, metric_func, processes: int = 4):
    """
    Split an image into tiles, then concurrently find the best `candidate_choices` number of candidate images for each tile using `processes` number of processes.
    :param target_image: The image we're trying to rebuild with tiles
    :param children_filenames: The filenames of the candidate images
    :param candidate_features: The features of the candidate images
    :param candidate_choices: How many candidate images we want to keep for each tile
    :param tile_width: The width of the tiles
    :param tile_height: The height of the tiles
    :param metric_func: The metric function we'll use to compare
    :param processes: How many processes we'll split this across
    :return:
    """

    tiles = split_img_into_tiles(target_image, tile_width, tile_height)
    dicts = []
    for r, row in enumerate(tiles):
        for c, tile in enumerate(row):
            dicts.append({'row': r, 'column': c, 'tile': tile, 'tile_id': r * len(row) + c})
    result_dict_lists = []
    if processes > 1:
        with multiprocessing.Pool(processes=processes) as pool:
            result_dict_lists = list(
                tqdm.tqdm(pool.imap(partial(get_closest_children, children_filenames=children_filenames, children_features=candidate_features, choices=candidate_choices, metric_func=metric_func), dicts), total=len(dicts)))
    else:
        pbar = tqdm.tqdm(total=len(tiles) * len(tiles[0]))
        for dic in dicts:
            result_dict_lists.append(get_closest_children(dic, children_filenames=children_filenames,
                                        children_features=candidate_features, choices=candidate_choices,
                                        metric_func=metric_func))
            pbar.update(1)
    return pd.DataFrame(list(np.array(result_dict_lists).flatten()))

def write_options(target_image_filename: str, feature_filename: str, tile_filename: str, candidate_choices: int,
                  tiles_per_row: int, tile_aspect_ratio: float, metric_func_str: str, processes: int = 4):
    """
    The main driver function for build. This file has some pretty poorly named methods. It will load all of the data and files we need, do some basic math to figure out tile sizes, then kick off the actual processing.
    :param target_image_filename: The filename of the image we intend to recreate
    :param feature_filename: The filename where the candidate images' features are stored
    :param tile_filename: The output filename where we will write our tiling decisions
    :param candidate_choices: How many candidate options to keep around for each tile. 1 means the top choice, 5 should ensure no self-adjacent images with the current tiler, 9 ensures that you'll never risk self-adjacency for most (all?) future tilers.
    :param tiles_per_row: How many tiles should we put in each row? I use this and aspect ratio to compute tile dimensions. It seems more user friendly than asking for pixels.
    :param tile_aspect_ratio: What aspect ratio should our tiles have? I will crop edges to ensure we meet it.
    :param metric_func_str: The string label of our metric function. New metric functions will need to have their label defined in metrics.functions
    :param processes: How many child processes to kick off for this sucker
    :return:
    """
    
    target_img = Image.open(target_image_filename)
    candidate_features = pd.read_pickle(feature_filename)['features']
    # Drop any images that aren't RGB
    candidate_features = candidate_features[candidate_features.str.len()==768] # Hacky AF
    candidate_filenames = list(candidate_features.index)
    candidate_features = np.array([list(t) for t in candidate_features.values])
    tile_width = math.ceil(float(target_img.size[0]) / tiles_per_row)
    tile_height = int(tile_width / tile_aspect_ratio)
    all_options = _compute_options_concurrent_(target_img, candidate_filenames, candidate_features, candidate_choices, tile_width, tile_height, metrics.functions.get(metric_func_str, metrics.rms), processes=processes)
    all_options.to_csv(tile_filename, index=False)
    return all_options