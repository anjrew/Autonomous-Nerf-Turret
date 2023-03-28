# Reinforcement learning controller

This component is where the reinforcement learning controller information is based

## Framework.

Using stable baselines with a Custom Environment that taps into the feed from the output of the vision controller.

## View Tensorboard
Run the following command from the root of the project
```bash
tensorboard --logdir=./components/rl_controller/turret_tensorboard
```