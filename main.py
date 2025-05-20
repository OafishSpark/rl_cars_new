import pygame
from models import *
from utils import *
from overtake_env import OvertakeEnv
from stable_baselines3 import PPO

device = 'cpu'

def run_simulation(use_ai=False):
    pygame.init()
    screen_width = 1600
    screen_height = 900
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()

    env = OvertakeEnv()
    model = PPO.load("ppo_overtake", device = 'cpu') if use_ai else None

    # Инициализация камеры
    camera_offset_x = 0
    camera_offset_y = 0

    running = True
    while running:
        # Плавное движение камеры
        target_offset_x = screen_width // 2 - int(env.ego.x)
        target_offset_y = screen_height // 2 - int(env.ego.y)
        camera_offset_x += (target_offset_x - camera_offset_x) * 0.1
        camera_offset_y += (target_offset_y - camera_offset_y) * 0.1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if use_ai:
            obs = env._get_obs()
            action, _ = model.predict(obs)
        else:
            keys = pygame.key.get_pressed()
            action = [
                1.0 if keys[pygame.K_UP] else -1.0 if keys[pygame.K_DOWN] else 0.0,
                1.0 if keys[pygame.K_RIGHT] else -1.0 if keys[pygame.K_LEFT] else 0.0
            ]

        obs, reward, done, _, _ = env.step(action)

        # Отрисовка
        screen.fill((255, 255, 255))
        pygame.draw.rect(
            screen, ROAD_COLOR,
            (
                start_road_x + int(camera_offset_x),
                start_road_y + int(camera_offset_y),
                road_length,
                road_width
            )
        )

        for i in range(1, num_lanes):
            pygame.draw.line(
                screen, LANE_COLOR,
                (start_road_x + int(camera_offset_x), start_road_y + i * lane_width + int(camera_offset_y)),
                (start_road_x + road_length + int(camera_offset_x), start_road_y + i * lane_width + int(camera_offset_y)),
                3
            )

        # EgoVehicle
        pygame.draw.rect(
            screen, AI_CAR_COLOR,
            (
                int(env.ego.x - env.ego.length // 2 + int(camera_offset_x)),
                int(env.ego.y - env.ego.width // 2 + int(camera_offset_y)),
                int(env.ego.length),
                int(env.ego.width)
            )
        )

        # NPC
        for v in env.npc_vehicles:
            pygame.draw.rect(
                screen, NPC_CAR_COLOR,
                (
                    v.x - v.length // 2 + int(camera_offset_x),
                    v.y - v.width // 2 + int(camera_offset_y),
                    v.length,
                    v.width
                )
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

run_simulation(use_ai=True)