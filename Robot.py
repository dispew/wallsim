import pygame
import numpy as np
import math

def dist(pt1, pt2):
    return math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)


def ang_norm(angle):  # atan2
    return -angle - 180 if -angle + 180 > 180 else -angle + 180


def ang_norm2(angle):  # robot_pos
    return angle + 360 if angle < 0 else angle


def ang_diff(a1, a2):
    if abs(a1 - a2) > 180:
        if a1 < a2:
            return -(a1 + 360 - a2)
        else:
            return -(a1 - a2 - 360)
    return -(a1 - a2)


class Robot:

    robot_speed = 2.0
    robot_turn_break = 1
    robot_turn = 2.5
    robot_init = [0, 0, 0]
    x = 0
    y = 0
    theta = 0

    # Odometry
    wheel_radius = 8.5  # 8.5 cm
    axis_dist = 15  # 15cm
    wheel_speed_constant = 0.0511

    # Sensors
    sensors = []
    sens_range = 0
    min_dist = 25

    ori_list = []
    turn_var = 0
    turn_count = 0
    turnning = False

    def __init__(self, x, y, theta, world_size):
        self.x = x
        self.y = y
        self.theta = theta
        self.robot_init = [x, y, theta]
        self.world_size = world_size
        self.surface = pygame.Surface(world_size)
        self.surface.fill((255, 255, 255, 255))
        self.font = pygame.font.SysFont('Tahoma', 8)

    def set_range_sensors(self, s, r):
        self.sensors = s
        self.sens_range = r

    def set_position(self, pos):
        [self.x, self.y, self.theta] = pos

    def get_position(self):
        return [self.x, self.y, self.theta]

    def reset_position(self):
        self.x = self.robot_init[0]
        self.y = self.robot_init[1]
        self.theta = self.robot_init[2]

    def at_goal(self, mapa_color):
        return mapa_color.get_at((int(self.x), int(self.y))) == (255, 255, 0, 255)

    # Measures (o, no, n, ne, l, se, s, so), st, x, y, ori, cur, class
    #
    # Class values
    # 1 = sala
    # 2 = corredor
    # 3 = porta
    def sense(self, mapa, mapa_color):
        self.surface.fill((255, 255, 255, 255))
        reads = [-1 for x in range(len(self.sensors))]
        reads2 = [-1, 0, 0, 0, 0, 0]

        for s in range(len(self.sensors)):
            for i in range(self.sens_range):
                sx = int(self.x + i * math.cos(math.radians(self.theta + self.sensors[s])))
                sy = int(self.y - i * math.sin(math.radians(self.theta + self.sensors[s])))

                point = mapa.get_at((sx, sy))

                if point == (0, 0, 0, 255):
                    reads[s] = i
                    pygame.gfxdraw.line(self.surface, int(self.x), int(self.y), sx, sy, (0, 255, 0, 255))
                    break
                if i == self.sens_range - 1:
                    reads[s] = -1
                    pygame.gfxdraw.line(self.surface, int(self.x), int(self.y), sx, sy, (255, 180, 255, 255))

            self.surface.blit(self.font.render('%d | %d' % (s, i), False, (0, 0, 255)), (sx + 5, sy - 5))
        # porta
        if mapa_color.get_at((int(self.x), int(self.y))) == (255, 0, 0, 255):
            reads2[5] = 3
            turn_count = 0
            reads2[0] = 1
        else:
            reads2[0] = -1

        # corredor
        if mapa_color.get_at((int(self.x), int(self.y))) == (0, 255, 0, 255):
            reads2[5] = 2

        # sala
        if mapa_color.get_at((int(self.x), int(self.y))) == (0, 0, 255, 255):
            reads2[5] = 1

        # ori
        self.ori_list.insert(0, self.theta)
        if len(self.ori_list) > 10:
            self.ori_list.pop()
        self.turn_var = np.var(self.ori_list)
        if not self.turnning and self.turn_var > 10:
            self.turnning = True
            self.turn_count += 1
        if self.turnning and self.turn_var <= 10:
            self.turnning = False
        reads2[4] = self.turn_count

        # pos ori
        reads2[1] = self.x
        reads2[2] = self.y
        reads2[3] = self.theta

        return reads + reads2

    # Simple Wall Follower
    def think(self, reads):
        v_l = 1.5
        v_r = 1.5
        reads_norm = [999 if x < 0 else x for x in reads[:8]]
        if min(reads_norm[1:4]) < self.min_dist * 0.75:
            v_l = -1.5
            v_r = 1.5
        elif min(reads_norm[3:5]) > self.min_dist:
            v_r = 0.5
        else:
            v_r = 1.5
        return [v_l, v_r]

    def move(self, vel_w_l, vel_w_r, mapa):
        old_pos = self.get_position()

        vel_w_l, vel_w_r = vel_w_r, vel_w_l
        dist = (vel_w_l * self.wheel_speed_constant * self.wheel_radius + vel_w_r * self.wheel_speed_constant * self.wheel_radius) / 2
        angl = (vel_w_l * self.wheel_speed_constant * self.wheel_radius - vel_w_r * self.wheel_speed_constant * self.wheel_radius) / self.axis_dist

        if abs(angl) > 0.0:
            self.x = self.x + dist/angl * (math.sin(math.radians(-self.theta) + angl) - math.sin(math.radians(-self.theta)))
            self.y = self.y - dist/angl * (math.cos(math.radians(-self.theta) + angl) - math.cos(math.radians(-self.theta)))
            self.theta = self.theta + math.degrees(angl)
        else:
            self.x = self.x + dist * math.cos(math.radians(-self.theta))
            self.y = self.y + dist * math.sin(math.radians(-self.theta))

        # Invalid
        while mapa.get_at((int(self.x), int(self.y))) == (0, 0, 0, 255):
            self.x = self.x + (1 if old_pos[0] >= self.x else -1)
            self.y = self.y + (1 if old_pos[1] >= self.y else -1)

    def draw(self, screen):
        if self.surface is not None:
            screen.blit(self.surface, self.surface.get_rect(), special_flags=pygame.BLEND_RGBA_MULT)
        pygame.gfxdraw.filled_circle(screen, int(self.x), int(self.y), 10, (0, 162, 232, 255))
        pygame.draw.line(screen, (237, 28, 36, 255), (int(self.x), int(self.y)),
                         (int(self.x + (15 * math.cos(math.radians(self.theta)))),
                          int(self.y - (15 * math.sin(math.radians(self.theta))))), 3)
