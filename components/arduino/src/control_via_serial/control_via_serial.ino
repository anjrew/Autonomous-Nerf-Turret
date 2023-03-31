/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <Servo.h>
#include "turret_control.h"
#include <stdint.h>

// Define stepper motor connections and steps per revolution:
#define dirPin 2
#define stepPin 3
#define shootPin 10
#define azimuthServoPin 9
#define stepsPerRevolution 200

// Define the initial timer interval in milliseconds. Start with max value
#define INITIAL_TIMER_INTERVAL 0;

// Define a timer interval variable
unsigned long timerIntervalMs = INITIAL_TIMER_INTERVAL;

// The default value is the value observed when testing in MILLISECONDS
uint8_t meanSerialProcessingTimeMs = 69;

/*
 * Alternates the PIN from HIGH to LOW on each half step
 */
bool alternator = false;

int azimuth_angle_deg = 90;

// The limits of the values to be set for the motor half step
const int SLOWEST_HALF_STEP_MILLISECONDS = 5;
const int FASTEST_HALF_STEP_MILLISECONDS = 3;
const int SLOWEST_STEP_SPEED = 80; // in milli seconds which is achieved by making 1 step at slowest possible seed and then waiting until 1 second has passed

const uint8_t SLOWEST_SPEED = 0;
const uint8_t FASTEST_SPEED = 10;
bool isFiring = false; // Records the isFirong state for debugging purposes

const uint8_t MAX_AZIMUTH_DEG_RANGE = 180;

Servo azimuthServo; // create servo object to control a servo

bool processSerialInput()
{

  // Read the encoded motor command from serial input
  uint8_t serialBuffer[2];

  if (Serial.available() >= 2)
  {
    unsigned long startOfSerialProcess = micros();
    uint8_t serialBuffer[2]; // create a buffer to store the read uint8_ts

    Serial.readBytes(serialBuffer, 2); // read two uint8_ts into the buffer

    // Decode the motor command
    TurretSettings decodedValues = decode(serialBuffer);
    int speedIn = decodedValues.speed;

    if (speedIn < 1)
    {
      // If the speed is zero then set interval to zero so it is ignored in the loop
      timerIntervalMs = 0;
    }
    else
    {
      if (speedIn > FASTEST_SPEED)
      {
        Serial.print("Decoded speed over maximum of: ");
        Serial.print(FASTEST_SPEED);
        Serial.print(". Speed decoded was: ");
        Serial.println(speedIn);
      }
      unsigned long stepMs = mapRange(speedIn, SLOWEST_SPEED, FASTEST_SPEED, SLOWEST_STEP_SPEED, FASTEST_HALF_STEP_MILLISECONDS);

      timerIntervalMs = max(stepMs < FASTEST_HALF_STEP_MILLISECONDS ? FASTEST_HALF_STEP_MILLISECONDS : stepMs, 0);
    }

    int newAzimuth = azimuth_angle_deg + decodedValues.azimuth;
    if (newAzimuth >= 0 && newAzimuth <= MAX_AZIMUTH_DEG_RANGE)
    {
      azimuthServo.write(newAzimuth);
      azimuth_angle_deg = newAzimuth;
    }

    digitalWrite(dirPin, decodedValues.isClockwise ? LOW : HIGH);

    isFiring = decodedValues.isFiring;

    digitalWrite(shootPin, isFiring ? HIGH : LOW);

    meanSerialProcessingTimeMs = (meanSerialProcessingTimeMs + micros() - startOfSerialProcess) / 2;

    return true;
  }
  else
  {
    return false;
  }
}

void setup()
{
  // Start serial for communication
  Serial.begin(9600);
  // Declare pins as output:
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);

  // Setup the servo motor
  azimuthServo.attach(azimuthServoPin, 600, 2300); // (pin, min, max)

  // Setup pin to shoot
  pinMode(shootPin, OUTPUT);

  Serial.println("Send Commands !");
}

void loop()
{

  bool had_serial_input = processSerialInput();
  uint8_t delay_time = had_serial_input ? meanSerialProcessingTimeMs / 1000 : 0;

  // Use this logic if the value is slower than the stepper motor can handle
  if (timerIntervalMs > SLOWEST_HALF_STEP_MILLISECONDS)
  {

    digitalWrite(stepPin, alternator ? HIGH : LOW);
    alternator = !alternator;
    delay(FASTEST_HALF_STEP_MILLISECONDS);

    digitalWrite(stepPin, alternator ? HIGH : LOW);
    alternator = !alternator;
    int secondWaitTime = timerIntervalMs - FASTEST_HALF_STEP_MILLISECONDS - delay_time;

    delay(secondWaitTime);
  }
  else if (timerIntervalMs > 1)
  {

    unsigned long interval_step = timerIntervalMs - delay_time;

    delay(interval_step);
    digitalWrite(stepPin, alternator ? HIGH : LOW);
    alternator = !alternator;
  }
  else
  {
  }
}
