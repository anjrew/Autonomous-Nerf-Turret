// Parametric NEMA 17 (17HS4023) stepper motor front plate / holder
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Front plate] */
// Plate size (square): just big enough for the cradle plus corner holes
plate_size      = 60.0;
// Plate thickness
plate_thickness = 2.0;
// Corner chamfer flat length on the base plate
plate_corner_flat = 8.0;
// Corner mounting screw holes (M3 clearance)
corner_hole_dia   = 3.4;
corner_hole_inset = 8.0;

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
// Length of the flat on each tapered corner (motor is octagonal)
corner_flat  = 6.0;

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
        // Chamfered plate corners to match the rest of the holder
        octagon_prism(plate_thickness, plate_size, plate_corner_flat);

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

module octagon_prism(height, across_flats, flat) {
    // Square across flats with 45 degree corner cuts leaving `flat`,
    // used for both the motor cavity and the cradle's outer corners.
    half = across_flats / 2;
    cut = flat / sqrt(2);
    linear_extrude(height = height, center = true)
        polygon(points = [
            [ half,        half - cut],
            [ half - cut,  half],
            [-(half - cut), half],
            [-half,        half - cut],
            [-half,       -(half - cut)],
            [-(half - cut), -half],
            [ half - cut,  -half],
            [ half,       -(half - cut)],
        ]);
}

module motor_cradle() {
    if (include_cradle) {
        // Cradle extends behind the plate to hold the motor body.
        translate([0, 0, -plate_thickness / 2 - motor_length / 2]) {
            difference() {
                // Outer shell with the same chamfered corner profile
                octagon_prism(motor_length,
                              motor_face + 2 * wall_thickness,
                              corner_flat);
                // Motor cavity (octagonal, matches the tapered corners)
                octagon_prism(motor_length + 2, motor_face + 0.6, corner_flat);
                // Wiring exit slot: 8 mm wide, from 2 mm to 10 mm off the back
                translate([0, -(motor_face + 0.6) / 2, -motor_length / 2 + 6])
                    cube([8, wall_thickness + 6, 8], center = true);
            }
        }
    }
}

module stepper_holder() {
    front_plate();
    motor_cradle();
}

stepper_holder();
