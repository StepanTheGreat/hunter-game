import pygame as pg

W, H = (640, 480)
FPS = 60 

screen = pg.display.set_mode((W, H))
clock = pg.time.Clock()
running = True

w, h = 200, 150
rects = [
    pg.Rect(W//2-w//2, H//2-h//2, w, h),
    pg.Rect(30, 40, 50, 100)
]

circles = [
    (pg.Vector2(W*0.8, H*0.2), 30)
]

def circle_circle_collision(circle1: tuple[pg.Vector2, float, float], circle2: tuple[pg.Vector2, float, float]) -> bool:
    """
    Circle vs circle collisions. If 2 circles are perfectly aligned (0 distance) - won't move them out.
    In the future this should also take a mass setting
    """
    p1, r1, mass1 = circle1
    p2, r2, mass2 = circle2

    mass_sum = mass1+mass2

    distance = p1.distance_to(p2)
    if 0 < distance < r1+r2:
        direction = (p2-p1).normalize() # a direction from p1 to p2
        move_distance = abs((r1+r2)-distance)
        p1 -= direction * move_distance/2 * mass1/mass_sum
        p2 += direction * move_distance/2 * mass2/mass_sum

        return True
    
    return False

def rect_circle_collision(rect: pg.Rect, circle: pg.Vector2, radius: float) -> bool:
    """
    This is an EXTREMELY simple algorithm. 
    One issue is that if a circle's center is inside - there's no mechanism in resolving the collision then.
    I think throughout the game these types of collisions will be rare, but it's still a problem
    """
    point = pg.Vector2(
        max(rect.x, min(circle.x, rect.x+rect.w)),
        max(rect.y, min(circle.y, rect.y+rect.h))
    )

    pg.draw.circle(screen, (255, 255, 0), point, 3)
    if not rect.collidepoint(circle):
        distance = circle.distance_to(point)
        if 0 < distance <= radius:
            circle += (circle-point).normalize() * (radius-distance)
            return True

    return False
radius = 40

while running:
    dt = clock.tick(FPS) / 1000
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False 

    mpos = pg.mouse.get_pos()

    screen.fill(0)
    for rect in rects:
        pg.draw.rect(screen, (0, 0, 255), rect)

    circle_pos = pg.Vector2(*mpos)

    for rect in rects:
        rect_circle_collision(rect, circle_pos, radius)

    for circle, radius in circles:
        for rect in rects:
            rect_circle_collision(rect, circle, radius)
        pg.draw.circle(screen, (0, 0, 255), circle, radius)

    for (circle, circle_r) in circles:
        circle_circle_collision((circle, circle_r, 1), (circle_pos, radius, 10))
    
    pg.draw.circle(screen, (255, 0, 0), circle_pos, radius)

    pg.display.flip()

pg.quit()