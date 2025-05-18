import numpy as np
from utils import *

class Vehicle:
    def __init__(self, lane, direction):
        self.width = 2 * pix_per_metr
        self.length = 4 * pix_per_metr
        self.lane = lane
        self.direction = direction
        self.speed = 0
        self.max_speed = max_speed * np.random.uniform(0.8, 1.2)

        if direction == 1:
            self.x = start_road_x + np.random.randint(0, road_length // 2)
        else:
            self.x = start_road_x + road_length - np.random.randint(0, road_length // 2)

        self.y = start_road_y + lane * lane_width + lane_width // 2
        self.target_speed = self.max_speed

    def update(self, dt, vehicles):
        front_vehicle = self.find_front_vehicle(vehicles)
        if front_vehicle and (front_vehicle.x - self.x) < safe_distance:
            self.target_speed = front_vehicle.speed
        else:
            self.target_speed = self.max_speed

        self.speed += (self.target_speed - self.speed) * dt
        self.x += self.speed * self.direction * dt

    def find_front_vehicle(self, vehicles):
        closest = None
        min_dist = float('inf')
        for v in vehicles:
            if v != self and v.lane == self.lane and v.direction == self.direction:
                dist = abs(v.x - self.x)
                if 0 < dist < min_dist and np.sign(v.x - self.x) == self.direction:
                    min_dist = dist
                    closest = v
        return closest

class EgoVehicle(Vehicle):
    def __init__(self):
        super().__init__(lane=0, direction=1)
        self.speed = max_speed * 3.0
        self.max_lane_change_speed = 2.0 * pix_per_metr
        self.max_speed = max_speed * 4.0
        self.x = start_road_x + 50
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