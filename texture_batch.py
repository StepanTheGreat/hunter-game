"This is a small testing example of texture batching"

import pygame as pg

pg.font.init()

W, H = 1280, 720
FPS = 60

CHARS = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890_~=\|-?.,><+@!#$%^&*()"
SIZE = 64

TEXTURE_SIZE = 256

class CharRect:
    MARGIN = 1
    def __init__(self, char: str, font: pg.Font):
        self.char = char
        self.surf = font.render(char, 0, (255, 255, 255))
        self.rect = self.surf.get_rect()

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
            (x+w+1, y), # top-right
            (x, y+h+1), # bottom-left
            (x+w+1, y+h+1), # bottom-right

            (x+w+1, y-target_h-1),
        )

    def move(self, x: int, y: int):
        self.rect.topleft = (x, y)

    def collides(self, other: "CharRect") -> bool:
        return self.rect.colliderect(other)
    
    def draw(self, screen: pg.Surface, outline: bool = False):
        
        if outline:
            pg.draw.rect(screen, (255, 0, 0, 30), self.rect)
        screen.blit(self.surf, self.rect)

class CharMap:
    def __init__(self, font: pg.Font, texture_size: int, resizable: bool):
        self.char_map: dict[str, CharRect] = {}
        self.resizable = resizable
        self.texture_width: int = texture_size
        self.texture_height: int = texture_size
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
                        if x >= self.texture_width-new_char.width() or y >= self.texture_height-new_char.height():
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
                if self.texture_width == self.texture_height:
                    self.texture_width *= 2
                else:
                    self.texture_height *= 2
            else:
                return False
    
    def push_char(self, char: str) -> bool:
        if char not in self.char_map:
            char_rect = CharRect(char, self.font)
            return self.__fit_char(char_rect) 
        else:
            return True
        
    def render(self) -> pg.Surface:
        surf = pg.Surface((self.texture_width, self.texture_height), pg.SRCALPHA)

        for char in self.char_map.values():
            char.draw(surf)

        return surf

screen = pg.display.set_mode((W, H))
clock = pg.time.Clock()
should_quit = False

font = pg.font.SysFont("bold", SIZE)

char_map = CharMap(font, 256, True)

char_map.push_char("mycoolname")
char_map.push_char("thisdudeisawesome")
char_map.push_char(">_<")
char_map.push_char("epicman")
char_map.push_char("destroyer of...uuhh...")

while not should_quit:
    dt = clock.tick(FPS)

    for event in pg.event.get():
        if event.type == pg.QUIT:
            should_quit = True
    
    screen.fill((0, 0, 0))

    pg.draw.rect(screen, (0, 255, 0), (0, 0, char_map.texture_width, char_map.texture_height), 1)
    for char_rect in char_map.char_map.values():
        char_rect.draw(screen, outline=True)

    pg.display.flip()

pg.quit()