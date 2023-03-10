#include <gtest/gtest.h>
#include "turret_control.h"
#include <stdint.h>
#include <iostream>


TEST(DecodeTest, Azimuth) {

    const uint8_t numOfCases = 3;

    uint8_t testBytes[numOfCases] = {
        0b00000000,
        0b10110100,
        0b01011010
    };

    int expected[numOfCases] = {
          -90,
          90,
          0
    };

    for (int i = 0; i < numOfCases; i++) {

      int testVal = testBytes[i];
      int expectedVal= expected[i];
      int resultVal= decodeAzimuth(testBytes[i]);
      std::cout << "\nTest  " << i << std::endl;
      std::cout << "The testVal is: " << testVal << std::endl;
      std::cout << "The expectedVal is: " << expectedVal << std::endl;
      std::cout << "The resultVal is: " << resultVal << std::endl;

      ASSERT_EQ( resultVal,  expectedVal);
    }  
}


TEST(DecodeTest, BaseValues) {
    const uint8_t numOfCases = 4;

    uint8_t testBytes[numOfCases] = {
        0b10000000,
        0b11000001,
        0b01001000,
        0b00000011
    };

    BaseTurretSettings expectedResults[numOfCases] = {
        { true, 0, false},
        { true, 1, true},
        { false, 8, true},
        { false, 3, false}
    };

    for (int i = 0; i < numOfCases; i++) {
        BaseTurretSettings vals = decodeValue(testBytes[i]);
        ASSERT_EQ(vals.isClockwise, expectedResults[i].isClockwise);
        ASSERT_EQ(vals.isFiring, expectedResults[i].isFiring);
        ASSERT_EQ(vals.speed, expectedResults[i].speed);
    }  
}

TEST(DecodeTest, AllValues) {
    const uint8_t numOfCases = 5;

    uint8_t testBytes[numOfCases][2] = {
        { 0b00000000, 0b10000000 },
        { 0b10110100, 0b11000001 },
        { 0b01011010, 0b01001000 },
        { 0b00000000, 0b01000011 },
        { 0b00000000, 0b10000011 }
    };


    TurretSettings expectedResults[numOfCases] = {
        {true , 0, false, -90 },
        {true , 1, true,  90  },
        {false, 8, true,  0   },
        {false, 3, true, -90 },
        {true, 3, false, -90 }
    };

    for (int i = 0; i < numOfCases; i++) {
        TurretSettings vals = decode(testBytes[i]);
        ASSERT_EQ(vals.azimuth, expectedResults[i].azimuth);
        ASSERT_EQ(vals.isClockwise, expectedResults[i].isClockwise);
        ASSERT_EQ(vals.isFiring, expectedResults[i].isFiring);
        ASSERT_EQ(vals.speed, expectedResults[i].speed);
    }  
}




TEST(MapRangeTest, MapsValueToMiddleOfOutputRange) {
    int input_value = 50;
    int min_value = 0;
    int max_value = 100;
    int new_min_value = 0;
    int new_max_value = 10;
    int expected_output = 5;

    EXPECT_EQ(mapRange(input_value, min_value, max_value, new_min_value, new_max_value), expected_output);
}

TEST(MapRangeTest, MapsValueToLowEndOfOutputRange) {
    int input_value = 0;
    int min_value = 0;
    int max_value = 100;
    int new_min_value = 0;
    int new_max_value = 10;
    int expected_output = 0;

    EXPECT_EQ(mapRange(input_value, min_value, max_value, new_min_value, new_max_value), expected_output);
}

TEST(MapRangeTest, MapsValueToHighEndOfOutputRange) {
    int input_value = 100;
    int min_value = 0;
    int max_value = 100;
    int new_min_value = 0;
    int new_max_value = 10;
    int expected_output = 10;

    EXPECT_EQ(mapRange(input_value, min_value, max_value, new_min_value, new_max_value), expected_output);
}

TEST(MapRangeTest, MapsNegativeValueToOutputRange) {
    int input_value = -90;
    int min_value = -90;
    int max_value = 90;
    int new_min_value = 0;
    int new_max_value = 180;
    int expected_output = 0;

    EXPECT_EQ(mapRange(input_value, min_value, max_value, new_min_value, new_max_value), expected_output);
}

TEST(MapRangeTest, MapsValueToOutputRange) {
    int input_value = 90;
    int min_value = -90;
    int max_value = 90;
    int new_min_value = 0;
    int new_max_value = 180;
    int expected_output = 180;

    EXPECT_EQ(mapRange(input_value, min_value, max_value, new_min_value, new_max_value), expected_output);
}

TEST(MapRangeTest, MapsValueOutsideInputRangeToOutputRange) {
    int input_value = 1000;
    int min_value = 0;
    int max_value = 100;
    int new_min_value = 0;
    int new_max_value = 10;
    int expected_output = 10;

    EXPECT_THROW(mapRange(input_value, min_value, max_value, new_min_value, new_max_value), std::invalid_argument);
}

TEST(MapRangeTest, MapsValueOutsideInputRangeToLowEndOfOutputRange) {
    int input_value = 0;
    int min_value = 1000;
    int max_value = 0;
    int new_min_value = 0;
    int new_max_value = 10;
    int expected_output = 10;

    EXPECT_EQ(mapRange(input_value, min_value, max_value, new_min_value, new_max_value), expected_output);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
   

    

    