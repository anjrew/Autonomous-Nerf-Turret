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
 * Alternates the PIN from HIGH to LOW on each half step
*/
unsigned long stepUs = 0;

/*
* Holds the value of the speed of the motor in RPM
*/
byte rpm = 0;


bool processSerialInput() {
  unsigned long startOfSerialProcess = micros();
  
  int size_ = 0;
  String payload;

  if (Serial.available()) {
    payload = Serial.readStringUntil('\n');
  }

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload);

  if (error) {
//    Serial.println(error.c_str());
    return false; // return an empty JSON document
  }

// // Print out json
//  char buffer[100];
//  serializeJsonPretty(doc, buffer);
//  Serial.println("Received Motor config");
//  Serial.println(buffer);

  if (doc.containsKey("isClockwise")) {
    isClockwise = doc["isClockwise"];
    if (isClockwise) {
      digitalWrite(dirPin, HIGH);
    }
    else {
      digitalWrite(dirPin, LOW);
    }
  }


  if (doc.containsKey("stepUs")) {

    
    if (doc["stepUs"] <= slowestHalfStepUs && doc["stepUs"] >= quickestHalfStepUs) {
      stepUs = doc["stepUs"];
    } else {
      stepUs = 0;
    }
//    
//    Serial.print("stepUs: ");
//    Serial.println(stepUs);

    timerIntervalUs = stepUs;
 
  }
  meanSerialProcessingTimeUs = (meanSerialProcessingTimeUs + micros() - startOfSerialProcess) / 2;
//  Serial.print("Time taken to process Serial(us): ");
//  Serial.println( millis() - startOfSerialProcess);
//  Serial.print("meanSerialProcessingTimeUs(us): ");
//  Serial.println(meanSerialProcessingTimeUs);
  
  return true;
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

  if (rpm > 1 || stepUs > 1) {

    byte delay_time = had_serial_input ? meanSerialProcessingTimeUs : 0;
    
    unsigned long interval_step = timerIntervalUs - delay_time;

    delayMicroseconds(interval_step);
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator;
  }

}
