from PIL import Image
import pandas as pd
from image_utils import resize_image
import tqdm

def tile(tile_filename: str, output_filename: str, output_width: int, output_height: int, choice: int = 0):
    df = pd.read_csv(tile_filename)
    df = df[df['choice'] == choice]

    column_count = df['col'].max()
    row_count = df['row'].max()
    total_tiles = column_count * row_count

    tile_width = int(output_width / column_count)
    tile_height = int(output_height / row_count)
    result = Image.new('RGB', (column_count * tile_width, row_count * tile_height))

    pbar = tqdm.tqdm(total=row_count * column_count)
    for r in range(row_count):
        for c in range(column_count):
            choice_row = df[(df['row'] == r) & (df['col'] == c)]
            filename = choice_row['filename'].iloc[0]
            result.paste(
                im=resize_image(Image.open(filename), width=tile_width),
                box=(c * tile_width, r * tile_height))
            pbar.update(1)
    result.save(output_filename)
