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

/* [Quality] */
$fn = 48;

outer_width  = cavity_width  + 2 * wall_thickness;
outer_length = cavity_length + 2 * wall_thickness;
outer_height = cavity_height + base_thickness;

module gun_cradle() {
    difference() {
        // Outer shell
        cube([outer_width, outer_length, outer_height], center = true);

        // Cavity, open at the top
        translate([0, 0, base_thickness / 2 + 0.5])
            cube([cavity_width, cavity_length, cavity_height + 1], center = true);
    }
}

gun_cradle();
