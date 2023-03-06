/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <ArduinoJson.h>



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

// The limits of the values to be set for the motor half step
const int slowestHalfStepUs = 16000;
const int quickestHalfStepUs = 400;

/*
* Holds the value of the direction of the motor
* false = Anti clockwise
* true = Clockwise
*/
bool isClockwise = false;

/*
 * Alternates the PIN from HIGH to LOW on each half step
*/
bool alternator = false;

/*
* Holds the value of the speed of the motor in RPM
*/
byte rpm = 0;

const int SLOWEST_HALF_STEP_MICROSECONDS = 17000;
const int FASTEST_HALF_STEP_MICROSECONDS = 400;

const byte SLOWEST_SPEED = 0;
const byte FASTEST_SPEED = 10;

class MotorSettings {
public:
  MotorSettings(bool clockwise, int speed) : isClockwise(clockwise), speed(speed) {}
  bool isClockwise;
  int speed;
};

MotorSettings decode(uint8_t encodedValue) {
  bool isClockwise = (encodedValue >> 7) & 1; // Extract the 8th bit for clockwise
  int speed = encodedValue & 0x0F; // Extract the lower 4 bits for speed (0-10)
  return MotorSettings(isClockwise, speed);
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
    unsigned long startOfSerialProcess = micros();
    
     // Read the encoded value from the serial port
    uint8_t encodedValue = Serial.read();
    
    MotorSettings decodedValues = decode(encodedValue);
    bool isClockwise = decodedValues.isClockwise;
    int speed_in = decodedValues.speed;
    int stepUs = map_range(speed_in);

    if (isClockwise) {
        digitalWrite(dirPin, HIGH);
    }
    else {
      digitalWrite(dirPin, LOW);
    }
      
    if (stepUs <= slowestHalfStepUs && stepUs >= quickestHalfStepUs) {
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
