from pathlib import Path
import pandas as pd
import multiprocessing
from PIL import Image
import numpy as np
from image_utils import *
import tqdm

def featurize_image(filename):
    img = Image.open(filename)
    hist = np.array(img.histogram()) / (img.size[0] * img.size[1])

    # histograms[str(filename)] = np.array(img.histogram()) / (img.size[0] * img.size[1])
    # ars[str(filename)] = get_aspect_ratio(img)
    # print("ar:", get_aspect_ratio(img))
    return filename, hist, img.size[0], img.size[1], get_aspect_ratio(img)


def featurize_directory(directory, processes=1, output_csv=None):
    filenames = Path(directory).glob('**/*.jpg')
    results = []
    filename_list = list(filenames)
    if processes > 1:
        with multiprocessing.Pool(processes=processes) as pool:
            # results = pool.map(featurize_image, list(filenames)[:5])
            results = list(tqdm.tqdm(pool.imap(featurize_image, filename_list), total=len(filename_list)))
    else:
        for filename in tqdm.tqdm(filename_list, total=len(filename_list)):
            import pdb
            pdb.set_trace()
            results.append(featurize_image(filename))
    df = pd.DataFrame(results, columns=['filename', 'histogram', 'width', 'height', 'aspect_ratio']).set_index('filename')
    if output_csv:
        df.to_csv(output_csv)
    return df
