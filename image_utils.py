
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
