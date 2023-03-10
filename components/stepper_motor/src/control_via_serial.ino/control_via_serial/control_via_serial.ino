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

int azimuth_angle_deg = 90;


// The limits of the values to be set for the motor half step
const int SLOWEST_HALF_STEP_MICROSECONDS = 17000;
const int FASTEST_HALF_STEP_MICROSECONDS = 1000;
const int SLOWEST_STEP_SPEED = 1e6; // one second  in milli seconds which is achived by making 1 step at slowest possible seed and then waiting until 1 second has passed

// We use the slowest speed allows minus fastest speed possible in the motor
// Not the slowest speed here is slower than the slowest step speed because we can quickly step and then wait.
// 1e6 is a million micro seconds which is 1 second
const int STEP_MICRO_SECONDS_RANGE = SLOWEST_STEP_SPEED - FASTEST_HALF_STEP_MICROSECONDS;


const byte SLOWEST_SPEED = 0;
const byte FASTEST_SPEED = 10;
// The speed range that is expected to come from the serial message
const byte ORDINAL_SPEED_RANGE = FASTEST_SPEED - SLOWEST_SPEED;

const byte MAX_AZIMUTH_DEG_RANGE= 180;

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
    Serial.print("The speed obatined from the decoder is: ");
    Serial.println(motor_command.speed);
    motor_command.isFiring = (encoded_value >> 2) & 1; // Get the 3rd bit for is_firing
    
    byte azimuth_byte = encoded_command[1];
    motor_command.azimuth = round((azimuth_byte / 255.0) * MAX_AZIMUTH_DEG_RANGE) - 90; // Scale the azimuth byte back to 0-180
    return motor_command;
}


int map_range(int value = 0) {

    float scaling_factor = (float)ORDINAL_SPEED_RANGE / (float)STEP_MICRO_SECONDS_RANGE;

    float original_value = ((float)(value - SLOWEST_SPEED) * scaling_factor) + SLOWEST_STEP_SPEED;
    int val = int(original_value);
    Serial.print("Returning mapped: ");
    Serial.print(val);
    Serial.print(" FROM ");
    Serial.println(value) ;
    return val;
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

    int newAzimuth = azimuth_angle_deg +  decodedValues.azimuth;
    if (newAzimuth >= 0 && newAzimuth <= MAX_AZIMUTH_DEG_RANGE) {
      azimuthServo.write(newAzimuth);
      azimuth_angle_deg = newAzimuth;
    }
    
    digitalWrite(dirPin, decodedValues.isClockwise ? LOW : HIGH);

    digitalWrite(shootPin, decodedValues.isFiring ? HIGH: LOW);   

    timerIntervalUs = stepUs < FASTEST_HALF_STEP_MICROSECONDS ? FASTEST_HALF_STEP_MICROSECONDS : stepUs;
   
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
  byte delay_time = had_serial_input ? meanSerialProcessingTimeUs : 0;
  Serial.print("timerIntervalUs " );
  Serial.println(timerIntervalUs );
  // Use this logic if the value is slower than the stepper motor can handle
  if (timerIntervalUs > SLOWEST_HALF_STEP_MICROSECONDS) {
    Serial.println('s');
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator;
    delayMicroseconds(SLOWEST_HALF_STEP_MICROSECONDS);
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator; 
    int secondWaitTime = timerIntervalUs - SLOWEST_HALF_STEP_MICROSECONDS - delay_time;
    delayMicroseconds(secondWaitTime);
     
  } else if (timerIntervalUs > 1) {
    Serial.println('g');
    unsigned long interval_step = timerIntervalUs - delay_time;

    delayMicroseconds(interval_step);
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator;
  } else {
     Serial.println('x');
  }

}
