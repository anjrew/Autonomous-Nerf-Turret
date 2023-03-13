# Stepper control notes

- Pulsing the **step** pin on the stepper motor driver will cause the motor to move one step
- The longer the time between pulses the slower the step will take place
- Change the direction pin between high/low to change direction of the spin to clockwise vs anti clockwise

# Key notes
- Input voltage is set to 12.5v

## Setup 

Before you start programming your Arduino and start using the driver there is one very important thing you need to do that a lot of people forget: set the current limit!

You must measure a reference voltage and adjust the on-board potentiometer accordingly. You will need a small screwdriver, a multimeter to measure the reference voltage, and alligator test leads

![Image of how to do it](https://www.makerguides.com/wp-content/uploads/2019/02/A4988-current-limit-wiring-diagram-schematic-e1560009202882.png)

To measure the reference voltage, the driver needs to be powered. The A4988 only needs power via VDD (5V) and you need to connect RST and SLP together, otherwise the driver won’t turn on. It’s best to disconnect the stepper motor while you do this.

The next step is to calculate the current limit with the following formula: **Current Limit = Vref / (8 × Rcs)**

Refactored to get the Vref this is **Vref = Current Limit * (8 × Rcs)**

The Rcs is the current sense resistance. If you bought a A4988 driver from Pololu before January 2017, the Rcs will be 0.050 Ω. Drivers sold after that have 0.068 Ω current sense resistors.

The calculation for the Vref that was acquired on the first time was:
Vref = 0.380 = 0.7A * (8 * 0.068)


## Communication over serial

A raw none stringified JSON string can be sent over serial and be received by the Arduino with optional direction and speed properties.


## Calculating RPM value

The motor here has 200 steps in one revolution
So 200 steps per second would equal 60 RPM

So time per step in seconds = 60 * steps_per_revolution



## Key points

Here are some key points after testing the motor at different half step speeds

- The slowest the motor can go is 16000us between each half step
  - That means that the slowest the motor can do one step is 32000us
  - So 32000us x 200 Steps for one revolution is 6400000us
  - That means that it does one revolution in 6.4 seconds at min speed
  - Max Revolutions per minute = 60 seconds/0.16 seconds = 375 revolutions per minute (RPM)
  - Min Revolutions per minute = 60 seconds/6.4 seconds = 9.375 revolutions per minute (RPM)

- The fastest the motor can go is 400us between each half step
  - That means that the fastest the motor can do one step is 800us
  - So 800us x 200 Steps for one revolution is 160000us
  - That means that it does one revolution in 0.16 seconds at max speed
  - Max Revolutions per minute = 60 seconds/0.16 seconds = 375 revolutions per minute (RPM)

- In summery the min/max RPM is ~9rpm/375rpm 

## Sources of information
 - See the [Documentation folder](./documentation/)
 - For info on the 2N3904 Resistor see [this](https://www.homemade-circuits.com/understanding-transistor-2n3904/) link
 - [Servo Motor](https://www.amazon.de/dp/B09WRBHSVD?ref=ppx_yo2ov_dt_b_product_details&th=1) for azimuth 
 - [LM2596 Buck Converter](https://www.amazon.de/Yizhet-LM2596-Buck-Converter-3-0/dp/B0823P6PW6/ref=sr_1_1_sspa?crid=NU4899MSJCM5&keywords=buck%2Bwandler%2B12v%2Bauf%2B6v&qid=1678690421&refinements=p_85%3A20943776031%2Cp_72%3A419117031&rnid=419116031&rps=1&sprefix=buck%2Bconverter%2B12v%2Bto%2B6v%2Caps%2C105&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1)