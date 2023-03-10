#include <stdint.h>


#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H


/**
 * BaseTurretSettings struct represents the base settings for a motor
 *
 * @param isClockwise A boolean indicating the direction of the elevation motor. True means clockwise, False means anti-clockwise.
 * @param speed The speed of the elevation motor.
 * @param isFiring A boolean indicating whether the gun is firing.
 */
struct BaseTurretSettings {
    bool isClockwise;
    int speed;
    bool isFiring;
}; 

/**
 * TurretSettings struct extends the BaseTurretSettings struct to include azimuth.
 *
 * @param isClockwise A boolean indicating the direction of the motor. True means clockwise, False means anti-clockwise.
 * @param speed The speed of the motor.
 * @param isFiring A boolean indicating whether the motor is firing.
 * @param azimuth The azimuth angle for the motor.
 */
struct TurretSettings:BaseTurretSettings {
    int azimuth;
};

/**
 * Decode the azimuth value from the encoded command uint8_t.
 *
 * @param encoded_command The encoded command uint8_t.
 * @returns The decoded azimuth value.
 */
int decodeAzimuth(uint8_t encoded_value) {
    return encoded_value - 90;
}

/**
 * Decode the motor settings from the encoded command uint8_t.
 *
 * @param encoded_command The encoded command uint8_t.
 * @returns The decoded motor settings.
 */
BaseTurretSettings decodeValue(uint8_t encoded_command) {
    BaseTurretSettings settings; 
    settings.isClockwise = bool((encoded_command & 0b10000000) >> 7); // Get the 8th bit for clockwise
    settings.isFiring = bool((encoded_command & 0b01000000) >> 6);  // Check the 7th bit for is_firing
    settings.speed = (encoded_command & 0b00001111); // Mask the lower 4 bits for speed
    return settings;
}


int mapRange(int value, int valRange, int newRange, int minVal, int minNewVal) {

   float scaling_factor = (float)valRange / (float)newRange;

   float original_value = ((float)(value - minVal) * scaling_factor) + minNewVal;
   int val = int(original_value);

   return val;
}


TurretSettings decode(uint8_t *encoded_command) {
    TurretSettings motor_command;
    
    uint8_t encoded_value = encoded_command[0];
    // Serial.print("encoded_value: ");
    // Serial.print(encoded_value, BIN);
    motor_command.isClockwise = bool((encoded_value & 0b10000000) >> 7); // Get the 8th bit for clockwise
    motor_command.isFiring = bool((encoded_value & 0b01000000) >> 6);  // Check the 7th bit for is_firing
    motor_command.speed = (encoded_value & 0b00001111); // Mask the lower 4 bits for speed
    // Serial.print(" - speed decoder: ");
    // Serial.print(motor_command.speed);
  
    
    // Serial.print(" - isFiring  ");
    // Serial.print(motor_command.isFiring);
    
    uint8_t azimuth_uint8_t = encoded_command[1];
    motor_command.azimuth =(encoded_command[1] & 0b11111111) - 90; // Scale the azimuth uint8_t back to 0-180
    // Serial.print(" - azimuth  ");
    // Serial.print(motor_command.azimuth);
    return motor_command;
}

#endif
