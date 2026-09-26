// Cradle for the Nerf gun to sit in (open-top tray)
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Cavity] */
// Internal cavity the gun sits in
cavity_width  = 60.0;   // X
cavity_height = 100.0;  // Z
cavity_length = 120.0;  // Y (20 mm longer)

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
open_side = 1;

/* [Mounts] */
// Pipe sockets coming off each side that a 10 mm pipe slides into
mount_pipes    = true;
pipe_dia       = 10.0;  // pipe bore (slip fit)
socket_outer_dia = 16.0;
socket_length  = 15.0;  // how far the socket sticks out
// Socket height as a fraction of the wall (0 = bottom edge, 0.5 = centred)
socket_z_fraction = 0.5;
// Distance of the socket centre from the closed end, along Y
socket_y = 100.0;
// Grub screw hole through the socket wall (self-tapping; 3.0 for M3)
grub_dia = 3.0;

/* [Quality] */
$fn = 48;

outer_width  = cavity_width  + 2 * wall_thickness;
outer_length = cavity_length + 2 * wall_thickness;
outer_height = cavity_height + base_thickness;

module rounded_rect(width, length, radius) {
    offset(r = radius) square([width - 2 * radius, length - 2 * radius], center = true);
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
                            difference() {
                                cylinder(d = socket_outer_dia, h = socket_length, center = true);
                                cylinder(d = pipe_dia, h = socket_length + 2, center = true);
                                // Grub screw hole through the socket wall
                                rotate([90, 0, 0])
                                    cylinder(d = grub_dia, h = socket_outer_dia + 2, center = true);
                            }
                }
            }
        }

        // Cavity with rounded inside corners, open at the top
        translate([0, 0, base_thickness / 2 + 0.5])
            linear_extrude(height = cavity_height + 1, center = true)
                rounded_rect(cavity_width, cavity_length, inner_corner_radius);

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
