import pygame
from models import *
from utils import *
from overtake_env import OvertakeEnv
from stable_baselines3 import PPO


def run_simulation(use_ai=False):
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()

    env = OvertakeEnv()
    model = PPO.load("ppo_overtake", device = 'cpu') if use_ai else None

    # Инициализация камеры
    camera_offset_x = 0
    camera_offset_y = 0

    score = 0

    running = True
    done = False

    while running:
        # Плавное движение камеры
        target_offset_x = screen_width // 2 - int(env.ego.x)
        target_offset_y = screen_height // 2 - int(env.ego.y)
        camera_offset_x += (target_offset_x - camera_offset_x) * 0.1
        camera_offset_y += (target_offset_y - camera_offset_y) * 0.1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if done:
            continue

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
        score += reward

        # Отрисовка
        screen.fill((255, 255, 255))
        pygame.draw.rect(
            screen, ROAD_COLOR,
            (
                0,
                start_road_y + int(camera_offset_y),
                road_length,
                road_width
            )
        )

        for i in range(1, num_lanes):
            pygame.draw.line(
                screen, LANE_COLOR,
                (0, start_road_y + i * lane_width + int(camera_offset_y)),
                (road_length, start_road_y + i * lane_width + int(camera_offset_y)),
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
            temp_rect = pygame.rect.Rect(
                v.x - v.length // 2 + int(camera_offset_x),
                v.y - v.width // 2 + int(camera_offset_y),
                v.length,
                v.width
            )
            pygame.draw.rect(
                screen, v.color, temp_rect
            )

        # Окошко с текстом
        pygame.display.set_caption("врум-врум")
        font = pygame.font.Font(None, 24)  # Шрифт (None = стандартный)
        text_lines = [
            f'Скросость: {env.ego.speed}',
            f'Очки: {score:.2f}',
        ]
        rendered_lines = []
        for line in text_lines:
            rendered_lines.append(font.render(line, True, TEXT_COLOR))
        pygame.draw.rect(
            screen,
            BACKGROUND_COLOR,
            (window_x, window_y, window_width, window_height),
            border_radius=8
        )
        pygame.draw.rect(
            screen,
            BORDER_COLOR,
            (window_x, window_y, window_width, window_height),
            2,
            border_radius=8
        )
        for i, line in enumerate(rendered_lines):
            screen.blit(
                line,
                (window_x + 10, window_y + 10 + i * 25)  # Отступы внутри окошка
            )

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

run_simulation(use_ai=False)
