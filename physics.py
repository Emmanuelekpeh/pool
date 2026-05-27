import pymunk

def create_space():
    space = pymunk.Space()
    space.gravity = (0, 0)
    space.damping = 0.9  # Friction/damping for the balls
    return space

def create_ball(space, position, radius=15, mass=1.0, collision_type=1):
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.9
    shape.friction = 0.5
    shape.collision_type = collision_type
    space.add(body, shape)
    return body, shape

def create_wall(space, p1, p2, thickness=10):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, p1, p2, thickness)
    shape.elasticity = 0.9
    shape.friction = 0.5
    space.add(body, shape)
    return shape
