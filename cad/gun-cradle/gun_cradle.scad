// Cradle for the Nerf gun to sit in (open-top tray)
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Cavity] */
// Internal cavity the gun sits in
cavity_width  = 60.0;   // X
cavity_height = 100.0;  // Z
cavity_length = 100.0;  // Y

/* [Walls] */
wall_thickness = 3.0;
base_thickness = 3.0;

/* [Corner radii] */
// Radius on the inside corners of the cavity
inner_corner_radius = 4.0;
// Radius on the outside corners of the cradle
outer_corner_radius = 6.0;

/* [Base fillet] */
// Fillet where the cavity floor meets the walls
floor_fillet = 3.0;

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
        // Outer shell with rounded outside corners
        linear_extrude(height = outer_height, center = true)
            rounded_rect(outer_width, outer_length, outer_corner_radius);

        // Cavity with rounded inside corners, open at the top
        translate([0, 0, base_thickness / 2 + 0.5])
            linear_extrude(height = cavity_height + 1, center = true)
                rounded_rect(cavity_width, cavity_length, inner_corner_radius);
    }
}

gun_cradle();
