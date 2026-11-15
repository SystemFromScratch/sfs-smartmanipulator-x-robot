#!/usr/bin/env python3
"""Pictorial connection views of SmartManipulator-X for readers new to electronics
(docs/hardware/images/pictorial-*.svg).

The boards are simplified drawings, not photos: they show where a wire goes, not every
part. Pin and pad names must match docs/hardware/wiring.md. Run from the repository root:

    python tools/docs/pictorial_diagrams.py
"""
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "hardware", "images")

# wire colors: one meaning each, used on every drawing and in the legends
WIRE = {
    "vm": ("#d93025", "motor supply (+)"),
    "gnd": ("#202124", "ground (−)"),
    "data": ("#1e8e3e", "bus DATA"),
    "v5": ("#f29900", "5 V / 3.3 V logic supply"),
    "v6": ("#e8710a", "6 V servo supply"),
    "sig": ("#1a73e8", "signal"),
    "usb": ("#5f6368", "USB cable"),
    "wifi": ("#9334e6", "Wi-Fi (no cable)"),
}
MOTOR = {"A+": "#202124", "A−": "#1e8e3e", "B+": "#d93025", "B−": "#1a73e8"}

STYLE = """
    .h { font-weight: 700; font-size: 16px; fill: #202124; }
    .t { fill: #202124; font-size: 13px; }
    .s { fill: #5f6368; font-size: 12px; }
    .w { fill: #ffffff; font-size: 11px; font-weight: 600; }
    .k { fill: #e8eaed; font-size: 10px; }
    .tag { fill: #ffffff; stroke: #dadce0; stroke-width: 1; }
    .step { fill: #1a73e8; }
    .stept { fill: #ffffff; font-weight: 700; font-size: 14px; }
"""


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title, self.parts = w, h, title, []

    def add(self, s):
        self.parts.append("  " + s)

    def rect(self, x, y, w, h, fill, stroke="none", rx=0, sw=1.5, extra=""):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def circle(self, x, y, r, fill, stroke="none", sw=1.5):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"/>')

    def text(self, x, y, s, cls="t", anchor="start", rot=None):
        tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
        self.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"{tr}>{s}</text>')

    def tag(self, x, y, s, anchor="middle"):
        """A white label with a border, for wire names."""
        w = 7.2 * len(s) + 12
        x0 = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
        self.rect(x0, y - 13, w, 19, "#ffffff", "#dadce0", 4, 1)
        self.text(x0 + w / 2, y + 1, s, "s", "middle")

    def step(self, x, y, n):
        self.circle(x, y, 13, "#1a73e8")
        self.text(x, y + 5, str(n), "stept", "middle")

    def wire(self, kind, *pts, color=None, width=5, curve=False, dash=None):
        """A wire with a dark outline; pts are joined by smooth curves."""
        c = color or WIRE[kind][0]
        if curve and len(pts) >= 2:
            d = f"M{pts[0][0]} {pts[0][1]}"
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                my = (y0 + y1) / 2
                d += f" C{x0} {my} {x1} {my} {x1} {y1}"
        else:
            d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        if not dash:
            self.add(f'<path d="{d}" fill="none" stroke="#00000055" stroke-width="{width + 2.5}" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>')
        self.add(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{width}" '
                 f'stroke-linecap="round" stroke-linejoin="round"{da}/>')

    def legend(self, x, y, kinds, cols=4, colw=230):
        for i, k in enumerate(kinds):
            xx, yy = x + (i % cols) * colw, y + (i // cols) * 22
            color, label = WIRE[k]
            dash = ' stroke-dasharray="6 5"' if k == "wifi" else ""
            self.add(f'<path d="M{xx} {yy} L{xx + 30} {yy}" stroke="{color}" stroke-width="5" '
                     f'stroke-linecap="round"{dash}/>')
            self.text(xx + 40, yy + 4, label, "s")

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" font-family="Segoe UI, DejaVu Sans, Arial, '
                f'sans-serif" role="img" aria-label="{self.title}">\n'
                f'  <title>{self.title}</title>\n  <style>{STYLE}  </style>\n')
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(head + "\n".join(self.parts) + "\n</svg>\n")
        print("wrote", os.path.join(OUT, name))


# ------------------------------------------------------------------ parts
def cm4duino(s, x, y, label=True):
    """CM4-Duino seen from above (73.58 x 53.34 mm at 4 px/mm). Returns pin points."""
    w, h = 294, 213
    s.rect(x, y, w, h, "#1b1b1b", "#000", 10)
    # left edge connectors
    s.rect(x - 14, y + 18, 50, 46, "#d4a73a", "#8a6d1f", 3)       # HDMI
    s.text(x + 42, y + 46, "HDMI", "k")
    s.rect(x - 14, y + 82, 50, 52, "#c7c9cc", "#7b7e82", 3)       # USB-A
    s.text(x + 42, y + 112, "USB", "k")
    s.rect(x - 10, y + 152, 42, 30, "#c7c9cc", "#7b7e82", 8)      # USB-C
    s.text(x + 38, y + 172, "5 V in", "k")
    # CM4 module on top
    s.rect(x + 70, y + 40, 168, 116, "#1e5631", "#0f3a1f", 6)
    s.rect(x + 128, y + 70, 52, 52, "#3c4043", "#202124", 3)
    s.text(x + 154, y + 101, "CM4", "w", "middle")
    s.text(x + 154, y + 145, "Compute Module 4 (Wi-Fi)", "k", "middle")
    pins = {}
    # top header: 18 pins
    names = ["SCL", "SDA", "AREF", "GND", "D11", "D9", "D10", "D8", "D23", "D22",
             "D21", "D18", "D19", "D20", "D17", "D16", "D14", "D15"]
    px0 = x + 62
    for i, n in enumerate(names):
        px = px0 + i * 12.6 + (8 if i >= 10 else 0)
        s.rect(px - 5, y + 4, 11, 13, "#f2c200", "#a58400", 1, 1)
        s.text(px + 3, y + 26, n, "k", "end", rot=-90)
        pins[n] = (px + 0.5, y + 4)
    # bottom headers: power (red) and analog (blue)
    pnames = ["A7", "CFG", "RST", "3V3", "5V", "GND", "GND2", "VIN"]
    for i, n in enumerate(pnames):
        px = x + 112 + i * 12.6
        s.rect(px - 5, y + h - 17, 11, 13, "#e53935", "#8e1d1b", 1, 1)
        s.text(px + 3, y + h - 22, n.replace("GND2", "GND"), "k", "start", rot=-90)
        pins[n] = (px + 0.5, y + h - 4)
    for i in range(6):
        px = x + 222 + i * 12.6
        s.rect(px - 5, y + h - 17, 11, 13, "#1e63d6", "#0d3a87", 1, 1)
        s.text(px + 3, y + h - 22, f"A{i}", "k", "start", rot=-90)
    if label:
        s.text(x + 20, y + h + 24, "CM4-Duino", "h")
    pins["USB-C"] = (x - 10, y + 167)
    return pins


def esc(s, x, y, ident=None, small=False, ident_left=False):
    """B-G431B-ESC1 drawn upright like the photo: ST-LINK part left, power part right."""
    k = 0.62 if small else 1.0
    W, H = 150 * k, 230 * k
    s.rect(x, y, 46 * k, H, "#173a7a", "#0b2150", 5)                # ST-LINK part
    s.rect(x + 50 * k, y, 100 * k, H, "#173a7a", "#0b2150", 5)      # power part
    s.circle(x + 23 * k, y + 28 * k, 15 * k, "#2a6fdb", "#123d8a")  # potentiometer
    s.rect(x + 9 * k, y + 70 * k, 28 * k, 28 * k, "#2b2b2b")        # STM32
    s.rect(x + 9 * k, y + H - 22 * k, 28 * k, 16 * k, "#c7c9cc", "#7b7e82", 2)  # micro-USB
    for r in range(2):
        for c in range(3):
            s.rect(x + (58 + c * 31) * k, y + (34 + r * 44) * k, 25 * k, 34 * k, "#2b2b2b")
    for c in range(3):
        s.rect(x + (58 + c * 31) * k, y + 128 * k, 25 * k, 22 * k, "#3c4043")
    pts = {}
    # motor tabs on the top edge: U V W
    for i, n in enumerate(("U", "V", "W")):
        tx = x + (60 + i * 31) * k
        s.rect(tx, y - 8 * k, 22 * k, 16 * k, "#d4a73a", "#8a6d1f", 2, 1)
        if not small:
            s.text(tx + 11 * k, y - 13 * k, n, "s", "middle")
        pts[n] = (tx + 11 * k, y - 8 * k)
    # power pads bottom right: + and −
    for i, n in enumerate(("+", "−")):
        tx = x + (90 + i * 32) * k
        s.rect(tx, y + H - 20 * k, 26 * k, 26 * k, "#d4a73a", "#8a6d1f", 2, 1)
        s.text(tx + 13 * k, y + H - 3 * k, n, "s" if not small else "k", "middle")
        pts[n] = (tx + 13 * k, y + H + 6 * k)
    # J3 pads: 5 small pads (positions schematic)
    for i in range(5):
        tx = x + (56 + i * 6.5) * k
        s.rect(tx, y + 168 * k, 5 * k, 9 * k, "#d4a73a")
    pts["J3-2"] = (x + 64 * k, y + 177 * k)
    pts["J3-5"] = (x + 83.5 * k, y + 177 * k)
    if not small:
        s.text(x + 72 * k, y + 192 * k, "J3", "w", "middle")
    pts["USB"] = (x + 23 * k, y + H - 6 * k)
    if ident and ident_left:
        for i, part in enumerate(ident.split("|")):
            s.text(x - 16, y + 30 + i * 18, part, "h" if i == 0 else "s", "end")
    elif ident:
        s.text(x + W / 2, y + H + (34 if not small else 26) * k, ident, "t", "middle")
    return pts


def motor(s, x, y, small=False, label=None):
    """Stepper motor seen from the side with its four leads; returns lead end points."""
    k = 0.6 if small else 1.0
    s.rect(x, y, 90 * k, 90 * k, "#262626", "#000", 6)
    s.rect(x + 4 * k, y + 4 * k, 82 * k, 14 * k, "#b8babd", "#7b7e82", 3)
    s.rect(x + 41 * k, y - 26 * k, 8 * k, 30 * k, "#c7c9cc", "#7b7e82", 2)
    for i in range(8):
        yy = y + (24 + i * 7) * k
        s.add(f'<path d="M{x + 6 * k} {yy} L{x + 84 * k} {yy}" stroke="#3a3a3a" stroke-width="1"/>')
    leads = {}
    for i, (n, c) in enumerate(MOTOR.items()):
        lx = x + (27 + i * 12) * k
        s.add(f'<path d="M{lx} {y + 90 * k} L{lx} {y + 104 * k}" stroke="{c}" '
              f'stroke-width="{4 * k + 1}"/>')
        leads[n] = (lx, y + 104 * k)
    if label:
        s.text(x + 45 * k, y - (40 if not small else 22), label, "t" if not small else "s",
               "middle")
    return leads


def laptop(s, x, y, title, lines, w=200, h=128):
    s.rect(x, y, w, h, "#3c4043", "#202124", 8)
    s.rect(x + 8, y + 8, w - 16, h - 16, "#e8f0fe", "none", 4)
    s.text(x + w / 2, y + 32, title, "h", "middle")
    for i, l in enumerate(lines):
        s.text(x + w / 2, y + 54 + i * 18, l, "s", "middle")
    s.add(f'<path d="M{x - 20} {y + h + 12} L{x + w + 20} {y + h + 12} L{x + w} {y + h} '
          f'L{x} {y + h} Z" fill="#9aa0a6" stroke="#5f6368"/>')


def psu(s, x, y, title, sub, w=170, h=96):
    s.rect(x, y, w, h, "#dadce0", "#80868b", 6)
    for i in range(6):
        s.add(f'<path d="M{x + 12} {y + 14 + i * 6} L{x + 70} {y + 14 + i * 6}" '
              f'stroke="#9aa0a6" stroke-width="2"/>')
    s.text(x + 12, y + 66, title, "h")
    s.text(x + 12, y + 84, sub, "s")
    s.circle(x + w - 46, y + 30, 9, "#d93025", "#7d1a14")
    s.circle(x + w - 18, y + 30, 9, "#202124", "#000")
    s.text(x + w - 46, y + 55, "+", "t", "middle")
    s.text(x + w - 18, y + 55, "−", "t", "middle")
    return {"+": (x + w - 46, y + 30), "−": (x + w - 18, y + 30)}


def box(s, x, y, w, h, title, sub, fill="#f1f3f4", stroke="#80868b"):
    s.rect(x, y, w, h, fill, stroke, 8)
    s.text(x + w / 2, y + 24, title, "h", "middle")
    if sub:
        for i, line in enumerate(sub if isinstance(sub, list) else [sub]):
            s.text(x + w / 2, y + 44 + i * 16, line, "s", "middle")


def estop(s, x, y):
    s.rect(x - 34, y - 26, 68, 62, "#f2c200", "#a58400", 6)
    s.circle(x, y + 4, 22, "#d93025", "#7d1a14", 2)
    s.text(x, y + 56, "E-stop", "t", "middle")
    return (x - 34, y + 4), (x + 34, y + 4)


def servo(s, x, y):
    s.rect(x, y, 110, 56, "#1f3b73", "#0f2147", 6)
    s.rect(x - 14, y + 18, 138, 10, "#1f3b73", "#0f2147", 3)
    s.circle(x + 30, y - 6, 16, "#ffffff", "#9aa0a6")
    s.text(x + 72, y + 40, "MG996R", "w", "middle")
    leads = {}
    for i, (n, c) in enumerate((("signal", "#f29900"), ("+6 V", "#d93025"), ("GND", "#6d4c41"))):
        ly = y + 14 + i * 12
        s.add(f'<path d="M{x + 110} {ly} L{x + 130} {ly}" stroke="{c}" stroke-width="5"/>')
        leads[n] = (x + 130, ly)
    return leads


def breadboard(s, x, y, w=230, h=150):
    s.rect(x, y, w, h, "#fafafa", "#bdc1c6", 6)
    for r in range(8):
        for c in range(int(w / 12)):
            s.circle(x + 10 + c * 12, y + 18 + r * 16, 1.6, "#bdc1c6")
    for i, n in enumerate(("U1", "U2", "U3")):
        cx = x + 40 + i * 62
        s.rect(cx - 16, y + 55, 32, 22, "#202124", "#000", 2)
        s.text(cx, y + 70, n, "w", "middle")
    s.rect(x + 190, y + 48, 26, 9, "#d2b48c", "#8d6e63", 3)
    s.text(x + 203, y + 44, "R1", "s", "middle")
    s.text(x + w / 2, y + h + 20, "Bus interface (breadboard)", "t", "middle")
    return {"in": (x, y + 100), "out": (x + w, y + 100)}


# ------------------------------------------------------------------ views
def view_sim():
    s = Svg(1100, 360, "Level 1: everything on one computer, no hardware. Docker runs the "
                       "Operator PC with MoveIt and RViz and the Robot PC with simulated joints")
    laptop(s, 60, 50, "Your computer", ["Docker"], w=380, h=210)
    for x, title, lines, fill, stroke in (
            (90, "Operator PC", ["MoveIt 2", "RViz2"], "#e6f4ea", "#188038"),
            (270, "Robot PC", ["ros2_control", "simulated joints"], "#e8f0fe", "#1a73e8")):
        s.rect(x, 120, 150, 100, fill, stroke, 6)
        s.text(x + 75, 146, title, "t", "middle")
        for i, l in enumerate(lines):
            s.text(x + 75, 170 + i * 18, l, "s", "middle")
    s.add('<path d="M240 170 L270 170" stroke="#1a73e8" stroke-width="3" '
          'marker-end="none"/>')
    s.text(250, 238, "DDS", "s", "middle")
    s.text(250, 310, "No cables, no boards, no power supply.", "t", "middle")
    s.text(560, 70, "What you can do here", "h")
    for i, line in enumerate([
            "• plan and execute arm motions in MoveIt 2 and watch them in RViz2",
            "• write your own planners, controllers or kinematics nodes in ROS 2",
            "• send trajectories to arm_controller and read /joint_states",
            "• later (Stage 1): replace the simulated joints by doppelstep",
            "drives that run their real firmware on your PC"]):
        s.text(560 if i < 4 else 572, 102 + i * 24, line, "t")
    s.text(560, 240, "Start: Getting started, two docker compose commands.", "s")
    s.save("pictorial-level1-simulation.svg")


def view_bench():
    s = Svg(1100, 600, "Level 2: one drive and one motor on the desk. The PC connects to the "
                       "drive with one USB cable; a laboratory supply powers the drive; the "
                       "motor has four wires")
    laptop(s, 40, 130, "Your computer", ["Robot PC in Docker", "+ Operator PC"])
    p = esc(s, 470, 200)
    s.text(545, 520, "doppelstep drive (B-G431B-ESC1)", "t", "middle")
    m = motor(s, 860, 250, label="stepper motor")
    lab = psu(s, 700, 455, "Lab supply", "12 V, current limit 0.5 A")
    # USB cable from the laptop to the ST-LINK micro-USB
    s.wire("usb", (250, 250), (400, 250), (400, 480), (p["USB"][0], 480), p["USB"], width=7)
    # motor leads to U V W
    pads = {"A+": (p["U"][0], 0), "B+": (p["V"][0], 0), "A−": (p["W"][0] - 4, 0),
            "B−": (p["W"][0] + 4, 0)}
    for i, lead in enumerate(("A+", "A−", "B+", "B−")):
        lx, ly = m[lead]
        yb = ly + 14 + i * 10
        xr = 790 - i * 14
        yt = 160 - i * 12
        px = pads[lead][0]
        s.wire("x", m[lead], (lx, yb), (xr, yb), (xr, yt), (px, yt), (px, p["U"][1]),
               color=MOTOR[lead], width=4)
    # supply
    s.wire("gnd", p["−"], (p["−"][0], 440), (lab["−"][0], 440), (lab["−"][0], lab["−"][1] - 9))
    s.wire("vm", p["+"], (p["+"][0], 455), (lab["+"][0], 455), (lab["+"][0], lab["+"][1] - 9))
    s.tag(640, 96, "A+ → U · B+ → V · A− and B− → W")
    s.step(500, 96, 2)
    s.tag(320, 240, "USB cable")
    s.step(255, 240, 1)
    s.step(650, 425, 3)
    for i, line in enumerate([
            ("1  USB cable: the DYNAMIXEL bus (virtual COM port),", "t"),
            ("    flashing and the log of the drive.", "t"),
            ("2  Motor: find the two coils with a multimeter first.", "t"),
            ("    Colors shown are those of a 17HS19-2004S1.", "s"),
            ("3  Supply last, after checking every wire.", "t"),
            ("    Start at 12 V with a current limit.", "s")]):
        s.text(40, 330 + i * 20, *line)
    s.legend(40, 570, ["vm", "gnd", "usb"], cols=3)
    s.text(720, 574, "Motor leads: black A+, green A−, red B+, blue B−", "s")
    s.save("pictorial-level2-bench.svg")


def view_full():
    s = Svg(1240, 990, "Level 3: the whole robot. Operator laptop over Wi-Fi to the CM4-Duino; "
                       "a two-wire bus to six drives; each drive has its motor; a 24 V supply "
                       "through the emergency stop and a fuse powers the drives and the servo "
                       "converter; a USB-C adapter powers the CM4-Duino")
    laptop(s, 30, 30, "Operator laptop", ["MoveIt 2 · RViz2", "your algorithms"])
    c = cm4duino(s, 380, 40)
    s.wire("wifi", (250, 90), (300, 70), (360, 90), width=4, dash="10 7", curve=True)
    s.tag(305, 58, "Wi-Fi")
    usbc = psu(s, 30, 230, "USB-C adapter", "5 V, 3 A", w=180)
    s.wire("v5", (usbc["+"][0], 222), (usbc["+"][0], 207), c["USB-C"], width=6)
    b = breadboard(s, 790, 60)
    s.wire("sig", c["D14"], (c["D14"][0], 20), (760, 20), (760, 140), (b["in"][0], 140), width=3)
    s.wire("sig", c["D15"], (c["D15"][0], 28), (750, 28), (750, 150), (b["in"][0], 150), width=3)
    s.wire("v5", c["3V3"], (c["3V3"][0], 290), (740, 290), (740, 120), (b["in"][0], 120), width=3)
    s.wire("gnd", c["GND"], (c["GND"][0], 300), (770, 300), (770, 175), (b["in"][0], 175), width=3)
    s.tag(640, 12, "D14 · D15")
    s.tag(640, 318, "3V3 · GND")
    # rows
    my, dy = 420, 520           # motors, drives
    bus_y, gnd_y = 700, 714
    vm_y, gv_y = 760, 776
    s.wire("data", b["out"], (1060, 160), (1060, bus_y), (110, bus_y), width=4)
    s.wire("gnd", (1020, 210), (1080, 210), (1080, gnd_y), (110, gnd_y), width=4)
    s.tag(1110, 340, "bus: DATA + GND")
    s.tag(1110, 362, "(twisted pair)")
    names = ["J1 base", "J2 shoulder A", "J2 shoulder B", "J3 elbow", "J4 roll", "J5 wrist"]
    for i in range(6):
        x = 80 + i * 165
        p = esc(s, x, dy, None, small=True)
        m = motor(s, x + 33, my, small=True, label=f"ID {i + 1} · {names[i]}")
        for lead, leg, off in (("A+", "U", 0), ("B+", "V", 0), ("A−", "W", -3), ("B−", "W", 3)):
            lx, ly = m[lead]
            yy = ly + 12 + {"A+": 0, "A−": 6, "B+": 12, "B−": 18}[lead]
            s.wire("x", m[lead], (lx, yy), (p[leg][0] + off, yy), (p[leg][0] + off, p[leg][1]),
                   color=MOTOR[lead], width=2.5)
        s.wire("data", p["J3-2"], (p["J3-2"][0], bus_y), width=3)
        s.wire("gnd", p["J3-5"], (p["J3-5"][0], gnd_y), width=3)
        s.wire("vm", p["+"], (p["+"][0], vm_y), width=4)
        s.wire("gnd", p["−"], (p["−"][0], gv_y), width=4)
        s.add(f'<circle cx="{p["J3-2"][0]}" cy="{bus_y}" r="3.5" fill="#202124"/>')
    # supply chain: PSU + -> E-stop -> fuse -> rail
    vm = psu(s, 30, 850, "24 V supply", "for the motors", w=180, h=96)
    e_in, e_out = estop(s, 330, 880)
    s.rect(420, 872, 60, 24, "#ffffff", "#5f6368", 4)
    s.text(450, 889, "fuse", "s", "middle")
    s.wire("vm", vm["+"], (vm["+"][0], 820), (e_in[0] - 20, 820), (e_in[0] - 20, e_in[1]), e_in)
    s.wire("vm", e_out, (420, e_out[1] + 0))
    s.wire("vm", (480, 884), (520, 884), (520, vm_y), width=5)
    s.wire("vm", (100, vm_y), (1150, vm_y), width=5)
    s.wire("gnd", vm["−"], (vm["−"][0], 800), (90, 800), (90, gv_y), (1170, gv_y), width=5)
    s.text(540, 900, "E-stop and fuse in the + line", "s")
    # gripper (later)
    box(s, 1100, 600, 120, 64, "DC/DC", ["24 → 6 V"], "#fce8e6", "#c5221f")
    s.wire("vm", (1150, vm_y), (1150, 664), width=4)
    s.wire("gnd", (1170, gv_y), (1170, 664), width=4)
    sv = servo(s, 1090, 470)
    s.wire("v6", (1190, 600), (1190, 584), (1232, 584), (1232, sv["+6 V"][1]), sv["+6 V"], width=3)
    s.wire("gnd", (1210, 600), (1210, 592), (1236, 592), (1236, sv["GND"][1]), sv["GND"], width=3)
    s.text(1090, 440, "Gripper (later)", "h")
    s.legend(30, 968, ["vm", "gnd", "data", "v5", "sig", "wifi"], cols=6, colw=200)
    s.save("pictorial-level3-robot.svg")


def view_drive_closeup():
    s = Svg(1100, 520, "Close-up of one drive on the robot: four motor wires to U, V and W, "
                       "two supply wires to the + and − pads, two bus wires to J3 pin 2 (DATA) "
                       "and J3 pin 5 (GND)")
    p = esc(s, 420, 120, "doppelstep drive|B-G431B-ESC1, seen from above", ident_left=True)
    m = motor(s, 820, 180, label="stepper motor")
    pads = {"A+": p["U"][0], "B+": p["V"][0], "A−": p["W"][0] - 4, "B−": p["W"][0] + 4}
    for i, lead in enumerate(("A+", "A−", "B+", "B−")):
        lx, ly = m[lead]
        yb, xr, yt = ly + 14 + i * 10, 760 - i * 14, 90 - i * 12
        s.wire("x", m[lead], (lx, yb), (xr, yb), (xr, yt), (pads[lead], yt),
               (pads[lead], p["U"][1]), color=MOTOR[lead], width=4)
    s.tag(860, 400, "black A+ → U · red B+ → V")
    s.tag(860, 424, "green A− and blue B− → W")
    s.wire("vm", p["+"], (p["+"][0], 430), (330, 430), width=6)
    s.wire("gnd", p["−"], (p["−"][0], 450), (330, 450), width=6)
    s.tag(240, 430, "+24 V from the fuse")
    s.tag(240, 456, "− to the ground star point")
    s.wire("data", p["J3-2"], (p["J3-2"][0], 300), (330, 300), width=3)
    s.wire("gnd", p["J3-5"], (p["J3-5"][0], 315), (330, 315), width=3)
    s.tag(220, 300, "bus DATA → J3 pin 2")
    s.tag(220, 326, "bus GND → J3 pin 5")
    s.text(40, 352, "J3 pins 1, 3 and 4 stay free.", "t")
    s.text(40, 372, "Pad positions are simplified: follow the", "s")
    s.text(40, 388, "labels printed on the board.", "s")
    s.text(600, 470, "The micro-USB stays unplugged on the robot.", "s")
    s.legend(40, 500, ["vm", "gnd", "data"], cols=3)
    s.save("pictorial-drive-closeup.svg")


def view_cm4_closeup():
    s = Svg(1100, 470, "Close-up of the CM4-Duino: jumper wires from D14, D15, 3V3 and GND to "
                       "the bus interface on a breadboard, and from there two wires to the "
                       "drives")
    c = cm4duino(s, 120, 120)
    b = breadboard(s, 640, 150)
    s.wire("sig", c["D14"], (c["D14"][0], 70), (600, 70), (600, 230), (b["in"][0], 230), width=4)
    s.wire("sig", c["D15"], (c["D15"][0], 85), (585, 85), (585, 250), (b["in"][0], 250), width=4)
    s.wire("v5", c["3V3"], (c["3V3"][0], 380), (610, 380), (610, 270), (b["in"][0], 270),
           width=4)
    s.wire("gnd", c["GND"], (c["GND"][0], 395), (625, 395), (625, 285), (b["in"][0], 285),
           width=4)
    s.tag(470, 62, "D14 (TX) → U1, U2")
    s.tag(470, 98, "D15 (RX) ← U3")
    s.tag(420, 380, "3V3 → chips + R1")
    s.tag(470, 404, "GND")
    s.wire("data", b["out"], (960, 250), (1060, 250), width=5)
    s.wire("gnd", (870, 285), (960, 285), (1060, 285), width=5)
    s.tag(1000, 230, "DATA")
    s.tag(1000, 312, "GND")
    s.text(965, 345, "to the drives", "t")
    s.text(640, 360, "Circuit and part numbers:", "s")
    s.text(640, 376, "Wiring → bus interface", "s")
    s.legend(40, 450, ["sig", "v5", "gnd", "data"], cols=4)
    s.save("pictorial-cm4duino-closeup.svg")


if __name__ == "__main__":
    view_sim()
    view_bench()
    view_full()
    view_drive_closeup()
    view_cm4_closeup()
