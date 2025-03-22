"This is a small testing example of texture batching"

import pygame as pg

pg.font.init()

W, H = 1280, 720
FPS = 60

CHARS = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890_"
SIZE = 64

TEXTURE_SIZE = 256

class CharRect:
    def __init__(self, char: str, font: pg.Font):
        self.char = char
        self.surf = font.render(char, 0, (255, 255, 255))
        self.rect = self.surf.get_rect()

        # Google texture bleeding. We'll make a small 1 pixel gap purely for collisions, but will modify it later
        self.rect.w += 2
        self.rect.h += 2

    def width(self) -> int:
        return self.rect.width
    
    def height(self) -> int:
        return self.rect.height

    def corners(self, target_w: int, target_h: int) -> tuple[tuple, ...]:
        x, y, w, h = self.rect
        # return (
        #     (x+w+1, y), # top-right
        #     (x, y+h+1), # bottom-left
        #     (x+w+1, y+h+1), # bottom-right

        #     (x+w+1, y-target_h-1),
        # )

        return (
            (x+w, y), # top-right
            (x, y+h), # bottom-left
            (x+w, y+h), # bottom-right

            (x+w, y-target_h),
        )

    def move(self, x: int, y: int):
        self.rect.topleft = (x, y)

    def collides(self, other: "CharRect") -> bool:
        return self.rect.colliderect(other)
    
    def finalize(self) -> tuple[str, pg.Rect]:
        rect = self.rect.copy()
        rect.x += 1
        rect.y += 1
        rect.width -= 2
        rect.height -= 2

        return self.char, rect
    
    def draw(self, screen: pg.Surface, outline: bool = False):
        
        if outline:
            _, final = self.finalize()
            pg.draw.rect(screen, (255, 0, 0, 30), final)
        screen.blit(self.surf, (self.rect.x+1, self.rect.y+1))

class CharMap:
    def __init__(self, font: pg.Font, texture_size: int, resizable: bool):
        self.char_map: dict[str, CharRect] = {}
        self.resizable = resizable
        self.texture_size: int = texture_size
        self.font = font

    def __fit_char(self, new_char: CharRect) -> bool:
        char = new_char.char
        char_rects = self.char_map.values()

        while True:
            if len(self.char_map) == 0:
                self.char_map[char] = new_char
                return True
            else:
                for existing_rect in char_rects:
                    corners = existing_rect.corners(new_char.width(), new_char.height())
                    for (x, y) in corners:
                        if x >= self.texture_size-new_char.width() or y >= self.texture_size-new_char.height():
                            continue
                        elif x < 0 or y < 0:
                            continue

                        new_char.move(x, y)

                        collided = False
                        for rect in char_rects:
                            if new_char.collides(rect):
                                collided = True
                                break
                        
                        if not collided:
                            self.char_map[char] = new_char
                            return True
            
            if self.resizable:
                self.texture_size *= 2
            else:
                return False
    
    def push_char(self, char: str) -> bool:
        if char not in self.char_map:
            char_rect = CharRect(char, self.font)
            return self.__fit_char(char_rect) 
        else:
            return True
        
    def render(self) -> pg.Surface:
        surf = pg.Surface((self.texture_size, self.texture_size), pg.SRCALPHA)

        for char in self.char_map.values():
            char.draw(surf)

        return surf

screen = pg.display.set_mode((W, H))
clock = pg.time.Clock()
should_quit = False

font = pg.font.SysFont("bold", SIZE)

char_map = CharMap(font, 256, True)
for char in CHARS:
    char_map.push_char(char)

pg.image.save(char_map.render(), "char_surf.png")

char_map.push_char("+")
char_map.push_char("-")

pg.image.save(char_map.render(), "char_surf2.png")

while not should_quit:
    dt = clock.tick(FPS)

    for event in pg.event.get():
        if event.type == pg.QUIT:
            should_quit = True
    
    screen.fill((0, 0, 0))

    pg.draw.rect(screen, (0, 255, 0), (0, 0, char_map.texture_size, char_map.texture_size), 1)
    for char_rect in char_map.char_map.values():
        char_rect.draw(screen, outline=True)

    pg.display.flip()

pg.quit()