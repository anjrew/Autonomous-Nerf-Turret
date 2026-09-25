// Parametric NEMA 17 (17HS4023) stepper motor front plate / holder
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Front plate] */
// Plate size (square): just big enough for the cradle plus corner holes
plate_size      = 60.0;
// Plate thickness
plate_thickness = 2.0;
// Corner mounting screw holes (M3 clearance)
corner_hole_dia   = 3.4;
corner_hole_inset = 4.0;

/* [Motor cutout] */
// NEMA 17 bolt hole spacing
bolt_spacing = 31.0;
// Motor bolt hole diameter (M3 clearance)
bolt_dia     = 3.4;
// Centring boss clearance
boss_dia     = 22.5;
// Shaft clearance
shaft_dia    = 8.0;
// Motor face size (17HS4023 is 42.3 mm)
motor_face   = 42.3;

/* [Body cradle] */
// Add a three-sided cradle to hold the motor body
include_cradle = true;
// Cradle wall height
wall_height    = 18.0;
// Cradle wall thickness
wall_thickness = 2.0;
// Motor body length (measured: 32 mm deep)
motor_length   = 32.0;

/* [Quality] */
$fn = 64;

module front_plate() {
    difference() {
        cube([plate_size, plate_size, plate_thickness], center = true);

        // Corner mounting holes
        for (x = [-1, 1], y = [-1, 1]) {
            translate([x * (plate_size / 2 - corner_hole_inset),
                       y * (plate_size / 2 - corner_hole_inset), 0])
                cylinder(d = corner_hole_dia, h = plate_thickness + 2, center = true);
        }

        // Stepper cutout: bolt pattern, boss and shaft clearance
        for (x = [-1, 1], y = [-1, 1]) {
            translate([x * bolt_spacing / 2, y * bolt_spacing / 2, 0])
                cylinder(d = bolt_dia, h = plate_thickness + 2, center = true);
        }
        cylinder(d = boss_dia, h = plate_thickness + 2, center = true);
        cylinder(d = shaft_dia, h = plate_thickness + 2, center = true);
    }
}

module motor_cradle() {
    if (include_cradle) {
        // Cradle extends behind the plate to hold the motor body.
        translate([0, 0, -plate_thickness / 2 - motor_length / 2]) {
            difference() {
                cube([motor_face + 2 * wall_thickness,
                      motor_face + 2 * wall_thickness,
                      motor_length], center = true);
                // Motor cavity
                cube([motor_face + 0.6, motor_face + 0.6, motor_length + 2], center = true);
                // Wiring exit slot in the back wall
                translate([0, (motor_face + 0.6) / 2, 0])
                    cube([16, wall_thickness + 2, 20], center = true);
            }
        }
    }
}

module stepper_holder() {
    front_plate();
    motor_cradle();
}

stepper_holder();
