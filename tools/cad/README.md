# CAD to URDF: SmartManipulator-X description from the BCN3D Moveo CAD

These scripts build `smartmanipulator_x_description` (URDF and meshes) from a
STEP export of the BCN3D Moveo assembly (`BCN3D Moveo assembly.SLDASM` in
<https://github.com/BCN3D/BCN3D-Moveo>, `CAD files/`). The STEP is not in the
repository (about 200 MB).

```bash
tools/cad/run_all.sh BCN3D_Moveo_assembly.stp ../BCN3D-Moveo /tmp/smx_cad
```

Python 3 with numpy, scipy and matplotlib. Run time is under a minute.

| Step | Script | Result |
| --- | --- | --- |
| 1 | `parse_step.py` | Faceted STEP (POLY_LOOP triangles, MAPPED_ITEM placements) to `shapes.npz` and `instances.json` |
| 2 | `match_parts.py` | Names each shape by comparing surface area and extents with the BCN3D printed-part STL files |
| 3 | `classify.py` | Assigns every part instance to a link: anchor parts per link, then nearest anchor for screws, bearings, motors |
| 4 | `build.py` | Joint axes from the axles (shoulder 8 × 140 mm, elbow, wrist 8 × 80 mm), link frames, gripper parallelogram, decimated visual meshes, convex-hull collision meshes, `geometry.json` |
| 5 | `gen_urdf.py` | `smartmanipulator_x.urdf.xacro` and a plain `test.urdf` |
| 6 | `fk_render.py`, `collide.py` | Check images at the zero and the CAD assembly pose; collision-mesh overlaps for the SRDF |

`holes.py <instance ids>` finds the bearing and screw holes of the gripper
parts; its results are the gripper points in `build.py`.

The shape and instance numbers in `classify.py` and `build.py` refer to this
particular STEP export. A different export (another converter, another CAD
version) gets other numbers: check `match.json` and the rendered images, and
update the anchor lists.

## Measured from the CAD

| Quantity | Value |
| --- | --- |
| Base (table plate top) to J2 axis | 231.64 mm |
| J2 to J3 | 221.12 mm |
| J3 to J5 (along the J4 roll axis) | 223.00 mm |
| J5 to the gear axes / pivot axes of the gripper | 65 mm / 85 mm |
| Gear and pivot arms (parallelogram) | 40 mm |
| Finger gap, fully open | 80 mm |
| CAD assembly pose | J2 42.5°, J3 26.8°, J4 8.2°, J5 52.4° |
