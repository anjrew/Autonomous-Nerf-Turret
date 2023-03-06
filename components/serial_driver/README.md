# Driver

The driver is responsible for managing the inputs from whatever controller source and forwarding the messages to the motors via serial

Examples of controller sources are:
  - ai model
  - game controller

The driver is a server that listens on a port and waits for commands from any controller and executes forwards the commands tot he