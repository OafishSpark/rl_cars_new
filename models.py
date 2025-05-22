import numpy as np
import pygame
from utils import *


class Vehicle:
    width = 2 * pix_per_metr
    length = 4 * pix_per_metr
    color = (0, 0, 0)  # Базовый цвет для неопределенных агентов

    base_speed = max_speed // 3  # целевая скорость
    acceleration = max_speed / 10  # ускорение

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
        self.safe_distance = (max_speed * 2 + safe_distance) * (1 + self.caution)  # безопасная дистанция для преследования
        self.safe_overtake_distance = 2 * self.safe_distance + self.length  # безопасная дистанция для обгона
        # параметры для принятия решений по Канеману-Тверски
        self.alpha = self.aggression
        self.beta = 1 - self.aggression
        self.lambd = 2 - self.aggression
        self.gamma = self.caution

    def collision_cars(self, vehicles):
        # метод проверки коллизий
        for v in vehicles:
            if v != self:
                if self.rect.colliderect(v.rect):
                    self.if_collapsed = True
                    v.if_collapsed = True
                    print('crash')
                    self.color = (200, 200, 200)
                    v.color = (200, 200, 200)

    def find_front_vehicle(self, vehicles):
        # ищет ближайшую машину спереди на той же полосе и расстояние до неё
        closest = None
        min_dist = float('inf')
        for v in vehicles:
            if v != self and self.lane == v.lane and self.x - self.length // 2 < v.x + v.length // 2:
                dist = abs(v.x - self.x)
                if 0 < dist < min_dist and np.sign(v.x - self.x) == self.direction:
                    min_dist = dist
                    closest = v
        return closest, min_dist

    def adjust_speed(self, dt, front_vehicle, min_dist):
        # корректировка скорости вне обгона
        if front_vehicle:
            if min_dist < self.safe_distance:
                self.speed -= self.acceleration * dt  # поддержание дистанции
                target_speed = min(front_vehicle.speed, self.base_speed)
                if self.speed < target_speed:
                    self.speed = target_speed
                return
        if self.speed < self.base_speed:
            self.speed += self.acceleration * dt
            if self.speed > self.base_speed:
                self.speed = self.base_speed

    def find_overtake_vehicle(self, vehicles):
        # ищем расстояние для обгона и последнюю обгоняемую машину
        candidates = []
        # нас интересуют только машины, которые на нашей полосе спереди
        lane = 1 if self.direction == 1 else 0
        for v in vehicles:
            if v != self and v.lane == lane and self.x <= v.x:
                candidates.append(v)
        if not candidates:
            return None, 0
        candidates.sort(key=lambda car: car.x)
        # ищем минимальное расстояние для обгона
        vehicle = None
        distance = 0
        for iv in range(len(candidates) - 1):
            first = candidates[iv]
            second = candidates[iv+1]
            dist = (second.x - second.length // 2 - safe_distance) - \
                (first.x + first.length // 2 + safe_distance)
            if dist > self.safe_overtake_distance:
                distance = dist
                vehicle = candidates[iv]
                break
        if not vehicle:
            vehicle = candidates[-1]
        return vehicle, distance
    
    def count_worst_overtake_time(self, vehicle):
        # считаем время обгона
        if not vehicle or vehicle.speed == max_speed or self.speed < max_speed / 10:
            return 10**6
        overtake_distance = (vehicle.x + vehicle.length // 2 + 2 * safe_distance \
                             + self.speed * (1 + self.caution) + self.length // 2) - self.x
        assert(overtake_distance >= 0)
        return overtake_distance / self.speed + 60
    
    def count_best_overtake_time(self, vehicle):
        # считаем время обгона
        if not vehicle or vehicle.speed == max_speed or self.speed < max_speed / 10:
            return 10**6
        overtake_distance = (vehicle.x + vehicle.length // 2 + self.safe_overtake_distance) - self.x
        assert(overtake_distance >= 0)
        time = 60
        acceleration_time = round((max_speed - self.speed) / self.acceleration) + 1
        acceleration_distance = acceleration_time**2 * self.acceleration / 2
        time += acceleration_time
        if acceleration_distance > overtake_distance:
            return time
        time += round(acceleration_time + (overtake_distance - acceleration_distance) / max_speed) + 1 
        return time
         
    def if_able_overtake(self, vehicles, vehicle, time):
        # считаем, не врежимся ли во что-то на встречке
        approaches = []
        overtake_distance = (vehicle.x + vehicle.length // 2 + self.safe_overtake_distance) - self.x
        print(overtake_distance)
        lane = 0 if self.direction == 1 else 1
        for v in vehicles:
            if v != self and v.lane == lane and self.x <= v.x:
                approaches.append(v)
        if not approaches:
            return True
        approaches.sort(key=lambda car:car.x)
        closest = approaches[0]
        # расстояние, которое будет после времени обгона до ближайшей машинки на встречке
        distance = (closest.x - closest.length // 2) - (self.x + self.length // 2 + self.safe_overtake_distance) \
            - max_speed * time
        print(distance)
        if distance < overtake_distance:
            return False
        print("Go!")
        return True

    def if_able_to_change_line(self, vehicles):
        # проверяет, свободна ли соседняя линия и таймер обгона
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= 1
            return False
        for v in vehicles:
            if v == self:
                continue
            temp_self_rect = pygame.rect.Rect(
                int(self.x - self.safe_overtake_distance // 2),
                0,
                int(self.safe_overtake_distance),
                self.width
            )
            temp_v_rect = pygame.rect.Rect(
                int(v.x - v.safe_overtake_distance // 2),
                0,
                int(v.safe_overtake_distance),
                v.width
            )
            if temp_self_rect.colliderect(temp_v_rect):
                return False
        return True

    def change_line(self, vehicles):
        # пробуем перестроиться
        if self.if_able_to_change_line(vehicles):
            self.lane = 0 if self.lane == 1 else 1
            self.y = start_road_y + self.lane * lane_width + lane_width // 2
            self.lane_change_cooldown = 60  # 2 секунды при 30 FPS
            self.stuck_behind_timer = 0

    def overtake(self, dt, vehicles):
        # процедура обгона
        target_lane = 1 if self.direction == 1 else 0   # та линия, на которой мы должны оказаться
        overtake_vehicle, _ = self.find_overtake_vehicle(vehicles)          # ищем, что можно обогнать
        if not overtake_vehicle:    # если ничего, то взвращаемся на исходную линию и завершаем обгон
            if self.lane != target_lane:
                self.change_line(vehicles)
            if self.lane == target_lane:
                self.overtake_flag = False
            return
        time_estimation = self.aggresion * self.count_best_overtake_time() + \
            (1 - self.aggression) * self.count_worst_overtake_time()    # взвешенная оценка времени в зависимости от самонадеянности агента
        if self.if_able_overtake(vehicles, overtake_vehicle, time_estimation):  # если есть, что обгонять, смотрим на встречку
            # по возможности меняем полосу
            self.change_line(vehicles)
            # ускоряемся до максимума если на встречке и можем обгонять
            if self.lane != target_lane:
                if self.speed < max_speed:
                    self.speed += self.acceleration
                if self.speed > max_speed:
                    self.speed = max_speed
                return
        # если нет возможности обгонять, сбрасываем скорость
        else:
            if self.speed > -max_speed:
                self.speed -= dt * self.acceleration
            if self.speed < -max_speed:
                self.speed == -max_speed
        # если на чужой линии, то возвращаемся как можно скорее
        if self.lane != target_lane:
            self.change_line(vehicles)
        # если к концу процедуры на своей линии, то заканчиваем обгон
        if self.lane == target_lane:
            self.overtake_flag = False

    def overtake_descision(self, vehicles):
        target_vehicle, distance = self.find_overtake_vehicle(vehicles)
        worst_time = self.count_worst_overtake_time(target_vehicle)
        best_time = self.count_best_overtake_time(target_vehicle)
        proba_1 = (distance - self.safe_overtake_distance) / (target_vehicle.speed * worst_time)
        if proba_1 > 1:
            proba_1 = 1
        proba_2 = best_time / worst_time
        outcome = self.aggression * self.stuck_behind_timer + (self.base_speed - self.speed)
        penalty = self.speed - self.base_speed
        value = prob_correct(proba_1 * proba_2, self.gamma) * utility_function(outcome, self.alpha, self.beta, self.lambd) + \
            prob_correct(1 - proba_1 * proba_2, self.gamma) * utility_function(penalty, self.alpha, self.beta, self.lambd)
        return value > 0 

    def try_lane_change(self, vehicles):
        # смотрит, запускать ли обгон
        front_vehicle, _ = self.find_front_vehicle(vehicles)
        if front_vehicle and front_vehicle.speed <= self.base_speed \
            and (self.x + self.length // 2) > (front_vehicle.x - front_vehicle.length // 2 - safe_distance * 8):
            self.stuck_behind_timer += 1
            if self.overtake_descision(vehicles):
                print('go go go')
                self.overtake_flag = True
        else:
            self.stuck_behind_timer = 0
                
    def update(self, dt, vehicles):
        self.collision_cars(vehicles)
        if self.if_collapsed:
            return
        front_vehicle, min_dist = self.find_front_vehicle(vehicles)
        # self.try_lane_change(vehicles)
        if self.overtake_flag:
            self.overtake(dt, vehicles)
        else:
            self.adjust_speed(dt, front_vehicle, min_dist)
        self.x += self.speed * self.direction * dt
        self.rect.update(
            int(self.x) - self.length // 2,
            int(self.y) - self.width // 2,
            self.length,
            self.width
        )


class Norman(Vehicle):
    color = (0, 100, 250)  # синий


class Grandma(Vehicle):
    color = (255, 200, 200)  #розовый
    base_speed = max_speed // 4
    caution = 1.0
    aggression = 0.0


class M_U_D_A_K(Vehicle):
    color = (255, 50, 50)  #красный
    base_speed = max_speed // 3
    caution = 0.1
    aggression = 0.9

    def try_lane_change(self, vehicles):
        if self.lane_change_cooldown <= 0 and np.random.random() > 0.3:
            super().try_lane_change(vehicles)
            self.lane_change_cooldown = 30  # 1 секунда при 30 FPS


class Gambler(Vehicle):
    color = (255, 215, 0)  # Желтый
    caution = 0.5
    aggression = 0.5
    base_speed = max_speed // np.random.randint(2, 4)


class Marshrutka(Grandma):
    color = (139, 69, 19)  # коричневый
    base_speed = max_speed // 3
    width = 3 * pix_per_metr
    length = 8 * pix_per_metr



class Truck(Marshrutka):
    color = (70, 70, 70)  #серый
    aggression = 0.2
    caution = 0.9
    base_speed = max_speed // 5


class EgoVehicle(Vehicle):
    def __init__(self):
        super().__init__(start_road_x + 50, lane=1, speed=max_speed * 6.0, direction=1)
        self.max_lane_change_speed = 2.0 * pix_per_metr
        self.acceleration = 4.0 * pix_per_metr
        self.lane_change_cooldown = 0
        self.base_speed = max_speed // 4 * 3
        self.color = AI_CAR_COLOR

    def apply_action(self, action):
        self.speed += action[0] * self.acceleration * 3
        self.speed = np.clip(self.speed, 0, max_speed)

        if self.lane_change_cooldown <= 0 and abs(action[1]) > 0.5:
            new_lane = self.lane + np.sign(action[1])
            if 0 <= new_lane < num_lanes:
                self.lane = new_lane
                self.y = start_road_y + new_lane * lane_width + lane_width // 2
                self.lane_change_cooldown = 30  # 0.5 сек при 60 FPS
        else:
            self.lane_change_cooldown -= 1