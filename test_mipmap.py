from ward import test

from mipmap import *

@test("Test that the mipmap returns proper level regions for every target height")
def _():
    texture_size = (128, 64)

    assert get_mipmap_rect(texture_size, 80) == pg.Rect(0, 0, 64, 64)
    assert get_mipmap_rect(texture_size, 32) == pg.Rect(64, 0, 32, 32)
    assert get_mipmap_rect(texture_size, 16) == pg.Rect(64+32, 0, 16, 16)
    assert get_mipmap_rect(texture_size, 8) == pg.Rect(64+32+16, 0, 8, 8)
    assert get_mipmap_rect(texture_size, 4) == pg.Rect(64+32+16, 0, 8, 8)