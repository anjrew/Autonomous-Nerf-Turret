/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <ArduinoJson.h>
#include <TimerOne.h>


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


  if (doc.containsKey("rpm")) {
    
    rpm = doc["rpm"];
    Serial.print("rpm: ");
    Serial.println(rpm);

    float revsPerSecond = rpm / 60.0f;
    Serial.print("revsPerSecond: ");
    Serial.println(revsPerSecond);

    float milliSecondsPerStep = (1/revsPerSecond);
    Serial.print("milliSecondsPerStep: ");
    Serial.println(milliSecondsPerStep);
 
    // We divide the interval by 2 so that we can switch the motor from High to low within one step
    timerIntervalUs = milliSecondsPerStep / 2;
    Serial.print("timerIntervalUs: ");
    Serial.println(timerIntervalUs);
    Timer1.setPeriod(timerIntervalUs);
 
  }

  if (doc.containsKey("stepUs")) {
    
    stepUs = doc["stepUs"];
    Serial.print("stepUs: ");
    Serial.println(stepUs);

    timerIntervalUs = stepUs;
 
  }
  meanSerialProcessingTimeUs = (meanSerialProcessingTimeUs + micros() - startOfSerialProcess) / 2;
  Serial.print("Time taken to process Serial(us): ");
  Serial.println( millis() - startOfSerialProcess);
  Serial.print("meanSerialProcessingTimeUs(us): ");
  Serial.println(meanSerialProcessingTimeUs);
  
  return true;
}


// Define a timer interrupt handler function that will be called at the specified interval
void doHalfMotorStep() {
//  unsigned long start_of_half_step_process = millis();
//  Serial.print("Updating motor State with timer: ");
//  
//  Serial.print("Timer interval is: ");
//  Serial.println(timerIntervalUs);
//
//  Serial.print("Direction: ");
//  Serial.print(isClockwise);
//  
//  Serial.print(", RPM: ");
//  Serial.print(rpm);
//  
//  Serial.print(", alternator: ");
//  Serial.println(alternator);
//  
//  digitalWrite(stepPin, alternator ? HIGH : LOW );
//  alternator = !alternator;
//
//  meanHalfStepProcessingTimeUs = (meanHalfStepProcessingTimeUs + (millis() - start_of_half_step_process)) / 2;
//  Serial.print("Time taken to process Serial(ms): ");
//  Serial.println(millis() - start_of_half_step_process);
  
}


void setup() {
  // Start serial for communication
  Serial.begin(9600);
  // Declare pins as output:
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  Serial.println("Send Commands !");

  // Set up the timer interrupt
//  Timer1.initialize(timerIntervalUs);  // set the initial timer interval
//  Timer1.attachInterrupt(doHalfMotorStep);   // attach the interrupt handler function
}


void loop() {
//  Serial.println("Doing Loop");
  
  bool had_serial_input = processSerialInput();

  if (rpm > 1 || stepUs > 1) {

    byte delay_time = had_serial_input ? meanSerialProcessingTimeUs : 0;
    
    unsigned long interval_step = timerIntervalUs - delay_time;
//    Serial.print("mean_serial_processing_time_ms(ms): ");
//    Serial.println(mean_serial_processing_time_ms);
//    Serial.print("timerIntervalUs: ");
//    Serial.println(timerIntervalUs);
//    Serial.print("interval_step: ");
//    Serial.println(interval_step);
    delayMicroseconds(interval_step);
    digitalWrite(stepPin, alternator ? HIGH : LOW );
    alternator = !alternator;
  }
//  doHalfMotorStep();
//  // Check if the timer has fired
//  if (timerCounter > 0) {
//    // Do something when the timer has fired
//    Serial.println("Timer fired!");
//    digitalWrite(stepPin, HIGH);
//    digitalWrite(stepPin, LOW);
//    // Reset the timer counter
//    timerCounter = 0;
//
//    // Change the timer interval to a new value
////    timerIntervalUs = random(500, 2000);
//    
//  }



 
//  delayMicroseconds(2000);;

//  // Spin the stepper motor 1 revolution slowly:
//  for (int i = 0; i < stepsPerRevolution; i++) {
//    // These four lines result in 1 step:
//    digitalWrite(stepPin, HIGH);
//    delayMicroseconds(2000);
//    digitalWrite(stepPin, LOW);
//    delayMicroseconds(2000);
//  }
//
//  delay(1000);
//
//  // Set the spinning direction counterclockwise:
//  digitalWrite(dirPin, LOW);
//
//  // Spin the stepper motor 1 revolution quickly:
//  for (int i = 0; i < stepsPerRevolution; i++) {
//    // These four lines result in 1 step:
//    digitalWrite(stepPin, HIGH);
//    delayMicroseconds(1000);
//    digitalWrite(stepPin, LOW);
//    delayMicroseconds(1000);
//  }
//
//  delay(1000);
//
//  // Set the spinning direction clockwise:
//  digitalWrite(dirPin, HIGH);
//
//  // Spin the stepper motor 5 revolutions fast:
//  for (int i = 0; i < 5 * stepsPerRevolution; i++) {
//    // These four lines result in 1 step:
//    digitalWrite(stepPin, HIGH);
//    delayMicroseconds(500);
//    digitalWrite(stepPin, LOW);
//    delayMicroseconds(500);
//  }
//
//  delay(1000);
//
//  // Set the spinning direction counterclockwise:
//  digitalWrite(dirPin, LOW);
//
//  //Spin the stepper motor 5 revolutions fast:
//  for (int i = 0; i < 5 * stepsPerRevolution; i++) {
//    // These four lines result in 1 step:
//    digitalWrite(stepPin, HIGH);
//    delayMicroseconds(500);
//    digitalWrite(stepPin, LOW);
//    delayMicroseconds(500);
//  }
//
}
