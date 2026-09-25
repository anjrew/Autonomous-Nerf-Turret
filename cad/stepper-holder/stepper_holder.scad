// Parametric NEMA 17 stepper motor holder (two end plates + cradle)
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Plates] */
// Inner plate: fits inside the cradle bore and bolts to the motor face
inner_plate = true;
// Outer plate: sits on the outside of the far end and mounts to the panel
outer_plate = true;
// Plate thickness
plate_thickness = 2.0;
// Outer plate size (square) and corner chamfer flat
plate_size        = 60.0;
plate_corner_flat = 8.0;
// Corner mounting screw holes (M3 clearance)
corner_hole_dia   = 3.4;
corner_hole_inset = 6.0;

/* [Motor cutout] */
// Motor face size (measured: 42 mm)
motor_face   = 42.0;
// Total clearance added to the cavity so the motor isn't too tight
motor_clearance = 0.6;
// NEMA 17 bolt hole spacing
bolt_spacing = 31.0;
// Motor bolt hole diameter (M3 clearance)
bolt_dia     = 3.4;
// Centring boss clearance
boss_dia     = 22.5;
// Shaft clearance
shaft_dia    = 8.0;
// Length of the flat on each tapered corner (motor is octagonal)
corner_flat  = 6.0;

/* [Cradle] */
// Add the three-sided cradle that wraps the motor body
include_cradle = true;
// Cradle wall thickness
wall_thickness = 2.0;
// Motor body length (measured: 45 mm deep)
motor_length   = 45.0;

/* [Wire cutout] */
// Distance of the slot centre from the motor-end plate
wire_slot_from_plate = 10.0;
// Slot width (along the plate)
wire_slot_width      = 8.0;
// Slot height (along the motor axis)
wire_slot_height     = 8.0;
// Which wall the slot breaks through: -1 = -Y wall, +1 = +Y wall
wire_slot_side       = -1;

/* [Parts] */
// Which piece(s) to lay out: "all", "inner", "outer", "cradle"
part = "all";

/* [Quality] */
$fn = 64;

module octagon_prism(height, across_flats, flat, center_z = 0) {
    // Square across flats with 45 degree corner cuts leaving `flat`.
    half = across_flats / 2;
    cut = flat / sqrt(2);
    translate([0, 0, center_z])
        linear_extrude(height = height, center = true)
            polygon(points = [
                [ half,         half - cut],
                [ half - cut,    half],
                [-(half - cut),  half],
                [-half,         half - cut],
                [-half,        -(half - cut)],
                [-(half - cut), -half],
                [ half - cut,   -half],
                [ half,        -(half - cut)],
            ]);
}

module motor_cutout() {
    // Bolt pattern, centring boss and shaft clearance
    for (x = [-1, 1], y = [-1, 1]) {
        translate([x * bolt_spacing / 2, y * bolt_spacing / 2, 0])
            cylinder(d = bolt_dia, h = plate_thickness * 4, center = true);
    }
    cylinder(d = boss_dia, h = plate_thickness * 4, center = true);
    cylinder(d = shaft_dia, h = plate_thickness * 4, center = true);
}

module inner_plate() {
    // Sits inside the cradle bore at the motor end and bolts to the motor.
    z_motor_end = -plate_thickness / 2 - plate_thickness / 2;
    difference() {
        octagon_prism(plate_thickness, motor_face + motor_clearance, corner_flat, z_motor_end);
        motor_cutout();
    }
}

module outer_plate() {
    // Sits on the outside of the far end and mounts to the panel.
    z_far = -plate_thickness / 2 - motor_length - plate_thickness / 2;
    difference() {
        octagon_prism(plate_thickness, plate_size, plate_corner_flat, z_far);
        // Central opening so the motor's shape can pass through the middle
        octagon_prism(plate_thickness * 4, motor_face + motor_clearance, corner_flat, z_far);
        for (x = [-1, 1], y = [-1, 1]) {
            translate([x * (plate_size / 2 - corner_hole_inset),
                       y * (plate_size / 2 - corner_hole_inset), z_far])
                cylinder(d = corner_hole_dia, h = plate_thickness * 4, center = true);
        }
    }
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
                octagon_prism(motor_length + 2, motor_face + motor_clearance, corner_flat);
                // Wiring exit slot (parameters under [Wire cutout])
                translate([0,
                           wire_slot_side * (motor_face + motor_clearance) / 2,
                           motor_length / 2 - wire_slot_from_plate])
                    cube([wire_slot_width, wall_thickness + 6, wire_slot_height],
                         center = true);
            }
        }
    }
}

module stepper_holder() {
    if (part == "all") {
        // Stacked vertically: inner plate at the bottom, cradle between,
        // outer frame on top.
        translate([0, 0, plate_thickness])
            inner_plate();
        translate([0, 0, plate_size + 20 + plate_thickness / 2 + motor_length / 2])
            motor_cradle();
        translate([0, 0, 2 * plate_size + 40 + plate_thickness + motor_length])
            outer_plate();
    } else if (part == "inner") {
        inner_plate();
    } else if (part == "outer") {
        outer_plate();
    } else {
        motor_cradle();
    }
}

stepper_holder();
