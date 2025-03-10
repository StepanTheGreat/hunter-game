import pygame as pg

def get_mipmap_rect(mipmap_size: tuple[int, int], target_height: int) -> pg.Rect:
    """
    Return a region rect for the provided mipmap texture size and target height (the texture to be scaled to).

    The important requirement is that you actually insert the mimpap's texture size, not the original size.
    This function will automatically divide its width
    """
    w, h = mipmap_size
    w = w//2
    assert w%2 == 0, "A mipmapped texture can't possibly not be able to be divided by 2"


    # TODO: This can be simplified
    if target_height > h//2:
        # If the target height is more than the half height of the texture
        return pg.Rect(0, 0, w, h)
    elif target_height > h//4:
        return pg.Rect(w, 0, w//2, h//2)
    elif target_height > h//8:
        return pg.Rect(w+w//2, 0, w//4, h//4)
    else:
        # Else we'll return the last, smallest level
        return pg.Rect(w+w//2+w//4, 0, w//8, h//8)

def generate_mipmaps(image: pg.Surface, smooth_scale: bool = False) -> pg.Surface:
    """
    This function will generate 3 new levels (in total 4) of mipmaps for the texture. 
    These are used to help the renderer interpolate image better
    """
    w, h = image.get_size()

    scale_func = pg.transform.smoothscale if smooth_scale else pg.transform.scale

    level2 = scale_func(image, (w//2, h//2))
    level3 = scale_func(image, (w//4, h//4))
    level4 = scale_func(image, (w//8, h//8))
    # Create a new image that can fit the same image, and an image of size w/2, h/2
    new_image = pg.Surface((w*2, h), pg.SRCALPHA)
    new_image.blit(image, (0, 0))
    new_image.blit(level2, (w, 0))
    new_image.blit(level3, (w+w//2, 0))
    new_image.blit(level4, (w+w//2+w//4, 0))

    return new_image


    
    
