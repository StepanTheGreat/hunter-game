import pygame as pg
from ward import test
from modules.atlas import SurfaceAtlas
from random import choice

COLORS = (
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
)


def make_surf(width: int, height: int) -> pg.Surface:
    new_surf = pg.Surface((width, height))
    new_surf.fill(choice(COLORS))
    return new_surf

@test("Test basic SurfaceAtlas usage")
def _():
    atlas = SurfaceAtlas((128, 32), False, 128)

    # These 4 surfaces should all fit together
    s = make_surf(28, 28)
    for char in "ABCD":
        assert atlas.push_sprite(char, s)

    # But, another one should't be able to
    assert not atlas.push_sprite("E", s)

    # But we should be able to include a smaller one!
    # From calculations, we should have 13 pixels left (from all space taken by sprites).
    # Then, we subtract 1 (because of 1-pixel margin), and we should be able to fit exactly 12 pixels!
    assert atlas.push_sprite("E", make_surf(12, 12))

    # It's important to remember that all sprites have a margin of 1 pixel, so it's a bit

@test("Test resizable SurfaceAtlas")
def _():
    atlas = SurfaceAtlas((32, 32), True, 128)

    # We're going to create a large surface that can't be fit initially without resizing
    s = make_surf(48, 48)
    assert atlas.push_sprite("A", s)
    assert atlas.get_size() == (64, 64)
    
    s = make_surf(16, 16)
    big_s = make_surf(120, 120)
    
    # Now, we'll attempt to fit a lot of small surfaces at once, and one big surface at the end.
    # This should fail of course
    assert not atlas.push_sprites("B", (s, s, s, s, big_s))

    # If we weren't able to fit - our atlas size should remain the same
    assert atlas.get_size() == (64, 64)

    # Now let's do the same thing, but without the big texture

    assert atlas.push_sprites("B", (s, s, s, s))

    # This should also increase its size
    assert atlas.get_size() == (128, 64)


@test("Test SurfaceAtlas should fail on the first sprite being bigger than the atlas")
def _():
    atlas = SurfaceAtlas((128, 128), False, 128)

    # Make a surface larger by a single pixel
    s = make_surf(129, 128)

    # Shouldn't fit
    assert not atlas.push_sprite("A", s)

    # However, a smaller one should
    s = make_surf(128, 128)
    assert atlas.push_sprite("A", s)
    