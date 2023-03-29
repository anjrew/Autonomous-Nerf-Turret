/*
     Servo Motor Control using the Arduino Servo Library
           by Dejan, https://howtomechatronics.com
*/

#include <Servo.h>

Servo azimuthServo;  // create servo object to control a servo

void setup() {
  azimuthServo.attach(9,600,2300);  // (pin, min, max)
}

void loop() {
  azimuthServo.write(0);  // tell servo to go to a particular angle
  delay(3000);
  
  azimuthServo.write(90);              
  delay(3000); 
  
  azimuthServo.write(135);              
  delay(3000);
  
  azimuthServo.write(180);              
  delay(3000);

}
