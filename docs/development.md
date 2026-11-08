# Development

This page describes how the Robot PC repository is organized and built: the
Docker image, the ROS 2 workspace, the robot description generated from the
CAD, the documentation and the CI workflows. The controller firmware has its
own [development environment](firmware/development.md).

## Repository layout

```text
.
├── docker/
│   ├── Dockerfile                    Robot PC image (ros:jazzy-ros-base + ROBOTIS packages + workspace)
│   ├── docker-compose.yml            robot_pc and probe services, network smx_net
│   ├── docker-compose.hw.yml         USB device pass-through (Linux hosts)
│   ├── entrypoint.sh                 sources ROS 2 and the built workspace
│   ├── env.example                   template for docker/.env
│   └── dds/fastdds_udp.xml           Fast DDS profile: UDPv4 only
├── ros2_ws/src/smartmanipulator_x/
│   ├── smartmanipulator_x_bringup/   robot.launch.py
│   ├── smartmanipulator_x_config/    controllers.yaml, hardware.yaml
│   ├── smartmanipulator_x_description/  URDF/Xacro and meshes generated from the Moveo CAD
│   └── smartmanipulator_x_tests/     test area
├── ros2_ws/src/robotis/              checkout target of ros2_robot.repos (in the image)
├── ros2_robot.repos                  upstream sources built into the Robot PC image
├── ros2.repos                        broader workspace manifest
├── tools/
│   ├── cad/                          STEP → URDF pipeline for the robot description
│   ├── diagnostics/smx_smoke_test.sh end-to-end check over DDS
│   └── docs/                         PDF manual builder, diagrams, MkDocs hook
├── docs/, overrides/, mkdocs.yml     this documentation
├── requirements-docs.txt             documentation tools (.venv)
└── .vscode/tasks.json                Robot PC and documentation tasks
```

Generated directories (`ros2_ws/build/`, `ros2_ws/install/`, `ros2_ws/log/`,
`site/`, `build/`, `docs/downloads/`, `.venv/`) are ignored.

## Robot PC image

The image is based on `ros:jazzy-ros-base`. It imports the DYNAMIXEL SDK and
interface packages through `ros2_robot.repos`, builds them together with the
project packages, and contains ROS control, USB diagnostics and build tools.
MoveIt 2, RViz2, Gazebo and the OpenMANIPULATOR GUI and bringup packages are
deliberately excluded: they belong to the Operator PC.

The workspace is baked into the image, not bind-mounted, so rebuild after
changing project sources or `ros2_robot.repos`:

```bash
docker compose -f docker/docker-compose.yml build robot_pc
docker compose -f docker/docker-compose.yml build --no-cache --pull robot_pc   # from scratch
```

The `jazzy` refs in `ros2_robot.repos` are branch names and can move; pin
immutable revisions before relying on a build for verification.

## VS Code tasks

`.vscode/tasks.json` runs Docker Compose from the repository root.
**Ctrl+Shift+B** opens a picker with every task of the build group; none is
the default, so the picker always appears.

| Task | Group | Command |
| --- | --- | --- |
| Robot PC: Start (mock hardware) | build | `docker compose -f docker/docker-compose.yml up --build robot_pc` |
| Robot PC: Stop | build | `docker compose -f docker/docker-compose.yml down` |
| Robot PC: Rebuild and restart | build | Stop, then `up --build --force-recreate robot_pc` |
| Robot PC: Build image | build | `build robot_pc` |
| Robot PC: Rebuild image (no cache) | build | `build --no-cache --pull robot_pc` |
| Docs: Build PDF manual | build | `python tools/docs/build_manual.py` in `.venv` |
| Robot PC: Smoke test (probe) | test | `run --rm probe smx_smoke_test.sh` |
| Robot PC: Probe shell | – | `run --rm probe bash` |
| Docs: Live preview | – | `mkdocs serve` in `.venv` |

## Robot description from the CAD

`smartmanipulator_x_description` is generated from a STEP export of the BCN3D
Moveo assembly by the scripts in `tools/cad/` (Python 3 with numpy, scipy and
matplotlib). The STEP itself is not in the repository (about 200 MB):

```bash
tools/cad/run_all.sh BCN3D_Moveo_assembly.stp ../BCN3D-Moveo /tmp/smx_cad
```

The steps, the measured dimensions and the conventions of the model are in
`tools/cad/README.md` and on the [BCN3D Moveo mechanics](mechanical/index.md)
page.

## Documentation

The documentation is the Markdown in `docs/`. MkDocs Material turns it into
the website, and `tools/docs/build_manual.py` turns the same pages into the
printable A4 user manual (cover, imprint, contents with page numbers,
numbered chapters, running headers, PDF bookmarks), rendered with WeasyPrint.
Both follow the SystemFromScratch® documentation style; the landing page is
configured in `mkdocs.yml → extra.landing` and the manual in
`mkdocs.yml → extra.manual`.

Set up the tools once in the repository `.venv`. WeasyPrint needs the Pango
library: on Windows from MSYS2 (`pacman -S mingw-w64-x86_64-pango`; the
builder finds `C:\msys64\mingw64\bin` by itself), on Ubuntu
`apt install libpango-1.0-0 libpangoft2-1.0-0`.

```powershell
# Windows (PowerShell, repository root)
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-docs.txt
```

```bash
# Linux (repository root)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-docs.txt
```

| Command | Result |
| --- | --- |
| `python -m mkdocs serve` | Live preview at <http://127.0.0.1:8000> |
| `python -m mkdocs build` | Static website in `site/` (strict: a broken link fails the build) |
| `python tools/docs/build_manual.py` | `build/manual/SmartManipulator-X_User_Manual_v<version>.pdf`; the version is the latest `vX.Y.Z` tag |
| `python tools/docs/build_manual.py --output docs/downloads/SmartManipulator-X_User_Manual.pdf` | The file the website links to (CI does this before deploying) |
| `python tools/docs/diagrams.py` | Regenerates the hero illustration `docs/assets/images/hero-3d.svg`; the arm is drawn from the robot description meshes and URDF by `tools/docs/hero_robot.py`, so run it again after the description changes |
| `python tools/docs/render_mermaid.py` | Renders `docs/**/diagrams/*.mmd` to `docs/**/images/*.svg` (needs Playwright and a network connection) |

Writing rules that keep the website and the PDF correct:

- Start every page with exactly one `# Title`; chapter and section numbers are
  added in the PDF, so do not number headings by hand.
- Add a new page to `nav` in `mkdocs.yml`, otherwise it is missing from the
  site and the PDF.
- An image on a line of its own, `![Caption](images/file.svg)`, becomes a
  figure with its alt text as the caption (`tools/docs/hooks.py`).
- Link to other pages with relative `.md` paths; strict mode checks them, and
  the PDF turns them into page references.
- Diagrams are SVG files. Mermaid sources live in `diagrams/*.mmd` next to the
  page and are rendered with `render_mermaid.py`, because the PDF renderer
  runs no JavaScript.

## CI

| Workflow | Trigger | Does |
| --- | --- | --- |
| `docker-publish.yml` | Push to `main` or a `v*` tag touching the image sources; manual | Builds the Robot PC image and publishes it to `ghcr.io/systemfromscratch/sfs-smartmanipulator-x-robot` |
| `documentation.yml` | Push to `main`; manual | Builds the PDF manual into `docs/downloads/`, then `mkdocs gh-deploy` publishes the website with the PDF to GitHub Pages |

## Engineering rules for agents

The architecture and the Robot PC, Operator PC and SmartFusion2 rules for
coding agents are skills in the shared
[sfs-smartmanipulator-x-skills](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-skills)
repository, used by every repository of the project.
