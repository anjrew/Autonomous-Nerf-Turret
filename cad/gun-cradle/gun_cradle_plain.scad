// Cradle for the Nerf gun to sit in (open-top tray)
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Cavity] */
// Internal cavity the gun sits in
// Outer size is 70 x 60 x 15 mm (cavity = outer - 2 x wall)
cavity_width  = 64.0;   // X -> outer 70
cavity_height = 15.0;   // Z -> outer 15 (no base)
cavity_length = 54.0;   // Y -> outer 60

/* [Walls] */
wall_thickness = 3.0;
// No base: the cradle is open at both ends (set > 0 to add a floor)
base_thickness = 0.0;

/* [Corner radii] */
// Radius on the inside corners of the cavity
inner_corner_radius = 4.0;
// Radius on the outside corners of the cradle
outer_corner_radius = 6.0;

/* [Base fillet] */
// Fillet where the cavity floor meets the walls
floor_fillet = 3.0;

/* [Open side] */
// Completely open one of the short sides
open_short_side = true;
// Which short side: -1 = -X, +1 = +X
open_side = -1;

/* [Mounts] */
// Pipe sockets coming off each side that a 10 mm pipe slides into
mount_pipes    = false;
pipe_dia       = 10.0;  // pipe bore (slip fit)
socket_outer_dia = 16.0;
socket_length  = 15.0;  // how far the socket sticks out
// Socket height as a fraction of the wall (0 = bottom edge, 0.5 = centred)
socket_z_fraction = 0.5;
// Distance of the socket centre from the closed end, along Y
socket_y = 100.0;
// Grub screw hole through the socket wall (kept for reference; unused)
grub_dia = 3.0;
// Clamp hardware
clamp_slit   = 1.6;  // slit width
clamp_ear_h  = 6.0;  // how far the clamp ears stick out
clamp_ear_w  = 5.0;  // ear width each side of the slit
clamp_bolt_dia = 3.4; // M3 bolt clearance
clamp_nut_af   = 5.5; // M3 hex nut across flats

/* [Capsule opening] */
// Capsule slot through the closed short wall (centred in X)
capsule_length = 35.0;
capsule_width  = 10.0;
// Distance from the bottom edge to the start of the capsule
capsule_from_bottom = 13.0;

/* [Quality] */
$fn = 48;

outer_width  = cavity_width  + 2 * wall_thickness;
outer_length = cavity_length + 2 * wall_thickness;
outer_height = cavity_height + base_thickness;

module rounded_rect(width, length, radius) {
    offset(r = radius) square([width - 2 * radius, length - 2 * radius], center = true);
}

module pipe_socket() {
    // Plain slip-fit socket (no clamp or tightening holes)
    difference() {
        cylinder(d = socket_outer_dia, h = socket_length, center = true);
        cylinder(d = pipe_dia, h = socket_length + 2, center = true);
    }
}

module gun_cradle() {
    difference() {
        // Outer shell with rounded outside corners, squared off at the open end
        union() {
            linear_extrude(height = outer_height, center = true)
                rounded_rect(outer_width, outer_length, outer_corner_radius);
            if (open_short_side) {
                translate([0, open_side * (outer_length / 2 - outer_corner_radius / 2), 0])
                    linear_extrude(height = outer_height, center = true)
                        square([outer_width, outer_corner_radius], center = true);
            }
            // Pipe sockets coming off each side at the bottom
            if (mount_pipes) {
                for (x = [-1, 1]) {
                    translate([x * (outer_width / 2 + socket_length / 2 - 1),
                               -outer_length / 2 + socket_y,
                               -outer_height / 2 + socket_z_fraction * outer_height])
                        rotate([0, 90, 0])
                            pipe_socket();
                }
            }
        }

        // Cavity with rounded inside corners, open at the top
        translate([0, 0, base_thickness / 2 + 0.5])
            linear_extrude(height = cavity_height + 1, center = true)
                rounded_rect(cavity_width, cavity_length, inner_corner_radius);

        // Capsule opening disabled for this part (too short to fit)
        // Remove one short side (±Y walls, the 60 mm-wide faces) entirely
        if (open_short_side) {
            translate([0, open_side * (cavity_length / 2 + wall_thickness / 2 + 0.5), 0])
                cube([outer_width + 2, wall_thickness + 1, outer_height + 2], center = true);
            // Square the inner cavity corners at the open end as well
            translate([0, open_side * (cavity_length / 2 - inner_corner_radius / 2), 0])
                linear_extrude(height = cavity_height + 2, center = true)
                    square([cavity_width, inner_corner_radius], center = true);
        }
    }
}

gun_cradle();
