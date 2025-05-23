import gymnasium as gym
import numpy as np
from models import *
from utils import *


class OvertakeEnv(gym.Env):
    npc_vehicles = []
    def __init__(self):
        super().__init__()
        self.action_space = gym.spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32
        )
        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(11,),  # Возвращено к исходной размерности
            dtype=np.float32
        )
        self.ego = EgoVehicle()
        self._generate_npc(3)

    def _generate_npc(self, count):
        for _ in range(count):
            direction = np.random.choice([-1, 1])
            lane = 1 if direction > 0 else 0
            speed = max_speed_c * 2

            # Выбор типа NPC
            npc_type = np.random.choice([
                Norman, Grandma, M_U_D_A_K,
                Gambler, Marshrutka, Truck
            ], p=[0.4, 0.3, 0.1, 0.1, 0.05, 0.05])

            x_start = self.ego.x + np.random.choice([-1, 1]) * np.random.randint(
                observation_radius // 4 * 3 - gen_radius,
                observation_radius // 4 * 3 + gen_radius
            )
            vehicle = npc_type(x_start, lane, speed, direction)
            self.npc_vehicles.append(vehicle)

    def reset(self, seed=None, options=None):
        self.close()
        return self._get_obs(), {}

    def _get_obs(self):
        obs = [
            self.ego.speed / self.ego.max_speed,
            self.ego.lane / (num_lanes - 1),
        ]

        visible_npc = []
        for v in self.npc_vehicles:
            distance = abs(v.x - self.ego.x)
            if distance <= observation_radius:
                visible_npc.append(v)

        visible_npc = sorted(visible_npc, key=lambda x: abs(x.x - self.ego.x))[:max_visible_vehicles]

        for v in visible_npc:
            obs.extend([
                (v.x - self.ego.x) / observation_radius,
                (v.y - self.ego.y) / road_width,
                v.speed / self.ego.max_speed
            ])

        while len(obs) < self.observation_space.shape[0]:
            obs.append(0.0)

        return np.array(obs, dtype=np.float32)

    def step(self, action):
        prev_x = self.ego.x
        prev_lane = self.ego.lane

        self.ego.apply_action(action)
        self.ego.update(0.1, self.npc_vehicles + [self.ego])
        for v in self.npc_vehicles:
            v.update(0.1, self.npc_vehicles + [self.ego])

        # награды
        progress_reward = 0.5 * (self.ego.x - prev_x) / pix_per_metr
        speed_bonus = 0.1 * (self.ego.speed / self.ego.max_speed)
        collision_penalty = 0
        if any(
                self.ego.rect.colliderect(v.rect)
                for v in self.npc_vehicles
        ):
            collision_penalty = -2000
            self.reset()

        # штраф за перестроение и награда за обгон
        lane_change_penalty = -1.0 if self.ego.lane != prev_lane else 0.0
        overtake_bonus = 0.0
        for v in self.npc_vehicles:
            if (self.ego.x > v.x + v.length and
                    abs(v.y - self.ego.y) < lane_width and
                    self.ego.lane != v.lane):
                overtake_bonus += 15.0

        # удаляем неписей
        for v in self.npc_vehicles:
            if v.if_collapsed:
                self.npc_vehicles.remove(v)
                del v
                continue
            if abs(self.ego.x - v.x) > observation_radius:
                self.npc_vehicles.remove(v)
                del v
                # print('deleted')

        # с ненулевой вероятностью генерируем неписей
        if np.random.random() > npc_proba and (len(self.npc_vehicles) < 20):
            self._generate_npc(1)
            # print("generated!")

        reward = progress_reward + speed_bonus + overtake_bonus + collision_penalty + lane_change_penalty
        done = collision_penalty < 0 or self.ego.x > road_length * 0.9

        return self._get_obs(), reward, done, False, {}