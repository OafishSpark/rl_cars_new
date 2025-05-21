import numpy as np
import pygame
from utils import *


class Vehicle:
    width = 2 * pix_per_metr
    length = 4 * pix_per_metr
    color = (200, 200, 200)  # Базовый цвет для неопределенных агентов

    def __init__(self, x_start, lane, speed, direction):
        self.x = x_start  # координата по x
        self.lane = lane  # координата по y (дискретная)
        self.direction = direction  # направление движения (-1/1)
        self.speed = speed  # текущая скорость
        self.y = start_road_y + lane * lane_width + lane_width // 2  # позиция по y
        self.base_speed = speed  # базовая скорость без ограничений
        self.caution = 0.5  #осторожность (0-1)
        self.aggression = 0.5  # агрессия (0-1)
        self.rect = pygame.rect.Rect(
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )
        self.if_collapsed = False  # флаг столкновения
        self.lane_change_cooldown = 0  # задержка между перестроениями
        self.stuck_behind_timer = 0  # счетчик времени "в пробке"

    def collision_cars(self, vehicles):
        for v in vehicles:
            if v != self:
                if self.rect.colliderect(v.rect):
                    self.if_collapsed = True
                    v.if_collapsed = True

    def find_front_vehicle(self, vehicles):
        closest = None
        min_dist = float('inf')
        for v in vehicles:
            if v != self and v.lane == self.lane and v.direction == self.direction:
                dist = abs(v.x - self.x)
                if 0 < dist < min_dist and np.sign(v.x - self.x) == self.direction:
                    min_dist = dist
                    closest = v
        return closest, min_dist

    def adjust_speed(self, front_vehicle, min_dist):
        safe_dist = (self.speed * 1.5 + safe_distance) * (2 - self.caution)
        if front_vehicle and min_dist < safe_dist:
            self.speed = front_vehicle.speed * 0.95  # поддержание дистанции

    def _calculate_lane_score(self, candidate_lane, vehicles):
        score = 0
        for v in vehicles:
            if v.lane == candidate_lane and v.direction == self.direction:
                dist = abs(v.x - self.x)
                if dist < observation_radius:
                    score -= (1 - self.aggression) * (observation_radius - dist)
        return score

    def try_lane_change(self, vehicles):
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= 1
            return

        # обновление таймера "застревания"
        front_vehicle, min_dist = self.find_front_vehicle(vehicles)
        if front_vehicle and front_vehicle.speed < self.base_speed * 0.8:
            self.stuck_behind_timer += 1
        else:
            self.stuck_behind_timer = 0

        # условия для активации перестроения
        if (self.stuck_behind_timer < 30 or  # 1 сек при 30 FPS
                np.random.random() < 0.7 * (1 - self.caution)):
            return

        # поиск лучшей полосы
        best_lane = self.lane
        max_score = -float('inf')
        for dl in [-1, 1]:
            candidate_lane = self.lane + dl
            if 0 <= candidate_lane < num_lanes:
                score = self._calculate_lane_score(candidate_lane, vehicles)
                if score > max_score:
                    max_score = score
                    best_lane = candidate_lane

        #перестроение
        if best_lane != self.lane:
            self.lane = best_lane
            self.y = start_road_y + best_lane * lane_width + lane_width // 2
            self.lane_change_cooldown = 60  # 2 секунды при 30 FPS
            self.stuck_behind_timer = 0

    def update(self, dt, vehicles):
        if self.if_collapsed:
            self.speed = 0
            return

        front_vehicle, min_dist = self.find_front_vehicle(vehicles)
        self.adjust_speed(front_vehicle, min_dist)
        self.try_lane_change(vehicles)

        self.x += self.speed * self.direction * dt
        self.rect.update(
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )


class EgoVehicle(Vehicle):
    def __init__(self):
        super().__init__(start_road_x + 50, lane=1, speed=max_speed * 6.0, direction=1)
        self.max_lane_change_speed = 2.0 * pix_per_metr
        self.max_speed = max_speed * 4.0
        self.acceleration = 2.0 * pix_per_metr
        self.lane_change_cooldown = 0
        self.color = AI_CAR_COLOR

    def apply_action(self, action):
        self.speed += action[0] * self.acceleration * 3
        self.speed = np.clip(self.speed, 0, self.max_speed)

        if self.lane_change_cooldown <= 0 and abs(action[1]) > 0.5:
            new_lane = self.lane + np.sign(action[1])
            if 0 <= new_lane < num_lanes:
                self.lane = new_lane
                self.y = start_road_y + new_lane * lane_width + lane_width // 2
                self.lane_change_cooldown = 30  # 0.5 сек при 60 FPS
        else:
            self.lane_change_cooldown -= 1


class Norman(Vehicle):
    color = (0, 100, 250)  # синий
    caution = 0.7
    aggression = 0.3

    def try_lane_change(self, vehicles):
        front_vehicle, min_dist = self.find_front_vehicle(vehicles)
        if min_dist < 15 * pix_per_metr:
            return
        super().try_lane_change(vehicles)


class Grandma(Vehicle):
    color = (255, 200, 200)  #розовый
    base_speed = max_speed * 0.6
    caution = 1.0
    aggression = 0.0

    def try_lane_change(self, vehicles):
        if np.random.random() > 0.98:
            super().try_lane_change(vehicles)


class M_U_D_A_K(Vehicle):
    color = (255, 50, 50)  #красный
    base_speed = max_speed * 1.3
    caution = 0.1
    aggression = 0.9

    def try_lane_change(self, vehicles):
        if self.lane_change_cooldown <= 0 and np.random.random() > 0.3:
            super().try_lane_change(vehicles)
            self.lane_change_cooldown = 30  # 1 секунда при 30 FPS


class Gambler(Vehicle):
    color = (255, 215, 0)  # Желтый
    caution = 0.5
    aggression = 0.8

    def try_lane_change(self, vehicles):
        if np.random.random() < 0.15:
            super().try_lane_change(vehicles)


class Marshrutka(Grandma):
    color = (139, 69, 19)  # коричневый
    width = 3 * pix_per_metr
    length = 8 * pix_per_metr
    base_speed = max_speed * 0.5


class Truck(Marshrutka):
    color = (70, 70, 70)  #серый
    aggression = 0.2
    caution = 0.9
