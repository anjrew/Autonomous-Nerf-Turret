/*Example sketch to control a stepper motor with A4988 stepper motor driver and Arduino without a library. More info: https://www.makerguides.com */
#include <ArduinoJson.h>
#include <TimerOne.h>


// Define stepper motor connections and steps per revolution:
#define dirPin 2
#define stepPin 3
#define stepsPerRevolution 200


// Define the initial timer interval in microseconds. Start with max value
#define INITIAL_TIMER_INTERVAL 4294967295;

// Define a timer interval variable
unsigned long timerInterval = INITIAL_TIMER_INTERVAL;
 
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


StaticJsonDocument<512> processSerialInput() {
  int size_ = 0;
  String payload;

  if (Serial.available()) {
    payload = Serial.readStringUntil('\n');
  }

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload);

  if (error) {
//    Serial.println(error.c_str());
    return doc; // return an empty JSON document
  }

//  char buffer[100];
//  serializeJsonPretty(doc, buffer);
//  Serial.println("Received Motor config");
//  Serial.println(buffer);

  return doc;
}


// Define a timer interrupt handler function that will be called at the specified interval
void doHalfMotorStep() {
  Serial.print("Updating motor State with timer: ");
  
  Serial.print("Timer interval is: ");
  Serial.println(timerInterval);

  Serial.print("Direction: ");
  Serial.print(isClockwise);
  Serial.print(", RPM: ");
  Serial.print(rpm);
  Serial.print(", alternator: ");
  Serial.println(alternator);
  
  digitalWrite(stepPin, alternator ? LOW : HIGH);
  
}


void setup() {
  // Start serial for communication
  Serial.begin(9600);
  // Declare pins as output:
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  Serial.println("Send Commands !");

  // Set up the timer interrupt
  Timer1.initialize(timerInterval);  // set the initial timer interval
  Timer1.attachInterrupt(doHalfMotorStep);   // attach the interrupt handler function
}


void loop() {
//  Serial.println("Doing Loop");
  
  StaticJsonDocument<512> motorDetails = processSerialInput();

  if (motorDetails.containsKey("isClockwise")) {
    isClockwise = motorDetails["isClockwise"];
    if (isClockwise) {
      digitalWrite(dirPin, HIGH);
    }
    else {
      digitalWrite(dirPin, LOW);
    }
  }


  if (motorDetails.containsKey("rpm")) {
    
    rpm = motorDetails["rpm"];
    Serial.print("rpm: ");
    Serial.println(rpm);

    float revsPerSecond = rpm / 60.0f;
    Serial.print("revsPerSecond: ");
    Serial.println(revsPerSecond);

    float milliSecondsPerStep = (1/revsPerSecond) * 100000;
    Serial.print("milliSecondsPerStep: ");
    Serial.println(milliSecondsPerStep);
 
    // We divide the interval by 2 so that we can switch the motor from High to low within one step
    timerInterval = milliSecondsPerStep / 2;
    Serial.print("timerInterval: ");
    Serial.println(timerInterval);
    Timer1.setPeriod(timerInterval);
 
  }


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
////    timerInterval = random(500, 2000);
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
