from PIL import Image

def get_aspect_ratio(img):
    """
    Get the aspect ratio of an image.
    :param img:
    :return:
    """
    return img.size[0] / img.size[1]

def resize_image(image, width=0, height=0, preserve_aspect_ratio=True):
    """
    Resize an image to specific dimensions
    :param image:
    :param width:
    :param height:
    :param preserve_aspect_ratio:
    :return:
    """
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
    """
    Split an image into tiles of specified dimensnions
    :param im:
    :param width:
    :param height:
    :return:
    """

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
    """
    Split an image file into tiles of specified dimensions
    :param filename:
    :param width:
    :param height:
    :return:
    """

    return split_img_into_tiles(Image.open(filename), width, height)

def crop_image(im, width, height):
    """
    Crop an image to a new width and height by cutting the edges.
    :param im:
    :param width:
    :param height:
    :return:
    """

    imgwidth, imgheight = im.size
    box = (int(imgwidth/2)-int(width/2), int(imgheight/2)-int(height/2), int(imgwidth/2) + width - int(width/2), int(imgheight/2) + height - int(height/2))
    return im.crop(box)

def crop_image_to_aspect_ratio(im, desired_aspect_ratio):
    """
    Crop an image into a particular aspect ratio
    :param im: The image
    :param desired_aspect_ratio: The aspect ratio to make this image
    :return:
    """

    imgwidth, imgheight = im.size
    img_aspect_ratio = imgwidth / imgheight
    box = (0, 0, imgwidth, imgheight)
    if img_aspect_ratio > desired_aspect_ratio:
        # This image is too wide, compute what the width should be and then crop it to that width.
        width = imgheight * desired_aspect_ratio
        box = (int(imgwidth / 2) - int(width / 2), 0,
               int(imgwidth / 2) + width - int(width / 2), imgheight)
    elif img_aspect_ratio < desired_aspect_ratio:
        # This image is too tall, compute what the height should be and then crop it to that height.
        height = imgwidth / desired_aspect_ratio
        box = (0, int(imgheight / 2) - int(height / 2),
               imgwidth, int(imgheight / 2) + height - int(height / 2))
    return im.crop(box)