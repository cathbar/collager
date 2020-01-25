from PIL import Image
import pandas as pd
from image_utils import resize_image, crop_image, crop_image_to_aspect_ratio
import tqdm
import multiprocessing
from functools import partial
import os
import math

def tile_old(tile_filename: str, output_filename: str, output_width: int, output_height: int, choice: int = 0, crop: bool = True):
    """
    Deprecated. It will populate the tiles but you have to specify the same choice number for every tile and it doesn't have any smarts about consecutive duplicates or multithreading.
    :param tile_filename:
    :param output_filename:
    :param output_width:
    :param output_height:
    :param choice:
    :param crop:
    :return:
    """

    df = pd.read_csv(tile_filename)
    df = df[df['choice'] == choice]

    column_count = df['col'].max()
    row_count = df['row'].max()

    tile_width = int(output_width / column_count)
    tile_height = int(output_height / row_count)
    result = Image.new('RGB', (column_count * tile_width, row_count * tile_height))

    pbar = tqdm.tqdm(total=row_count * column_count)
    for r in range(row_count):
        for c in range(column_count):
            choice_row = df[(df['row'] == r) & (df['col'] == c)]
            filename = choice_row['filename'].iloc[0]
            if crop:
                resized_child = crop_image(resize_image(Image.open(filename), width=tile_width), width=tile_width, height=tile_height)
            else:
                resized_child = resize_image(Image.open(filename), width=tile_width, height=tile_height)
            result.paste(
                im=resized_child,
                box=(c * tile_width, r * tile_height))
            pbar.update(1)
    result.save(output_filename)

def tile_no_neighbors(tile_filename: str, output_filename: str, output_width: int, output_height: int, aspect_ratio: float, crop: bool = True):
    """
    Also deprecated-ish. Similar to tile_old, but at least this one makes sure that neighboring tiles aren't the same image.
    This has cropping of candidate images, which is nice. This does not leverage any multiprocessing.
    It is therefore slower, but should use less RAM and is less likely to result in filling up memory if you're creating a massive image.
    Once the concurrent version is fixed, then they'd both be unlikely to do that.
    :param tile_filename:
    :param output_filename:
    :param output_width:
    :param output_height:
    :param aspect_ratio:
    :param choice:
    :param crop:
    :return:
    """

    df = pd.read_csv(tile_filename)

    column_count = df['col'].max()+1
    row_count = df['row'].max()+1

    tile_width = int(output_width / column_count)
    tile_height = int(output_height / row_count)
    result = Image.new('RGB', (column_count * tile_width, row_count * tile_height))

    pbar = tqdm.tqdm(total=row_count * column_count)
    selected_filenames = []

    for r in range(row_count):
        row_filenames = []
        for c in range(column_count):
            # Find neighbors
            neighbors = []
            if r > 0:
                if c > 0:
                    neighbors.append(selected_filenames[r - 1][c - 1])
                neighbors.append(selected_filenames[r - 1][c])
                if c < column_count-1:
                    neighbors.append(selected_filenames[r - 1][c + 1])
            if c > 0:
                    neighbors.append(row_filenames[c - 1])
            choice_rows = df[(df['row'] == r) & (df['col'] == c) & (~df['filename'].isin(neighbors))].sort_values('choice')

            filename = choice_rows['filename'].iloc[0]
            if crop:
                resized_child = resize_image(crop_image_to_aspect_ratio(Image.open(filename), aspect_ratio), width=tile_width)
            else:
                resized_child = resize_image(Image.open(filename), width=tile_width, height=tile_height)
            result.paste(
                im=resized_child,
                box=(c * tile_width, r * tile_height))
            row_filenames.append(filename)
            pbar.update(1)
        selected_filenames.append(row_filenames)
    save_final_choices(selected_filenames)
    result.save(output_filename)

def load_tile(tuple, crop=None, aspect_ratio=None, tile_width=None, tile_height=None):
    """
    Load an image into memory and crop/resize it to fit into a tile.
    This is the time-consuming part of the tiling process, so I'm breaking it into a function to multiprocess it.
    :param tuple:
    :param crop:
    :param aspect_ratio:
    :param tile_width:
    :param tile_height:
    :return:
    """

    if crop:
        return resize_image(crop_image_to_aspect_ratio(Image.open(tuple.get('filename')), aspect_ratio), width=tile_width), (tuple.get('c') * tile_width, tuple.get('r') * tile_height)
    else:
        return resize_image(Image.open(tuple.get('filename')), width=tile_width, height=tile_height), (tuple.get('c') * tile_width, tuple.get('r') * tile_height)


def tile(tile_filename: str, output_filename: str, output_width: int, output_height: int, aspect_ratio: float, processes: int, crop: bool = True):
    """
    Do the tiling. This leverages multiprocessing for loading the tiles from disk, but keep in mind that as of now,
    all of these resized candidate images are going to sit in memory and then be pasted into the final result image.
    This is fine for every use case I've run, but you could see why it might blow up in memory if you were trying to
    do this for a billboard-size image. Consider refactoring this when we start working on billboards.
    :param tile_filename:
    :param output_filename:
    :param output_width:
    :param output_height:
    :param aspect_ratio:
    :param choice:
    :param crop:
    :return:
    """

    df = pd.read_csv(tile_filename)

    column_count = df['col'].max()+1
    row_count = df['row'].max()+1


    tile_width = math.ceil(float(output_width)/ column_count)
    tile_height = math.ceil(float(output_height) / row_count)
    result = Image.new('RGB', (column_count * tile_width, row_count * tile_height))
    tuples = []

    selected_filenames = []
    for r in range(row_count):
        row_filenames = []
        for c in range(column_count):
            # Find neighbors
            neighbors = []
            if r > 0:
                if c > 0:
                    neighbors.append(selected_filenames[r - 1][c - 1])
                neighbors.append(selected_filenames[r - 1][c])
                if c < column_count-1:
                    neighbors.append(selected_filenames[r - 1][c + 1])
            if c > 0:
                    neighbors.append(row_filenames[c - 1])
            choice_rows = df[(df['row'] == r) & (df['col'] == c) & (~df['filename'].isin(neighbors))].sort_values('choice')
            filename = choice_rows['filename'].iloc[0]
            tuples.append({
                'filename': filename,
                'c': c,
                'r': r
            })
            row_filenames.append(filename)
        selected_filenames.append(row_filenames)
    with multiprocessing.Pool(processes=processes) as pool:
        result_tuple_list = list(
            tqdm.tqdm(pool.imap(partial(load_tile, crop=crop, aspect_ratio=aspect_ratio, tile_width=tile_width, tile_height=tile_height), tuples), total=len(tuples), desc='Loading tiles into memory.'))
    # input_tile_path, ext = os.path.splitext(tile_filename)
    # save_final_choices(selected_filenames, f'{input_tile_path}_final{ext}')
    for result_tuple in tqdm.tqdm(result_tuple_list, desc='Creating actual collage image'):
        result.paste(
            im=result_tuple[0],
            box=result_tuple[1])

    # If the image wasn't perfectly divisible by the tile dimensions, we'll spill over outside our desired final image dimensions. Save a copy of the uncropped then crop it and save a final version too.
    prefix, ext = os.path.splitext(output_filename)
    result.save(f'{prefix}_uncropped{ext}')
    crop_image(result, output_width, output_height, center=False).save(output_filename)

def save_final_choices(selected_filenames, filename):
    """
    Write the tile choices out to a csv. This doesn't really serve a purpose now, but I could imagine a scenario in
    which I'd like to change some tiles in a finalized image. In that case, we could just modify this and then provide
    it as input to a simple choice-based tiler (without the neighbor logic) that would just rebuild the image with the
    new tiles specified.
    :param selected_filenames: A 2d array of which filenames go to which row/column.
    :return:
    """

    dicts = []
    for r, row in enumerate(selected_filenames):
        for c, filename in enumerate(row):
            dicts.append({'tile_id': r * len(row) + c, 'row': r, 'col': c, 'choice': 0, 'filename': filename})
    df = pd.DataFrame(dicts)
    df.to_csv(filename, index=False)