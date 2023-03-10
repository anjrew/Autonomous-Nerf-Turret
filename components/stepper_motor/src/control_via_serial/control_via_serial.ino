/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <Servo.h>
#include "turret_control.h"
#include <stdint.h>



// Define stepper motor connections and steps per revolution:
#define dirPin 2
#define stepPin 3
#define shootPin 13
#define azimuthServoPin 9
#define stepsPerRevolution 200

// Define the initial timer interval in microseconds. Start with max value
#define INITIAL_TIMER_INTERVAL 0;

// Define a timer interval variable
unsigned long timerIntervalUs = INITIAL_TIMER_INTERVAL;

// The default value is the value observed when testing in MICROSECONDS
uint8_t meanSerialProcessingTimeUs = 69;

// The default value is the value observed when testing
uint8_t meanHalfStepProcessingTimeUs = 69;

/*
 * Alternates the PIN from HIGH to LOW on each half step
*/
bool alternator = false;

int azimuth_angle_deg = 90;


// The limits of the values to be set for the motor half step
const int SLOWEST_HALF_STEP_MICROSECONDS = 17000;
const int FASTEST_HALF_STEP_MICROSECONDS = 1000;
const int SLOWEST_STEP_SPEED = 1e6; // one second  in milli seconds which is achieved by making 1 step at slowest possible seed and then waiting until 1 second has passed

// We use the slowest speed allows minus fastest speed possible in the motor
// Not the slowest speed here is slower than the slowest step speed because we can quickly step and then wait.
// 1e6 is a million micro seconds which is 1 second
const int STEP_MICRO_SECONDS_RANGE = SLOWEST_STEP_SPEED - FASTEST_HALF_STEP_MICROSECONDS;


const uint8_t SLOWEST_SPEED = 0;
const uint8_t FASTEST_SPEED = 10;
// The speed range that is expected to come from the serial message
const uint8_t ORDINAL_SPEED_RANGE = FASTEST_SPEED - SLOWEST_SPEED;

const uint8_t MAX_AZIMUTH_DEG_RANGE= 180;

Servo azimuthServo;  // create servo object to control a servo


bool processSerialInput() {
  
  // Read the encoded motor command from serial input
  uint8_t serialBuffer[2];
  
  if (Serial.available() >= 2) {
    unsigned long startOfSerialProcess = micros();
    uint8_t serialBuffer[2];  // create a buffer to store the read uint8_ts

    Serial.readBytes(serialBuffer, 2);  // read two uint8_ts into the buffer
    
    // Decode the motor command
    TurretSettings decodedValues = decode(serialBuffer);
    int speedIn = decodedValues.speed;
    // int value, int value_min, int value_max, int new_min_value, int new_max_value
    int stepUs = mapRange(speedIn, SLOWEST_SPEED, FASTEST_SPEED, SLOWEST_STEP_SPEED, FASTEST_HALF_STEP_MICROSECONDS);

    int newAzimuth = azimuth_angle_deg +  decodedValues.azimuth;
    if (newAzimuth >= 0 && newAzimuth <= MAX_AZIMUTH_DEG_RANGE) {
      azimuthServo.write(newAzimuth);
      azimuth_angle_deg = newAzimuth;
    }
    timerIntervalUs = stepUs < FASTEST_HALF_STEP_MICROSECONDS ? FASTEST_HALF_STEP_MICROSECONDS : stepUs;

    
    digitalWrite(dirPin, decodedValues.isClockwise ? LOW : HIGH);

    digitalWrite(shootPin, decodedValues.isFiring ? HIGH: LOW);   

   
    meanSerialProcessingTimeUs = (meanSerialProcessingTimeUs + micros() - startOfSerialProcess) / 2;
//    Serial.print(" - azimuth: ");
//    Serial.print(decodedValues.azimuth);
//    Serial.print(" - azimuth: ");
//    Serial.print(decodedValues.azimuth);
//    Serial.print(" - isClockwise: ");
//    Serial.print(decodedValues.isClockwise);
//    Serial.print(" - speed: ");
//    Serial.print(decodedValues.speed);
//    Serial.println(decodedValues.isFiring);

    return true;
  } else {
    return false;
  }
}


void setup() {
  // Start serial for communication
  Serial.begin(9600);
  // Declare pins as output:
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);

  // Setup the servo motor
  azimuthServo.attach(azimuthServoPin ,600,2300);  // (pin, min, max)

  // Setup pin to shoot
  pinMode(shootPin, OUTPUT);

//  Serial.print("Current configuration");
//  Serial.print("SLOWEST_HALF_STEP_MICROSECONDS: ");
//  Serial.println(SLOWEST_HALF_STEP_MICROSECONDS);
//  Serial.print(" - FASTEST_HALF_STEP_MICROSECONDS: ");
//  Serial.println(FASTEST_HALF_STEP_MICROSECONDS);
//  Serial.print(" - SLOWEST_STEP_SPEED: ");
//  Serial.println(SLOWEST_STEP_SPEED);
//  Serial.print(" - STEP_MICRO_SECONDS_RANGE: ");
//  Serial.println(STEP_MICRO_SECONDS_RANGE);
//  Serial.print(" - SLOWEST_SPEED: ");
//  Serial.println(SLOWEST_SPEED);
//  Serial.print(" - FASTEST_SPEED: ");
//  Serial.println(FASTEST_SPEED);
//  Serial.print(" - ORDINAL_SPEED_RANGE: ");
//  Serial.println(ORDINAL_SPEED_RANGE);
//  Serial.print(" - MAX_AZIMUTH_DEG_RANGE: ");
//  Serial.println(MAX_AZIMUTH_DEG_RANGE);

  Serial.println("Send Commands !");
}


void loop() {
  
  bool had_serial_input = processSerialInput();
  uint8_t delay_time = had_serial_input ? meanSerialProcessingTimeUs : 0;
//  Serial.print("timerIntervalUs " );
//  Serial.println(timerIntervalUs );
  // Use this logic if the value is slower than the stepper motor can handle
  if (timerIntervalUs > SLOWEST_HALF_STEP_MICROSECONDS) {
//    Serial.println('s');
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator;
    delayMicroseconds(SLOWEST_HALF_STEP_MICROSECONDS);
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator; 
    int secondWaitTime = timerIntervalUs - SLOWEST_HALF_STEP_MICROSECONDS - delay_time;
    delayMicroseconds(secondWaitTime);
     
  } else if (timerIntervalUs > 1) {
//    Serial.println('g');
    unsigned long interval_step = timerIntervalUs - delay_time;

    delayMicroseconds(interval_step);
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator;
  } else {
//     Serial.println('x');
  }

}
