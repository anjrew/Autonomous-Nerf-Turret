# Stepper motor holder (NEMA 17 / 17HS4023)

Parametric OpenSCAD holder for the elevation stepper motor used by the turret.

## Files

- `stepper_holder.scad` — parametric source; edit the values at the top
- Export an STL with OpenSCAD: open the file, press **F6** (render), then
  **File → Export → Export as STL**

## Default dimensions

| Feature | Value |
| --- | --- |
| Motor face | 42.3 mm (17HS4023) |
| Bolt pattern | 31 mm square, M3 (3.4 mm clearance) |
| Centring boss clearance | 22.5 mm |
| Shaft clearance | 8 mm |
| Plate thickness | 5 mm |
| Cradle wall height | 18 mm |

The holder has a face plate with the NEMA 17 bolt pattern, a three-sided
cradle that holds the motor body (open on top for drop-in and at the back for
wiring), and two side flanges with screw slots for mounting to the turret.

Tune the parameters for your exact motor, then re-render and export.
