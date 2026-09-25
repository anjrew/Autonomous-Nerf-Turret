// Parametric NEMA 17 (17HS4023) stepper motor holder / bracket
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Motor] */
// NEMA 17 face size (square)
motor_face        = 42.3;   // 17HS4023 is 42.3 mm
// Bolt hole spacing (NEMA 17 standard)
bolt_spacing      = 31.0;
// Bolt hole diameter (M3 clearance)
bolt_dia          = 3.4;
// Centring boss diameter (clearance)
boss_dia          = 22.5;
// Shaft hole diameter
shaft_dia         = 8.0;    // generous clearance around the 5 mm shaft + hub
// Motor body length (for the cradle depth)
motor_length      = 40.0;

/* [Holder] */
// Plate thickness
plate_thickness   = 5.0;
// Plate size (square) - set larger than the motor face
plate_size        = 60.0;
// Side wall height (cradle holding the motor body)
wall_height       = 18.0;
// Wall thickness
wall_thickness    = 4.0;
// Mounting flange width (each side) and length
flange_width      = 14.0;
flange_length     = 24.0;
// Flange screw holes (M3)
flange_hole_dia   = 3.4;
flange_hole_inset = 8.0;

/* [Quality] */
$fn = 64;

module nema17_face_plate() {
    difference() {
        cube([plate_size, plate_size, plate_thickness], center = true);

        // Bolt holes
        for (x = [-1, 1], y = [-1, 1]) {
            translate([x * bolt_spacing / 2, y * bolt_spacing / 2, 0])
                cylinder(d = bolt_dia, h = plate_thickness + 2, center = true);
        }

        // Central boss / shaft clearance
        cylinder(d = boss_dia, h = plate_thickness + 2, center = true);
        // Shaft path through the boss opening
        cylinder(d = shaft_dia, h = plate_thickness + 2, center = true);
    }
}

module motor_cradle() {
    // Three-sided cradle around the motor body (open on the shaft side)
    difference() {
        translate([0, 0, plate_thickness / 2 + wall_height / 2]) {
            difference() {
                cube([plate_size, plate_size, wall_height], center = true);
                // Inner cavity
                translate([0, 0, 0])
                    cube([motor_face + 0.6, motor_face + 0.6, wall_height + 2], center = true);
                // Open the top so the motor can drop in
                translate([0, 0, wall_height / 2 + 1])
                    cube([plate_size + 2, plate_size + 2, 2], center = true);
                // Open the back so wires can exit
                translate([0, -(motor_face + 0.6) / 2 - 1, 0])
                    cube([14, 4, wall_height + 2], center = true);
            }
        }
    }
}

module flange(side = 1) {
    // side = -1 left, +1 right
    translate([side * (plate_size / 2 + flange_length / 2 - 2), 0, 0]) {
        difference() {
            cube([flange_length, flange_width, plate_thickness], center = true);
            // Screw hole (through the flange) plus a slot opening to the edge
            translate([0, 0, 0])
                cylinder(d = flange_hole_dia, h = plate_thickness + 2, center = true);
            translate([side * (flange_length / 2), 0, 0])
                cube([flange_length, flange_hole_dia, plate_thickness + 2], center = true);
        }
    }
}

module stepper_holder() {
    nema17_face_plate();
    motor_cradle();
    flange(-1);
    flange(1);
}

stepper_holder();
