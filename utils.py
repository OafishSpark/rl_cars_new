pix_per_metr = 20
road_length = 1000 * pix_per_metr
road_width = 10 * pix_per_metr
num_lanes = 2
lane_width = road_width // num_lanes
start_road_x = 4 * pix_per_metr
start_road_y = 4 * pix_per_metr
max_speed = 1.5 * pix_per_metr
safe_distance = 2 * pix_per_metr
observation_radius = 500 * pix_per_metr
max_visible_vehicles = 3

ROAD_COLOR = (50, 50, 50)
AI_CAR_COLOR = (0, 200, 0)
NPC_CAR_COLOR = (200, 50, 50)
LANE_COLOR = (150, 150, 150)