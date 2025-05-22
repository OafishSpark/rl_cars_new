import numpy as np
import pygame
from utils import *


class Vehicle:
    width = 2 * pix_per_metr
    length = 4 * pix_per_metr
    color = (0, 0, 0)  # Базовый цвет для неопределенных агентов

    base_speed = max_speed_c  # целевая скорость
    acceleration = max_speed_c / 10  # ускорение
    max_speed = max_speed_c * 4

    caution = 0.5  # осторожность (0-1)
    aggression = 0.5  # агрессия (0-1)

    overtake_flag = False   # флаг обгона
    if_collapsed = False    # флаг аварии

    lane_change_cooldown = 0  # задержка между перестроениями
    stuck_behind_timer = 0  # счетчик времени "в пробке"

    def __init__(self, x_start, lane, speed, direction):
        self.x = x_start  # координата по x
        self.lane = lane  # координата по y (дискретная)
        self.direction = direction  # направление движения (-1/1)
        self.speed = speed  # текущая скорость
        self.y = start_road_y + lane * lane_width + lane_width // 2  # позиция по y
        self.rect = pygame.rect.Rect(   # прямоугольник для рассчёта коллизий
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )
        self.safe_distance = (self.speed * 2 + safe_distance) * (2 - self.caution) * 0.5  # безопасная дистанция для преследования
        self.safe_overtake_distance = 2 * self.safe_distance + self.length  # безопасная дистанция для обгона
        # параметры для принятия решений по Канеману-Тверски
        self.alpha = self.aggression
        self.beta = 1 - self.aggression
        self.lambd = 2 - self.aggression
        self.gamma = self.caution

    def collision_cars(self, vehicles):
        for v in vehicles:
            if v != self:
                if self.rect.colliderect(v.rect):
                    self.if_collapsed = True
                    v.if_collapsed = True
                    print('crash')
                    self.color = (200, 200, 200)
                    v.color = (200, 200, 200)

    def find_front_vehicle_lane(self, vehicles):
        closest = None
        min_dist = float('inf')
        for v in vehicles:
            if v != self and v.lane == self.lane:
                dist = abs(v.x - self.x)
                if 0 < dist < min_dist:
                    min_dist = dist
                    closest = v
        return closest, min_dist

    def adjust_speed(self, dt, front_vehicle, min_dist):
        if front_vehicle and min_dist < self.safe_distance:
            assert(front_vehicle.lane == self.lane)
            target_speed = min(front_vehicle.speed, self.base_speed)
            self.speed -= 2 * self.acceleration * dt  # поддержание дистанции
            if self.speed < target_speed:
                self.speed = target_speed
        elif self.speed < self.base_speed:
            self.speed += self.acceleration * dt
            if self.speed > self.base_speed:
                self.speed = self.base_speed
        if self.speed > self.base_speed:
            self.speed = self.base_speed

    # ищем расстояние для обгона и последнюю обгоняемую машину
    def find_overtake_vehicle(self, vehicles):
        candidates = []
        # нас интересуют только машины, которые на нашей полосе спереди
        lane = 1 if self.direction == 1 else 0
        for v in vehicles:
            if v != self and v.lane == lane and (self.x - v.x) * self.direction <= 0:
                candidates.append(v)
        # если обгонять некого
        if not candidates:
            return None
        # кандидатов сортируем по координате
        candidates.sort(key=lambda car: self.direction * car.x)
        # ищем минимальное расстояние для обгона
        vehicle = None
        for iv in range(len(candidates) - 1):
            first = candidates[iv]
            second = candidates[iv+1]
            dist = abs((second.x - self.direction * second.length // 2 - self.direction * safe_distance) \
                       - (first.x + self.direction * first.length // 2 + self.direction * safe_distance))
            if dist > (2 * safe_distance + self.length + self.speed * 2):
                vehicle = candidates[iv]
                break
        if not vehicle:
            vehicle = candidates[-1]
        # overtake_distance = vehicle.x + vehicle.length // 2 + 2 * safe_distance + self.length // 2
        return vehicle
    
    def count_overtake_time(self, vehicle):
        # считаем время обгона
        if not vehicle or vehicle.speed == max_speed_c or self.speed < max_speed_c / 10:
            return 10**6
        overtake_distance = abs((vehicle.x + self.direction * vehicle.length // 2 + 2 * safe_distance * self.direction \
                              + self.direction * self.speed * 1.5 + self.direction * self.length // 2) - self.x)
        assert(overtake_distance >= 0)
        return overtake_distance / self.speed + 60
         
    def if_can_overtake(self, vehicles, vehicle, time):
        # считаем, не врежимся ли во что-то на встречке
        approaches = []
        overtake_distance = abs((vehicle.x + self.direction * vehicle.length // 2 + self.direction * 2 * safe_distance \
                             + self.direction * self.speed * 1.5 + self.direction * self.length // 2) - self.x)
        # print(overtake_distance)
        lane = 0 if self.direction == 1 else 1
        for v in vehicles:
            if v != self and v.lane == lane and (self.x - v.x) * self.direction <= 0:
                approaches.append(v)
        if not approaches:
            return True
        approaches.sort(key=lambda car: self.direction * car.x)
        closest = approaches[0]
        # расстояние, которое будет после времени обгона до ближайшей машинки на встречке
        distance = (closest.x - self.direction * closest.length // 2 - self.direction * safe_distance) - \
            (self.x + self.direction * self.length // 2 + self.direction * safe_distance) - self.direction * max_speed_c * (time + 1)
        # print(distance)
        if distance < overtake_distance:
            return False
        print("go!")
        return True
    
    # проверяет, свободна ли соседняя линия и таймер обгона
    def if_able_to_change_lane(self, vehicles):
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= 1
            return False
        for v in vehicles:
            if v == self:
                continue
            temp_self_rect = pygame.rect.Rect(
                self.x - (self.length + safe_distance + self.speed * 2) // 2,
                0,
                (self.length + safe_distance + self.speed * 2),
                self.width
            )
            temp_v_rect = pygame.rect.Rect(
                v.x - (v.length + safe_distance + self.speed * 2) // 2,
                0,
                v.length + safe_distance + self.speed * 2,
                v.width
            )
            if temp_self_rect.colliderect(temp_v_rect):
                return False
        return True

    def change_line(self, vehicles):
        if self.if_able_to_change_lane(vehicles):
            self.lane = 0 if self.lane == 1 else 1
            self.y = start_road_y + self.lane * lane_width + lane_width // 2
            self.lane_change_cooldown = 60  # 2 секунды при 30 FPS
            self.stuck_behind_timer = 0


    def overtake(self, dt, vehicles):
        target_lane = 1 if self.direction == 1 else 0
        # ищем, что можно обогнать
        overtake_vehicle = self.find_overtake_vehicle(vehicles)
        # если ничего, то и хрен с ним
        if not overtake_vehicle:
            if self.lane != target_lane:
                self.change_line(vehicles)
            self.overtake_flag = False
            return
        # если есть, что обгонять, смотрим на встречку
        if self.if_can_overtake(vehicles, overtake_vehicle, self.count_overtake_time(overtake_vehicle)):
            # по возможности меняем полосу
            self.change_line(vehicles)
            # иначе ускоряемся если на встречке
            if self.lane != target_lane:
                if self.speed < self.max_speed:
                    self.speed += self.acceleration
                if self.speed > max_speed_c:
                    self.speed = self.max_speed
        # если нет возможности обгонять, сбрасываем скорость
        elif self.lane != target_lane:
            if self.speed > -self.max_speed:
                self.speed -= 2 * self.acceleration
            if self.speed < -self.max_speed:
                self.speed == -self.max_speed
        if self.lane != target_lane:
            self.change_line(vehicles)
        if self.lane == target_lane:
            self.overtake_flag = False

    def try_lane_change(self, vehicles):
        # смотрит, запускать ли обгон
        front_vehicle, _ = self.find_front_vehicle_lane(vehicles)
        if front_vehicle and front_vehicle.speed < self.base_speed * 0.8 \
            and (self.x + self.length // 2) > (front_vehicle.x - front_vehicle.length // 2 - safe_distance * 8):
            self.stuck_behind_timer += 1
            if (self.stuck_behind_timer < 30 or \
             np.random.random() < 0.7 * (1 - self.caution)): # 1 сек при 30 FPS
                self.overtake_flag = True
        else:
            self.stuck_behind_timer = 0
                
    def update(self, dt, vehicles):
        self.collision_cars(vehicles)
        if self.if_collapsed:
            return
        front_vehicle, min_dist = self.find_front_vehicle_lane(vehicles)
        self.try_lane_change(vehicles)
        if self.overtake_flag:
            self.overtake(dt, vehicles)
        else:
            self.adjust_speed(dt, front_vehicle, min_dist)
        self.x += self.speed * self.direction * dt
        self.rect.update(
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )


class Norman(Vehicle):
    color = (0, 100, 250)  # синий
    caution = 0.7
    aggression = 0.3
    max_speed = max_speed_c * 4
    base_speed = max_speed_c * 2

class Grandma(Vehicle):
    color = (255, 200, 200)  #розовый
    base_speed = max_speed_c * 0.6
    max_speed = base_speed
    caution = 1.0
    aggression = 0.0

class M_U_D_A_K(Vehicle):
    color = (255, 50, 50)  #красный
    base_speed = max_speed_c * 2
    max_speed = max_speed_c * 4
    caution = 0.1
    aggression = 0.9

class Gambler(Vehicle):
    color = (255, 215, 0)  # Желтый
    caution = 0.5
    aggression = 0.8
    def try_lane_change(self, vehicles):
        if np.random.random() < 0.15:
            super().try_lane_change(vehicles)


class Marshrutka(Grandma):
    color = (139, 69, 19)  # коричневый
    max_speed = max_speed_c * 2
    base_speed = max_speed_c
    def __init__(self, x_start, lane, speed, direction):
        super().__init__(x_start, lane, speed, direction)
        self.width = 3 * pix_per_metr
        self.length = 8 * pix_per_metr
        self.rect = pygame.rect.Rect(
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )
    
    def update(self, dt, vehicles):
        super().update(dt, vehicles)
        self.rect.update(
            self.x - self.length // 2,
            self.y - self.width // 2,
            self.length,
            self.width
        )



class Truck(Marshrutka):
    color = (70, 70, 70)  #серый
    aggression = 0.2
    caution = 0.9
    max_speed = max_speed_c


class EgoVehicle(Vehicle):
    def __init__(self):
        super().__init__(start_road_x + 50, lane=1, speed=max_speed_c * 6.0, direction=1)
        self.max_lane_change_speed = 2.0 * pix_per_metr
        self.max_speed = max_speed_c * 9.0
        self.base_speed = max_speed_c * 2.0
        self.acceleration = 4.0 * pix_per_metr
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