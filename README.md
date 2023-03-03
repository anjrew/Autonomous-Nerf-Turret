# Autonomous Nerf Turret

A project dedicated to creating a fully autonomous, AI-powered Nerf gun. The turret is equipped with a camera, allowing it to detect and track human targets. 

## Project structure

This project has a domain driven design where each domain lies in a folder in the root of the project. Each domain folder contains files that relate to the part of the project associated with that domain

For example:
  - The **camera_vision** folder contains files related to the computer vision tasks associated with face tracking.
  - The **stepper_motor** folder contains files related to the task of moving and controlling the stepper motor through the Arduino