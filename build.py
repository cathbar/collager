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
    img_features = featurize_image(tile).get('features') # Featurize the target tile
    distances = [metric_func(img_features, child_feature) for child_feature in children_features.values] # Compute distances between tile and all candidates
    if choices < 1:
        print("Must provide a positive choice count.")
    return np.argpartition(np.array(distances), choices)[:choices] # Return the closest `choices` number of image indices

def get_closest_children(tile_dict, children_filenames, children_features, choices, metric_func):
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
    tiles = split_img_into_tiles(target_image, tile_width, tile_height)
    tuples = []
    for r, row in enumerate(tiles):
        for c, tile in enumerate(row):
            tuples.append({'row': r, 'column': c, 'tile': tile, 'tile_id': r * len(row) + c})

    with multiprocessing.Pool(processes=processes) as pool:
        result_dict_lists = list(
            tqdm.tqdm(pool.imap(partial(get_closest_children, children_filenames=children_filenames, children_features=candidate_features, choices=candidate_choices, metric_func=metric_func), tuples), total=len(tuples)))

    return pd.DataFrame(list(np.array(result_dict_lists).flatten()))

def write_options(target_image_filename: str, feature_filename: str, tile_filename: str, candidate_choices: int,
                  tiles_per_row: int, tile_aspect_ratio: float, metric_func_str: str, processes: int = 4):
    target_img = Image.open(target_image_filename)
    candidate_features = pd.read_pickle(feature_filename)['features']
    candidate_filenames = list(candidate_features.index)
    candidate_features = np.array([list(t) for t in candidate_features.values])
    tile_width = math.ceil(float(target_img.size[0]) / tiles_per_row)
    tile_height = int(tile_width / tile_aspect_ratio)
    all_options = _compute_options_concurrent_(target_img, candidate_filenames, candidate_features, candidate_choices, tile_width, tile_height, metrics.functions.get(metric_func_str, metrics.rms), processes=processes)
    all_options.to_csv(tile_filename, index=False)
    return all_options