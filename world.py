import pymunk
from physics import create_wall

WIDTH, HEIGHT = 800, 400
POCKET_RADIUS = 35

POCKET_POSITIONS = [
    (0, 0), (WIDTH//2, 0), (WIDTH, 0),
    (0, HEIGHT), (WIDTH//2, HEIGHT), (WIDTH, HEIGHT)
]

COLLISION_TYPE_BALL = 1
COLLISION_TYPE_POCKET = 2
COLLISION_TYPE_ENEMY = 3
COLLISION_TYPE_WALL = 4

def setup_table(space):
    # Create walls
    walls = []
    thickness = 10
    
    # Top walls
    walls.append(create_wall(space, (POCKET_RADIUS, 0), (WIDTH//2 - POCKET_RADIUS, 0), thickness))
    walls.append(create_wall(space, (WIDTH//2 + POCKET_RADIUS, 0), (WIDTH - POCKET_RADIUS, 0), thickness))
    
    # Bottom walls
    walls.append(create_wall(space, (POCKET_RADIUS, HEIGHT), (WIDTH//2 - POCKET_RADIUS, HEIGHT), thickness))
    walls.append(create_wall(space, (WIDTH//2 + POCKET_RADIUS, HEIGHT), (WIDTH - POCKET_RADIUS, HEIGHT), thickness))
    
    # Left wall
    walls.append(create_wall(space, (0, POCKET_RADIUS), (0, HEIGHT - POCKET_RADIUS), thickness))
    
    # Right wall
    walls.append(create_wall(space, (WIDTH, POCKET_RADIUS), (WIDTH, HEIGHT - POCKET_RADIUS), thickness))
    
    for wall in walls:
        wall.collision_type = COLLISION_TYPE_WALL
    
    # Create pockets as sensors
    pockets = []
    for pos in POCKET_POSITIONS:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos
        shape = pymunk.Circle(body, POCKET_RADIUS)
        shape.sensor = True
        shape.collision_type = COLLISION_TYPE_POCKET
        space.add(body, shape)
        pockets.append(shape)
        
    return walls, pockets
