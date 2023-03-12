# Autonomous Nerf Turret

A project dedicated to creating a fully autonomous, AI-powered Nerf gun. The turret is equipped with a camera, allowing it to detect and track human targets. 

## Getting started

This project was built on MacOS on top of these two main dependencies:

 - bash
 - conda

 If these are installed then run the following command in the project root to get the rest of the dependencies and setup the virtual environment:
 ```bash
source bin/init.sh
 ```

 When coming back to the project to reactivate the environment run the following in the project root:
 ```bash
 source bin/activate.sh
 ```


## Project structure

This project has a domain driven design where each domain lies in a folder in the root of the project. Each domain folder contains files that relate to the part of the project associated with that domain

For example:
  - The **camera_vision** folder contains files related to the computer vision tasks associated with face tracking.
  - The **stepper_motor** folder contains files related to the task of moving and controlling the stepper motor through the Arduino


  # Versions

  - 1 - Stepperonline Nema 17 Stepper Motor, 45 Ncm, 1.5 A, 12 V, 39 mm, 4-Wire 1.8 Deg Stepper Motor with 1 m Wire for 3D Printers:
    - When firing under full load with stepper servo and gun the circuit pulls around 1.8A when running and 2.1A when starting up
    - Of this the gun motors take up around 1.1A at full speed and 1.9A when starting up
    - On stand still the circuit uses 0.08A