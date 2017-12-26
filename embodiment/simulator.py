import numpy as np
import pyglet
import pymunk
import pymunk.pyglet_util
from pymunk.vec2d import Vec2d
import ipdb

feed_touch_counter = {}

class TwoWheelVehicleRobotSimulator(object):
    def __init__(self, obstacle_num=5, obstacle_radius=30, feed_num=0, feed_radius=5):
        super(TwoWheelVehicleRobotSimulator, self).__init__()
        self.controll_func = None

        # obstacles
        OBSTACLE_RADIUS = 30
        for a in (np.linspace(0, np.pi*2, obstacle_num, endpoint=False) + np.pi/2):
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (DISPAY_MARGIN+arena_size/2+arena_size*0.3*np.cos(a), DISPAY_MARGIN+arena_size/2+arena_size*0.3*np.sin(a))
            shape = pymunk.Circle(body, obstacle_radius)
            shape.friction = 0.2
            shape.collision_type = COLLISION_TYPE_OBJECT
            space.add(shape)

        for i in range(feed_num):
            body = pymunk.Body(1, 1)
            body.position = DISPAY_MARGIN + feed_radius + np.random.rand(2) * (arena_size - feed_radius*2)
            shape = pymunk.Circle(body, feed_radius)
            shape.sensor = True
            shape.color = FEED_COLOR
            shape.collision_type = COLLISION_TYPE_FEED
            handler = space.add_collision_handler(COLLISION_TYPE_VEHICLE, COLLISION_TYPE_FEED)
            handler.pre_solve = feed_touch_handler
            handler.separate = feed_separate_handler
            space.add(body, shape)

            feed_touch_counter[shape] = 0


    def run(self):
        pyglet.clock.schedule_interval(self.__update, 1/60)
        pyglet.app.run()

    def __update(self, dt):
        if not running:
            return
        vehicle_b.velocity = (0, 0)
        vehicle_b.angular_velocity = 0
        if self.controll_func is not None:
            sensor_data = {
                "left_touch": left_sensor_val,
                "right_touch": right_sensor_val,
                "feed_touching": feed_sensor_val
            }
            #velocity_l, velocity_r = self.controll_func(left_sensor_val, right_sensor_val)
            velocity_l, velocity_r = self.controll_func(sensor_data)
            velocity_l += MOTOR_NOISE * np.random.randn()
            velocity_r += MOTOR_NOISE * np.random.randn()
            vehicle_b.apply_impulse_at_local_point((velocity_l*vehicle_b.mass, 0), (0, vehicle_radius))
            vehicle_b.apply_impulse_at_local_point((velocity_r*vehicle_b.mass, 0), (0, -vehicle_radius))
        lf = get_lateral_velocity() * vehicle_b.mass
        vehicle_b.apply_impulse_at_local_point(-lf)
        space.step(1/60)

DISPAY_MARGIN = 10
arena_size = 600
vehicle_radius = 20

COLLISION_TYPE_OBJECT = 1
COLLISION_TYPE_VEHICLE = 2
COLLISION_TYPE_LEFT_SENSOR = 3
COLLISION_TYPE_RIGHT_SENSOR = 4
COLLISION_TYPE_FEED = 5

SENSOR_ANGLE = np.pi * 45 / 180
SENSOR_RANGE = 80

running = True

SENSOR_NOISE = 0
MOTOR_NOISE = 1.0

left_sensor_val = 0
right_sensor_val = 0
feed_sensor_val = False

FEED_COLOR = (0, 0, 0)
FEED_ACTIVE_COLOR = (255, 0, 0)

FEED_EATING_TIME = 100

def feed_touch_handler(arbiter, space, data):
    global feed_sensor_val
    feed = arbiter.shapes[1]
    feed.color = FEED_ACTIVE_COLOR
    feed_touch_counter[feed] += 1
    feed_sensor_val = True
    if (feed_touch_counter[feed] > FEED_EATING_TIME):
        feed.body.position = DISPAY_MARGIN + feed.radius/2 + np.random.rand(2) * (arena_size - feed.radius)
    return True

def feed_separate_handler(arbiter, space, data):
    global feed_sensor_val
    feed = arbiter.shapes[1]
    feed.color = FEED_COLOR
    feed_touch_counter[feed] = 0
    feed_sensor_val = False
    return True

def left_sensr_handler(arbiter, space, data):
    global left_sensor_val
    p = arbiter.contact_point_set.points[0]
    distance = vehicle_b.world_to_local(p.point_b).get_length()
    left_sensor_val = 1 - distance / SENSOR_RANGE
    left_sensor_val += SENSOR_NOISE * np.random.randn()
    return True

def left_sensr_separate_handler(arbiter, space, data):
    global left_sensor_val
    left_sensor_val = 0
    return True

def right_sensr_handler(arbiter, space, data):
    global right_sensor_val
    p = arbiter.contact_point_set.points[0]
    distance = vehicle_b.world_to_local(p.point_b).get_length()
    right_sensor_val = 1 - distance / SENSOR_RANGE
    right_sensor_val += SENSOR_NOISE * np.random.randn()
    return True

def right_sensr_separate_handler(arbiter, space, data):
    global right_sensor_val
    right_sensor_val = 0
    return True


window = pyglet.window.Window(arena_size+DISPAY_MARGIN*2, arena_size+DISPAY_MARGIN*2, vsync=False)
space = pymunk.Space()
space.gravity = 0, 0

# arena
walls = [pymunk.Segment(space.static_body, (DISPAY_MARGIN, DISPAY_MARGIN), (arena_size+DISPAY_MARGIN, DISPAY_MARGIN), 0),
         pymunk.Segment(space.static_body, (arena_size+DISPAY_MARGIN, DISPAY_MARGIN), (arena_size+DISPAY_MARGIN, arena_size+DISPAY_MARGIN), 0),
         pymunk.Segment(space.static_body, (arena_size+DISPAY_MARGIN, arena_size+DISPAY_MARGIN), (DISPAY_MARGIN, arena_size+DISPAY_MARGIN), 0),
         pymunk.Segment(space.static_body, (DISPAY_MARGIN, arena_size+DISPAY_MARGIN), (DISPAY_MARGIN, DISPAY_MARGIN), 0)]
for w in walls:
    w.collision_type = COLLISION_TYPE_OBJECT
    w.friction = 0.2
space.add(walls)

# vehicle
mass = 1
vehicle_b = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, vehicle_radius))
vehicle_b.position = arena_size/2+DISPAY_MARGIN, arena_size/2+DISPAY_MARGIN
vehicle_s = pymunk.Circle(vehicle_b, vehicle_radius)
vehicle_s.friction = 0.2
vehicle_s.collision_type = COLLISION_TYPE_VEHICLE
space.add(vehicle_b, vehicle_s)

# left sensor
sensor_l_s = pymunk.Segment(vehicle_b, (0, 0), (SENSOR_RANGE * np.cos(SENSOR_ANGLE), SENSOR_RANGE * np.sin(SENSOR_ANGLE)), 0)
sensor_l_s.sensor = True
sensor_l_s.collision_type = COLLISION_TYPE_LEFT_SENSOR
handler_l = space.add_collision_handler(COLLISION_TYPE_LEFT_SENSOR, COLLISION_TYPE_OBJECT)
handler_l.pre_solve = left_sensr_handler
handler_l.separate = left_sensr_separate_handler
space.add(sensor_l_s)

# right sensor
sensor_r_s = pymunk.Segment(vehicle_b, (0, 0), (SENSOR_RANGE * np.cos(-SENSOR_ANGLE), SENSOR_RANGE * np.sin(-SENSOR_ANGLE)), 0)
sensor_r_s.sensor = True
sensor_r_s.collision_type = COLLISION_TYPE_RIGHT_SENSOR
handler_r = space.add_collision_handler(COLLISION_TYPE_RIGHT_SENSOR, COLLISION_TYPE_OBJECT)
handler_r.pre_solve = right_sensr_handler
handler_r.separate = right_sensr_separate_handler
space.add(sensor_r_s)

draw_options = pymunk.pyglet_util.DrawOptions()

@window.event
def on_draw():
    pyglet.gl.glClearColor(255,255,255,255)
    window.clear()
    space.debug_draw(draw_options)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        global running
        running = not running

def get_lateral_velocity():
    v = vehicle_b.world_to_local(vehicle_b.velocity + vehicle_b.position)
    rn = Vec2d(0, -1)
    return v.dot(rn) * rn
