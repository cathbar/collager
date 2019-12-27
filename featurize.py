from pathlib import Path
import pandas as pd
import multiprocessing
from PIL import Image
import numpy as np
from image_utils import *
import tqdm

def featurize_image(img, normalize=True):
    hist = np.array(img.histogram())
    if normalize:
        hist = hist / (img.size[0] * img.size[1])
    return {'features': hist, 'width': img.size[0], 'height': img.size[1],
            'aspect_ratio': get_aspect_ratio(img)}

def featurize_image_file(filename: str):
    """
    Extract features and descriptive information from an image.
    :param filename: The filename of the image to featurize
    :return: A dictionary of filename, feature_vector, image_width, image_height, and aspect ratio
    """

    feature_dict = featurize_image(Image.open(filename))
    feature_dict['filename'] = filename
    return feature_dict


def featurize_directory(directory: str, processes: int = 1, output_csv: str = None):
    """
    Recursively featurize a directory's images.
    :param directory: The directory to scan
    :param processes: How many subprocesses to allow to featurize
    :param output_csv: Where to write these features
    :return:
    """

    filenames = Path(directory).glob('**/*.jpg')
    results = []
    filename_list = list(filenames)
    if processes > 1:
        with multiprocessing.Pool(processes=processes) as pool:
            # results = pool.map(featurize_image_file, list(filenames)[:5])
            results = list(tqdm.tqdm(pool.imap(featurize_image_file, filename_list), total=len(filename_list)))
    else:
        for filename in tqdm.tqdm(filename_list, total=len(filename_list)):
            results.append(featurize_image_file(filename))
    df = pd.DataFrame(results).set_index('filename')
    if output_csv:
        df.to_csv(output_csv)
    return df
