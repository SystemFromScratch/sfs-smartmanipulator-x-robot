#!/bin/bash
# Regenerate the SmartManipulator-X description from the BCN3D Moveo CAD.
#   tools/cad/run_all.sh <assembly.stp> <BCN3D-Moveo checkout> [work dir]
# Needs Python 3 with numpy, scipy and matplotlib. Writes the URDF and the
# meshes into smartmanipulator_x_description and renders check images.
set -euo pipefail
STEP="$(realpath "$1")"; BCN3D="$(realpath "$2")"; WORK="${3:-/tmp/smx_cad}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PKG="$HERE/../../ros2_ws/src/smartmanipulator_x/smartmanipulator_x_description"
mkdir -p "$WORK" && cd "$WORK"
cp "$HERE"/*.py .
python3 parse_step.py "$STEP" .           # shapes.npz, instances.json
python3 match_parts.py "$BCN3D"            # match.json: STEP shape -> BCN3D part name
python3 classify.py > classify.txt         # labels.json: instance -> link
python3 build.py out > /dev/null           # frames, gripper geometry, meshes, geometry.json
python3 gen_urdf.py out/geometry.json out/smartmanipulator_x.urdf.xacro out/test.urdf
python3 fk_render.py out/test.urdf out/meshes out/zero.png ""
python3 fk_render.py out/test.urdf out/meshes out/assembly.png \
  "j2_shoulder=0.7416,j3_elbow=0.4674,j4_forearm_roll=0.1426,j5_wrist=0.9151"
python3 collide.py > collide.txt
cp out/smartmanipulator_x.urdf.xacro "$PKG/urdf/"
rm -rf "$PKG/meshes/visual" "$PKG/meshes/collision"
cp -r out/meshes/visual out/meshes/collision "$PKG/meshes/"
cp out/geometry.json "$PKG/meshes/geometry.json"
echo "Done. Check images: $WORK/out/zero.png, $WORK/out/assembly.png; collisions: $WORK/collide.txt"
