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


int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
   

    

    