import time
import math
import serial
import servo

# Define stepper motor connections and steps per revolution:
DIR_PIN = 2
STEP_PIN = 3
SHOOT_PIN = 13
AZIMUTH_SERVO_PIN = 9
STEPS_PER_REVOLUTION = 200

# Define the initial timer interval in microseconds. Start with max value
INITIAL_TIMER_INTERVAL = 0

# Define a timer interval variable
timer_interval_us = INITIAL_TIMER_INTERVAL

# The default value is the value observed when testing in MICROSECONDS
mean_serial_processing_time_us = 69

# The default value is the value observed when testing
mean_half_step_processing_time_us = 69

"""
Alternates the PIN from HIGH to LOW on each half step
"""
alternator = False

azimuth_angle_deg = 90

# The limits of the values to be set for the motor half step
SLOWEST_HALF_STEP_MICROSECONDS = 17000
FASTEST_HALF_STEP_MICROSECONDS = 1000

SLOWEST_SPEED = 0
FASTEST_SPEED = 10

MAX_AZIMUTH_DEG_RANGE= 180

azimuth_servo = servo.Servo(AZIMUTH_SERVO_PIN)  # create servo object to control a servo

class MotorSettings:
    def __init__(self, azimuth=0, is_clockwise=False, speed=0, is_firing=False):
        self.azimuth = azimuth
        self.is_clockwise = is_clockwise
        self.speed = speed
        self.is_firing = is_firing

def decode(encoded_command):
    motor_command = MotorSettings()

    encoded_value = encoded_command[0]
    motor_command.is_clockwise = (encoded_value & 0x80) >> 7;; # Get the 8th bit for clockwise
    motor_command.speed = encoded_value & 0x0F; # Mask the lower 4 bits for speed
    motor_command.is_firing = (encoded_value >> 2) & 1; # Get the 3rd bit for is_firing

    azimuth_byte = encoded_command[1]
    motor_command.azimuth = round((azimuth_byte / 255.0) * MAX_AZIMUTH_DEG_RANGE) - 90; # Scale the azimuth byte back to 0-180
    return motor_command

def map_range(value=0, min_value=1e6, max_value=FASTEST_HALF_STEP_MICROSECONDS, new_min_value=SLOWEST_SPEED, new_max_value=FASTEST_SPEED):
    # The min value of 1e6 is equal to 1 second in microseconds.
    second = 1e6

    new_range = new_max_value - new_min_value

    original_range = max_value - min_value

    scaling_factor = (float)original_range / new_range

    original_value = ((value - new_min_value) * scaling_factor) + min_value

    return int(original_value)


def process_serial_input():
    # Read the encoded motor command from serial input
    encoded_value = []
    if ser.in_waiting >= 2:
        start_of_serial_process = time.monotonic_ns()
        encoded_value.append(ser.read())
        encoded_value.append(ser.read())

        # Decode the motor command
        decoded_values = decode(encoded_value)
        speed_in = decoded_values.speed
        step_us = map_range(speed_in)

        new_azimuth = azimuth_angle_deg + decoded_values.azimuth
        if 0 <= new_azimuth <= MAX_AZIMUTH_DEG_RANGE:
            azimuth_servo.write(new_azimuth)
            azimuth_angle_deg = new_azimuth

        dir_pin_value = LOW if decoded_values.is_clockwise else HIGH
        digitalWrite(dirPin, dir_pin_value)

        shoot_pin_value = HIGH if decoded_values.is_firing else LOW
        digitalWrite(shootPin, shoot_pin_value)

        timer_interval_us = FASTEST_HALF_STEP_MICROSECONDS if step_us < FASTEST_HALF_STEP_MICROSECONDS else step_us
        mean_serial_processing_time_us = (mean_serial_processing_time_us + (time.monotonic_ns() - start_of_serial_process) / 1000) / 2

        return True
    else:
        return False

def setup():
    # Start serial for communication
    ser.baudrate = 9600
    # Declare pins as output:
    pinMode(STEP_PIN, OUTPUT)
    pinMode(DIR_PIN, OUTPUT)

    # Setup the servo motor
    azimuth_servo.attach(AZIMUTH_SERVO_PIN, 600, 2300)  # (pin, min, max)

    # Setup pin to shoot
    pinMode(SHOOT_PIN, OUTPUT)

    print("Send Commands !")


def loop():
    had_serial_input = process_serial_input()
    delay_time = mean_serial_processing_time_us if had_serial_input else 0
    print(timer_interval_us)
    # Use this logic if the value is slower than the stepper motor can handle
    if timer_interval_us > SLOWEST_HALF_STEP_MICROSECONDS:
        print('s')
        digitalWrite(STEP_PIN, HIGH if alternator else LOW)
        alternator = not alternator
        delayMicroseconds(SLOWEST_HALF_STEP_MICROSECONDS)
        digitalWrite(STEP_PIN, HIGH if alternator else LOW)
        delayMicroseconds(timer_interval_us - SLOWEST_HALF_STEP_MICROSECONDS - delay_time)
        alternator = not alternator
    elif timer_interval_us > 1:
        print('g')
        interval_step = timer_interval_us - delay_time
        delayMicroseconds(interval_step)
        digitalWrite(STEP_PIN, HIGH if alternator else LOW)
        alternator = not alternator
    else:
        print('x')
