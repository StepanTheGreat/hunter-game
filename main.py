import pygame as pg
import config



pg.display.set_caption(config.CAPTION)

screen = pg.display.set_mode((config.W, config.H))
clock = pg.time.Clock()
quitted = False

while not quitted:
    dt = clock.tick(config.FPS) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            quitted = True

    screen.fill((0, 0, 0))
    pg.display.flip()

pg.quit()