pix_per_metr = 5
road_length = 1000000 * pix_per_metr
road_width = 10 * pix_per_metr
num_lanes = 2
lane_width = road_width // num_lanes
start_road_x = 4 * pix_per_metr
start_road_y = 4 * pix_per_metr
max_speed = 10 * pix_per_metr
safe_distance = 2 * pix_per_metr
observation_radius = 1000 * pix_per_metr
max_visible_vehicles = 3

npc_proba = 0.9
gen_radius = 200 * pix_per_metr

screen_width, screen_height = 1600, 800

# Размеры и позиция окошка
window_width, window_height = 200, 80  # Ширина и высота
window_x, window_y = 10, 10  # Отступ слева и сверху

ROAD_COLOR = (50, 50, 50)
AI_CAR_COLOR = (0, 200, 0)
NPC_CAR_COLOR = (200, 50, 50)
LANE_COLOR = (150, 150, 150)

# Цвета
BACKGROUND_COLOR = (50, 50, 50)  # Тёмно-серый фон окошка
TEXT_COLOR = (255, 255, 255)     # Белый текст
BORDER_COLOR = (100, 100, 100)   # Цвет рамки

def utility_function(x, alpha=1, beta=2, lambd=2):
    # функция полезности из теории перспектив Канемана-Тверски
    if x >= 0:
        return x**alpha
    else:
        return -lambd * (-x)**beta
    
def prob_correct(p, gamma = 0.65):
    # функция коррекции вероятности
    return p**gamma / (p**gamma + (1-p)**gamma) ** (1/gamma)
