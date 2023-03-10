#include <stdint.h>


#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H


/**
 * BaseTurretSettings struct represents the base settings for a turret
 *
 * @param isClockwise A boolean indicating the direction of the elevation turret. True means clockwise, False means anti-clockwise.
 * @param speed The speed of the elevation turret.
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
 * @param isClockwise A boolean indicating the direction of the turret. True means clockwise, False means anti-clockwise.
 * @param speed The speed of the turret.
 * @param isFiring A boolean indicating whether the turret is firing.
 * @param azimuth The azimuth angle for the turret.
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
 * Decode the turret settings from the encoded command uint8_t.
 *
 * @param encoded_command The encoded command uint8_t.
 * @returns The decoded turret settings.
 */
BaseTurretSettings decodeValue(uint8_t encoded_command) {
    BaseTurretSettings settings; 
    settings.isClockwise = bool((encoded_command & 0b10000000) >> 7); // Get the 8th bit for clockwise
    settings.isFiring = bool((encoded_command & 0b01000000) >> 6);  // Check the 7th bit for is_firing
    settings.speed = (encoded_command & 0b00001111); // Mask the lower 4 bits for speed
    return settings;
}


int mapRange(int value, int value_min, int value_max, int new_min_value, int new_max_value) {
    int max_value = std::max(value_min, value_max);
    int min_value = std::min(value_min, value_max);

    if (value < min_value || value > max_value) {
        throw std::invalid_argument("The given value must be within the value_min and value_max range");;
    } 

    int original_range = value_max - value_min;
    int new_range = new_max_value - new_min_value;
    float scaling_factor = static_cast<float>(original_range) / static_cast<float>(new_range);
    int place_in_original_range = value - value_min;
    int scaled = static_cast<int>(place_in_original_range / scaling_factor);
    int mapped_value = scaled + new_min_value;

    return mapped_value;
}


TurretSettings decode(uint8_t *encoded_command) {
    TurretSettings turret_command;
    
    uint8_t encoded_value = encoded_command[0];
    // Serial.print("encoded_value: ");
    // Serial.print(encoded_value, BIN);
    turret_command.isClockwise = bool((encoded_value & 0b10000000) >> 7); // Get the 8th bit for clockwise
    turret_command.isFiring = bool((encoded_value & 0b01000000) >> 6);  // Check the 7th bit for is_firing
    turret_command.speed = (encoded_value & 0b00001111); // Mask the lower 4 bits for speed
    // Serial.print(" - speed decoder: ");
    // Serial.print(turret_command.speed);
  
    
    // Serial.print(" - isFiring  ");
    // Serial.print(turret_command.isFiring);
    
    uint8_t azimuth_uint8_t = encoded_command[1];
    turret_command.azimuth =(encoded_command[1] & 0b11111111) - 90; // Scale the azimuth uint8_t back to 0-180
    // Serial.print(" - azimuth  ");
    // Serial.print(turret_command.azimuth);
    return turret_command;
}

#endif
