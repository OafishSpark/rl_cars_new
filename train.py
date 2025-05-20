import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from overtake_env import OvertakeEnv

def train():
    device = "cpu"
    env = DummyVecEnv([lambda: OvertakeEnv()])

    model = PPO(
        "MlpPolicy",
        env,
        policy_kwargs=dict(net_arch=[512, 512, 256]),
        learning_rate=1e-5,
        n_steps=8192,
        batch_size=512,
        n_epochs=50,
        gamma=0.999,
        ent_coef=0.1,  # Увеличено для исследования
        clip_range=0.2,
        verbose=1,
        device=device
    )

    model.learn(total_timesteps=3_000_0, progress_bar=True)
    model.save("ppo_overtake")

train()