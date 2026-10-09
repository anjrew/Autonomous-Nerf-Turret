// Trigger block for the Nerf turret fire mechanism
// Export: F6 to render, then File > Export > Export as STL
// All dimensions in mm.

/* [Block] */
block_x = 4.0;   // width
block_y = 5.0;   // depth
block_z = 20.0;  // length

/* [Quality] */
$fn = 48;

cube([block_x, block_y, block_z], center = true);
