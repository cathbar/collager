from PIL import Image

def get_aspect_ratio(img):
    return img.size[0] / img.size[1]

def resize_image(image, width=0, height=0, preserve_aspect_ratio=True):
    if width > 0:
        wsize = width
        if height > 0:
            hsize = height
        else:
            wpercent = (width/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
    elif height > 0:
        hsize = height
        if width > 0:
            wsize = width
        else:
            hpercent = (width/float(image.size[1]))
            wsize = int((float(image.size[0])*float(hpercent)))
    return image.resize((wsize,hsize), Image.ANTIALIAS)

def split_img_into_tiles(im, width, height):
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

def split_img_file_into_tiles(filename, width, height):
    return split_img_into_tiles(Image.open(filename), width, height)