from stable_baselines3.common.env_checker import check_env
from turret_env import TurretEnv

env = TurretEnv()

check_env(env, warn=True)

obs = env.reset()
n_steps = 10
for _ in range(n_steps):
    # Random action
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)
    if done:
        obs = env.reset()