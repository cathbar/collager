import numpy as np
import pandas as pd
from featurize import featurize_image
from image_utils import *
import metrics
import tqdm

def get_closest_children(tile, children_features, choices, metric_func):
    img_features = featurize_image(tile).get('features') # Featurize the target tile
    distances = [metric_func(img_features, child_feature) for child_feature in children_features.values] # Compute distances between tile and all candidates
    # return children_features.index[np.argmin(distances)]
    if choices < 1:
        print("Must provide a positive choice count.")
    return np.argpartition(np.array(distances), choices)[:choices] # Return the closest `choices` number of image indices

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

def write_options(target_image_filename: str, feature_filename: str, tile_filename: str, candidate_choices: int, tile_width:int, tile_height: int, metric_func_str: str):
    target_img = Image.open(target_image_filename)
    candidate_features = pd.read_csv(feature_filename, index_col='filename')['features']
    candidate_features = candidate_features.apply(lambda x: np.fromstring(x.replace('[', '').replace(']',''), sep=' '))
    all_options = _compute_options_(target_img, candidate_features, candidate_choices, tile_width, tile_height, metrics.functions.get(metric_func_str, metrics.rms))
    all_options.to_csv(tile_filename, index=False)
    return all_options