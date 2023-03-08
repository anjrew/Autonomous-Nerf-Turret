/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <ArduinoJson.h>
#include <Servo.h>

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

struct MotorSettings {
    int azimuth;
    bool isClockwise;
    int speed;
    bool isFiring;
};

MotorSettings decode(byte *encoded_command) {
    MotorSettings motor_command;
    
    byte encoded_value = encoded_command[0];
    motor_command.isClockwise = (encoded_value & 0x80) >> 7;; // Get the 8th bit for clockwise
    motor_command.speed = encoded_value & 0x0F; // Mask the lower 4 bits for speed
    motor_command.isFiring = (encoded_value >> 2) & 1; // Get the 3rd bit for is_firing
    
    byte azimuth_byte = encoded_command[1];
    motor_command.azimuth = round((azimuth_byte / 255.0) * 180.0); // Scale the azimuth byte back to 0-180
    return motor_command;
}


int map_range(int value = 0, int min_value = SLOWEST_HALF_STEP_MICROSECONDS, int max_value = FASTEST_HALF_STEP_MICROSECONDS, int new_min_value = SLOWEST_SPEED, int new_max_value = FASTEST_SPEED) {
    
    int new_range = new_max_value - new_min_value;

    int original_range = max_value - min_value;

    float scaling_factor = (float)original_range / new_range;

    float original_value = ((value - new_min_value) * scaling_factor) + min_value;

    return int(original_value);
}


bool processSerialInput() {
  
  // Read the encoded motor command from serial input
  byte encodedValue[2];
  
  if (Serial.available() >= 2) {
    unsigned long startOfSerialProcess = micros();
    encodedValue[0] = Serial.read();
    encodedValue[1] = Serial.read();
    
    // Decode the motor command
    
    MotorSettings decodedValues = decode(encodedValue);
    int speed_in = decodedValues.speed;
    int stepUs = map_range(speed_in);
    azimuthServo.write(decodedValues.azimuth);
    digitalWrite(dirPin, decodedValues.isClockwise ? LOW : HIGH);

    digitalWrite(shootPin, decodedValues.isFiring ? HIGH: LOW);   

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
  azimuthServo.attach(azimuthServoPin ,600,2300);  // (pin, min, max)

  // Setup pin to shoot
  pinMode(shootPin, OUTPUT);

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
