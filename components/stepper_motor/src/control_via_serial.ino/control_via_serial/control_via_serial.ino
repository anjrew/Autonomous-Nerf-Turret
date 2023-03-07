/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <ArduinoJson.h>
#include <Servo.h>

// Define stepper motor connections and steps per revolution:
#define dirPin 2
#define stepPin 3
#define stepsPerRevolution 200

// Define the initial timer interval in microseconds. Start with max value
#define INITIAL_TIMER_INTERVAL 0;

// Define a timer interval variable
unsigned long timerIntervalUs = INITIAL_TIMER_INTERVAL;

// The default value is the value observed when testing in MICROSECONDS
byte meanSerialProcessingTimeUs = 69;

// The default value is the value observed when testing
byte meanHalfStepProcessingTimeUs = 69;

/*
 * Alternates the PIN from HIGH to LOW on each half step
*/
bool alternator = false;


// The limits of the values to be set for the motor half step
const int SLOWEST_HALF_STEP_MICROSECONDS = 17000;
const int FASTEST_HALF_STEP_MICROSECONDS = 1000;

const byte SLOWEST_SPEED = 0;
const byte FASTEST_SPEED = 10;

Servo azimuthServo;  // create servo object to control a servo

class MotorSettings {
public:
  MotorSettings(bool clockwise, int speed, int azimuth) : isClockwise(clockwise), speed(speed), azimuth(azimuth) {}
  bool isClockwise;
  int speed;
  int azimuth;
};


MotorSettings decode(uint8_t encodedValue) {
  bool isClockwise = (encodedValue >> 7) & 1; // Extract the 8th bit for clockwise
  int speed = encodedValue & 0x0F; // Extract the lower 4 bits for speed (0-10)
  int azimuth = ((encodedValue >> 4) & 0xFF) * 16;
  Serial.println(azimuth);
  return MotorSettings(isClockwise, speed, azimuth);
}

int map_range(int value = 0, int min_value = SLOWEST_HALF_STEP_MICROSECONDS, int max_value = FASTEST_HALF_STEP_MICROSECONDS, int new_min_value = SLOWEST_SPEED, int new_max_value = FASTEST_SPEED) {
    
    int new_range = new_max_value - new_min_value;

    int original_range = max_value - min_value;

    float scaling_factor = (float)original_range / new_range;

    float original_value = ((value - new_min_value) * scaling_factor) + min_value;

    return int(original_value);
}


bool processSerialInput() {
  if (Serial.available() > 0) {
    Serial.println("READING Serial");
    unsigned long startOfSerialProcess = micros();
    byte receivedBytes[2];

    // Read the two bytes of data from the serial port
    Serial.readBytes(receivedBytes, 2);
    
    // Combine the two bytes into a single value
    uint8_t encodedValue = (receivedBytes[0] << 8) | receivedBytes[1];
//    uint8_t encodedValue = Serial.read();
    
    MotorSettings decodedValues = decode(encodedValue);
    int speed_in = decodedValues.speed;
    int stepUs = map_range(speed_in);
    Serial.println(decodedValues.azimuth);
    azimuthServo.write(decodedValues.azimuth);

    if (decodedValues.isClockwise) {
        digitalWrite(dirPin, HIGH);
    }
    else {
      digitalWrite(dirPin, LOW);
    }
      
    if (stepUs < SLOWEST_HALF_STEP_MICROSECONDS && stepUs >= FASTEST_HALF_STEP_MICROSECONDS) {
      stepUs = stepUs;
    } else {
      stepUs = 0;
    }
  
    timerIntervalUs = stepUs;
   
    meanSerialProcessingTimeUs = (meanSerialProcessingTimeUs + micros() - startOfSerialProcess) / 2;

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
  azimuthServo.attach(9,600,2300);  // (pin, min, max)

  Serial.println("Send Commands !");
}


void loop() {
  
  bool had_serial_input = processSerialInput();

  if (timerIntervalUs > 1) {

    byte delay_time = had_serial_input ? meanSerialProcessingTimeUs : 0;
    
    unsigned long interval_step = timerIntervalUs - delay_time;

    delayMicroseconds(interval_step);
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator;
  }

}
