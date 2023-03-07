/*
     Servo Motor Control - 50Hz Pulse Train Generator
           by Dejan, https://howtomechatronics.com
*/

#define servoPin 9

void setup() {
  pinMode(servoPin, OUTPUT);
}

void loop() {
   // A pulse each 20ms
    digitalWrite(servoPin, HIGH);
    delayMicroseconds(1450); // Duration of the pusle in microseconds
    digitalWrite(servoPin, LOW);
    delayMicroseconds(18550); // 20ms - duration of the pusle
    // Pulses duration: 600 - 0deg; 1450 - 90deg; 2300 - 180deg
}