import numpy as np
import pygame
from utils import *


class Vehicle:
    width = 2 * pix_per_metr
    length = 4 * pix_per_metr

    def __init__(self, x_start, lane, speed, direction):
        self.x = x_start  # координата по x
        self.lane = lane  # координата по y (дискретная)
        self.direction = direction  # в какую сторону движется (-1/1)
        self.speed = speed  # скорость по x
        self.y = start_road_y + lane * lane_width + lane_width // 2  # координата по y (на сетке)

        self.rect = pygame.rect.Rect(
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )
        self.if_collapsed = False

    def collision_cars(self, vehicles):
        for v in vehicles:
            if v != self:
                if self.rect.colliderect(v.rect):
                    self.if_collapsed == True
                    v.if_collapsed = True

    def update(self, dt, vehicles):
        if self.if_collapsed:
            self.speed = 0
        self.x += self.speed * self.direction * dt

        self.rect = pygame.rect.Rect(
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )

        self.collision_cars(vehicles)

    def offscreen(self, ego_x):
        return abs(self.x - ego_x) > observation_radius

class EgoVehicle(Vehicle):
    def __init__(self):
        super().__init__(start_road_x + 50, lane=0, speed=max_speed * 6.0, direction=1)
        self.max_lane_change_speed = 2.0 * pix_per_metr
        self.max_speed = max_speed * 4.0
        self.acceleration = 2.0 * pix_per_metr
        self.lane_change_cooldown = 0

    def apply_action(self, action):
        self.speed += action[0] * self.acceleration * 3
        self.speed = np.clip(self.speed, 0, self.max_speed)

        if self.lane_change_cooldown <= 0 and abs(action[1]) > 0.5:
            new_lane = self.lane + np.sign(action[1])
            if 0 <= new_lane < num_lanes:
                self.lane = new_lane
                self.y = start_road_y + new_lane * lane_width + lane_width // 2
                self.lane_change_cooldown = 30  # Задержка 0.5 сек (при 60 FPS)
        else:
            self.lane_change_cooldown -= 1