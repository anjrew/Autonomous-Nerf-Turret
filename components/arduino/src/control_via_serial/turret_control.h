#include <stdint.h>
//#include <stdexcept>




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

/** TODO: implement inheritance
 * TurretSettings struct extends the BaseTurretSettings struct to include azimuth.
 *
 * @param isClockwise A boolean indicating the direction of the turret. True means clockwise, False means anti-clockwise.
 * @param speed The speed of the turret.
 * @param isFiring A boolean indicating whether the turret is firing.
 * @param azimuth The azimuth angle for the turret.
 */
struct TurretSettings {
    bool isClockwise;
    int speed;
    bool isFiring;
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


TurretSettings decode(uint8_t *encoded_command) {
    TurretSettings turretCommand;
    turretCommand.azimuth = decodeAzimuth(encoded_command[0]);
    BaseTurretSettings encodedValue = decodeValue(encoded_command[1]);
    turretCommand.isClockwise =encodedValue.isClockwise;
    turretCommand.speed =encodedValue.speed;
    turretCommand.isFiring =encodedValue.isFiring;
    return turretCommand;
}


int mapRange(int value, int value_min, int value_max, int new_min_value, int new_max_value) {
//    int max_value = std::max(value_min, value_max);
//    int min_value = std::min(value_min, value_max);
    int max_value = max(value_min, value_max);
    int min_value = min(value_min, value_max);
    
    if (value < min_value || value > max_value) {
        // throw std::invalid_argument("The given value must be within the value_min and value_max range");;
        static_assert("The given value must be within the value_min and value_max range");
    } 

    int original_range = value_max - value_min;
    int new_range = new_max_value - new_min_value;
    float scaling_factor = static_cast<float>(original_range) / static_cast<float>(new_range);
    int place_in_original_range = value - value_min;
    int scaled = static_cast<int>(place_in_original_range / scaling_factor);
    int mapped_value = scaled + new_min_value;

    return mapped_value;
}
