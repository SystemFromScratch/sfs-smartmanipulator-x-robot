#!/usr/bin/env python3
"""Wiring diagrams of SmartManipulator-X (docs/hardware/images/wiring-*.svg).

Plain SVG, drawn in the style of the architecture diagram, so the website and the PDF
manual (WeasyPrint, no JavaScript) render them the same. Run from the repository root:

    python tools/docs/wiring_diagrams.py

Every pin and connector name here must match docs/hardware/wiring.md and
docs/hardware/gripper-servo.md; change both together.
"""
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "hardware", "images")

STYLE = """
    .pc { fill: #f1f3f4; stroke: #5f6368; stroke-width: 1.5; }
    .kit { fill: #e8f0fe; stroke: #1a73e8; stroke-width: 1.5; }
    .ic { fill: #ffffff; stroke: #1a73e8; stroke-width: 1.5; }
    .fab { fill: #e6f4ea; stroke: #188038; stroke-width: 1.5; }
    .drv { fill: #fef7e0; stroke: #b06000; stroke-width: 1.5; }
    .pwr { fill: #fce8e6; stroke: #c5221f; stroke-width: 1.5; }
    .fut { fill: #ffffff; stroke: #9aa0a6; stroke-width: 1.5; stroke-dasharray: 6 4; }
    .pad { fill: #ffffff; stroke: #3c4043; stroke-width: 1.2; }
    .h { font-weight: 700; font-size: 15px; fill: #202124; }
    .t { fill: #202124; }
    .s { fill: #5f6368; font-size: 12px; }
    .n { fill: #1a73e8; font-size: 12px; font-weight: 600; }
    .w { stroke: #3c4043; stroke-width: 2; fill: none; }
    .data { stroke: #188038; stroke-width: 2.5; fill: none; }
    .gnd { stroke: #202124; stroke-width: 2.5; fill: none; }
    .vm { stroke: #c5221f; stroke-width: 3; fill: none; }
    .v6 { stroke: #e37400; stroke-width: 2.5; fill: none; }
    .v5 { stroke: #b06000; stroke-width: 2.5; fill: none; }
    .sig { stroke: #1a73e8; stroke-width: 2; fill: none; }
    .ph { stroke: #9334e6; stroke-width: 2.5; fill: none; }
    .nc { stroke: #9aa0a6; stroke-width: 1.5; fill: none; stroke-dasharray: 4 3; }
    .dot { fill: #202124; }
"""


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title, self.parts = w, h, title, []

    def add(self, s):
        self.parts.append("  " + s)

    def box(self, cls, x, y, w, h, title=None, lines=(), small=None, rx=8):
        self.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>')
        yy = y + 24
        if title:
            self.add(f'<text class="h" x="{x + 12}" y="{yy}">{title}</text>')
            yy += 21
        for line in lines:
            self.add(f'<text class="t" x="{x + 12}" y="{yy}">{line}</text>')
            yy += 18
        if small:
            for line in ([small] if isinstance(small, str) else small):
                self.add(f'<text class="s" x="{x + 12}" y="{yy}">{line}</text>')
                yy += 16

    def text(self, x, y, s, cls="t", anchor="start"):
        self.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{s}</text>')

    def line(self, cls, *pts):
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        self.add(f'<path class="{cls}" d="{d}"/>')

    def dot(self, x, y):
        self.add(f'<circle class="dot" cx="{x}" cy="{y}" r="3.5"/>')

    def pin(self, x, y, label, side="right", w=150):
        """A labelled connector pad; returns the wire attachment point."""
        self.add(f'<rect class="pad" x="{x}" y="{y - 10}" width="{w}" height="20" rx="3"/>')
        self.add(f'<text class="t" x="{x + 8}" y="{y + 4}" font-size="12">{label}</text>')
        return (x + w, y) if side == "right" else (x, y)

    def gnd_symbol(self, x, y):
        self.line("w", (x, y), (x, y + 8))
        for i, half in enumerate((10, 6, 2)):
            yy = y + 8 + i * 4
            self.line("w", (x - half, yy), (x + half, yy))

    def resistor(self, x, y, horizontal, label):
        if horizontal:
            self.add(f'<rect class="pad" x="{x}" y="{y - 6}" width="34" height="12"/>')
            self.text(x + 17, y - 10, label, "s", "middle")
            return (x, y), (x + 34, y)
        self.add(f'<rect class="pad" x="{x - 6}" y="{y}" width="12" height="34"/>')
        self.text(x + 10, y + 21, label, "s")
        return (x, y), (x, y + 34)

    def cap(self, x, y, label, left=False):
        """Vertical capacitor from (x, y) downwards; returns the bottom point."""
        self.line("w", (x, y), (x, y + 12))
        self.line("w", (x - 10, y + 12), (x + 10, y + 12))
        self.line("w", (x - 10, y + 17), (x + 10, y + 17))
        self.line("w", (x, y + 17), (x, y + 29))
        if left:
            self.text(x - 14, y + 19, label, "s", "end")
        else:
            self.text(x + 14, y + 19, label, "s")
        return (x, y + 29)

    def legend(self, x, y, items):
        for i, (cls, label) in enumerate(items):
            yy = y + i * 18
            self.line(cls, (x, yy), (x + 28, yy))
            self.text(x + 36, yy + 4, label, "s")

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" font-family="Segoe UI, DejaVu Sans, Arial, '
                f'sans-serif" font-size="13" role="img" aria-label="{self.title}">\n'
                f'  <title>{self.title}</title>\n  <style>{STYLE}  </style>\n')
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(head + "\n".join(self.parts) + "\n</svg>\n")
        print("wrote", os.path.join(OUT, name))


def gate(svg, x, y, name, part, inputs, output):
    """A logic gate as a block: input pins on the left, output on the right."""
    h = 34 + 24 * (len(inputs) - 1)
    svg.add(f'<rect class="ic" x="{x}" y="{y}" width="120" height="{h}" rx="4"/>')
    svg.text(x + 60, y - 18, name, "n", "middle")
    svg.text(x + 60, y - 5, part, "s", "middle")
    pins = []
    for i, label in enumerate(inputs):
        yy = y + 17 + 24 * i
        svg.text(x + 6, yy + 4, label, "s")
        pins.append((x, yy))
    oy = y + h / 2
    svg.text(x + 114, oy + 4, output, "s", "end")
    return pins, (x + 120, oy)


# ----------------------------------------------------------------- bus interface
def bus_interface():
    s = Svg(1000, 560, "Bus interface between the CM4-Duino UART0 and the single-wire "
                       "DYNAMIXEL bus: open-drain driver, echo-blocking receive gate, pull-up")
    s.box("kit", 20, 20, 220, 300, "CM4-Duino", [], ["Arduino headers, 3.3 V logic"])
    tx = s.pin(40, 110, "D14 · GPIO14 TXD0", w=180)
    rx = s.pin(40, 160, "D15 · GPIO15 RXD0", w=180)
    v33 = s.pin(40, 230, "3V3 (power header)", w=180)
    gnd = s.pin(40, 280, "GND", w=180)

    s.box("pc", 290, 20, 520, 420, "Bus interface (breadboard, later a shield)", [])
    s.text(300, 432, "Each gate: 100 nF from VCC (3V3) to GND, next to the IC", "s")

    u1_in, u1_out = gate(s, 440, 90, "U1", "74LVC1G07 · open-drain buffer", ["A"], "Y")
    u2_in, u2_out = gate(s, 330, 250, "U2", "74LVC1G04", ["A"], "Y")
    u3_in, u3_out = gate(s, 600, 250, "U3", "74LVC1G32 · OR", ["A", "B"], "Y")

    # TX -> U1 and U2
    s.line("sig", tx, (300, 110), (300, u1_in[0][1]), u1_in[0])
    s.dot(300, 110)
    s.line("sig", (300, 110), (300, u2_in[0][1]), u2_in[0])
    s.dot(300, u1_in[0][1])
    # U2 out (/TX) -> U3 B
    s.line("sig", u2_out, (520, u2_out[1]), (520, u3_in[1][1]), u3_in[1])
    s.text(528, u2_out[1] - 6, "/TX", "s")
    # DATA node
    data_x = 700
    s.line("data", u1_out, (data_x, u1_out[1]))
    s.dot(data_x, u1_out[1])
    # pull-up R1 from 3V3 rail
    s.line("v5", (data_x, 48), (data_x, 55))
    s.text(data_x + 8, 46, "3V3", "s")
    a, b = s.resistor(data_x, 55, False, "R1 470 Ω")
    s.line("data", b, (data_x, u1_out[1]))
    # RC delay into U3 A
    s.line("data", (data_x, u1_out[1]), (data_x, 170))
    a, b = s.resistor(data_x - 34, 170, True, "")
    s.text(data_x - 17, 160, "R2 100 Ω", "s", "middle")
    s.line("data", (data_x, 170), b)
    s.line("data", a, (575, 170), (575, u3_in[0][1]), u3_in[0])
    s.dot(620, 170)
    bot = s.cap(620, 170, "C1 100 pF")
    s.gnd_symbol(*bot)
    # U3 out -> RX
    s.line("sig", u3_out, (760, u3_out[1]), (760, 400), (260, 400), (260, 160), rx)
    # 3V3 and GND to the interface
    s.line("v5", v33, (270, 230), (270, 48), (data_x, 48))
    s.line("gnd", gnd, (280, 280), (280, 470), (900, 470))
    # bus connector
    s.box("fab", 840, 60, 140, 140, "BUS", [], ["to all drives"])
    d = s.pin(850, 120, "1 DATA", side="left", w=120)
    g = s.pin(850, 170, "2 GND", side="left", w=120)
    s.line("data", (data_x, u1_out[1]), (790, u1_out[1]), (790, d[1]), d)
    s.line("gnd", (900, 470), (900, 230), (830, 230), (830, g[1]), g)

    s.legend(30, 360, [("sig", "logic signal (3.3 V)"), ("data", "bus DATA"),
                       ("gnd", "ground"), ("v5", "3V3 supply")])
    s.text(20, 500, "Sending: U1 pulls DATA low for every 0 bit; R1 pulls it back to 3.3 V. "
           "Receiving: U3 passes DATA to RXD0 only while TXD0 is high,", "s")
    s.text(20, 518, "so the CM4 does not receive its own transmission (no echo). "
           "R2/C1 delay DATA by ~10 ns against /TX, so no glitch reaches RXD0 at a falling edge.", "s")
    s.text(20, 536, "Proposed circuit: build and measure it in Stage 3 before relying on it.", "s")
    s.save("wiring-bus-interface.svg")


# ----------------------------------------------------------------- drive node
def drive_node():
    s = Svg(1060, 590, "Connections of one doppelstep drive (B-G431B-ESC1): motor supply on "
                       "J5/J6, stepper coils on J7, DYNAMIXEL bus on J3")
    s.box("fab", 330, 60, 380, 500, "B-G431B-ESC1 · doppelstep", ["STM32G431CB, Zephyr"],
          ["power stage: 3 half-bridges, current sensing"])
    # ST-LINK
    s.box("pc", 400, 150, 240, 70, "ST-LINK (on board)", ["micro-USB: VCP = USART2, SWD, RTT"])
    s.line("sig", (520, 150), (520, 30))
    s.text(528, 40, "USB to the bench PC (Stage 2 only)", "s")
    # power pads
    vp = s.pin(340, 280, "J5  V+  (+)", side="left", w=110)
    vn = s.pin(340, 330, "J6  GND (−)", side="left", w=110)
    s.box("pwr", 20, 245, 220, 120, "Motor supply V_M", ["from the distribution rail"],
          ["voltage: open (≤ 24 V, see text)", "short, thick wires"])
    s.line("vm", (240, 280), vp)
    s.line("gnd", (240, 330), vn)
    # motor pads
    o1 = s.pin(600, 270, "J7  OUT1", w=100)
    o2 = s.pin(600, 310, "J7  OUT2", w=100)
    o3 = s.pin(600, 350, "J7  OUT3", w=100)
    s.box("drv", 820, 230, 220, 170, "Stepper motor", ["bipolar, 4 wires"], [])
    s.text(832, 300, "Coil A: A+ / A−", "t")
    s.text(832, 322, "Coil B: B+ / B−", "t")
    s.text(832, 352, "A− and B− share OUT3", "s")
    s.text(832, 368, "(assumed, see text)", "s")
    s.line("ph", o1, (800, 270), (820, 270))
    s.text(760, 264, "A+", "s")
    s.line("ph", o2, (780, 310), (780, 330), (820, 330))
    s.text(760, 304, "B+", "s")
    s.line("ph", o3, (760, 350), (760, 385), (820, 385))
    s.text(728, 344, "A−, B−", "s")
    # J3 bus pads
    s.text(345, 418, "J3 (pads, fit a 5-pin header)", "n")
    labels = ["1  +5V (BEC output)", "2  USART2_TX · PB3", "3  USART2_RX · PB4",
              "4  PWM · PA15", "5  GND"]
    xs = [340 + i * 0 for i in range(5)]
    pts = []
    for i, label in enumerate(labels):
        y = 450 + i * 22
        pts.append(s.pin(xs[i], y, label, w=170))
    # bus
    s.box("fab", 820, 440, 220, 90, "DYNAMIXEL bus", ["DATA, GND"], ["daisy chain to the next drive"])
    s.line("data", pts[1], (760, pts[1][1]), (760, 470), (820, 470))
    s.line("gnd", pts[4], (780, pts[4][1]), (780, 505), (820, 505))
    for i in (0, 2, 3):
        s.line("nc", pts[i], (540, pts[i][1]))
        s.text(546, pts[i][1] + 4, "not connected", "s")
    s.legend(20, 430, [("vm", "motor supply"), ("gnd", "ground"), ("ph", "motor phase"),
                       ("data", "bus DATA"), ("nc", "not connected")])
    s.save("wiring-drive-node.svg")


# ----------------------------------------------------------------- power
def power():
    s = Svg(1100, 600, "Power distribution: motor supply with emergency stop and fuse to six "
                       "drives and the servo converter, separate 5 V supply for the CM4-Duino, "
                       "one ground star point")
    s.box("pwr", 20, 40, 190, 100, "Motor PSU", ["V_M (open, ≤ 24 V)"], ["mains powered"])
    s.box("fut", 250, 55, 130, 70, "E-stop", ["cuts V_M"], None)
    s.box("pwr", 420, 55, 110, 70, "Fuse F1", ["main"], None)
    s.line("vm", (210, 80), (250, 80))
    s.line("vm", (380, 90), (420, 90))
    s.line("vm", (530, 90), (570, 90), (570, 200), (1060, 200))
    s.text(580, 192, "V_M rail", "s")
    # drives
    for i in range(6):
        x = 40 + i * 150
        s.box("fab", x, 260, 130, 80, f"Drive ID {i + 1}", ["J5 (+) / J6 (−)"], None)
        s.line("vm", (x + 40, 200), (x + 40, 260))
        s.dot(x + 40, 200)
        s.line("gnd", (x + 90, 340), (x + 90, 400))
        s.dot(x + 90, 400)
    # servo converter
    s.box("pwr", 940, 240, 150, 100, "DC/DC 6 V", ["≥ 5 A"], ["servo only"])
    s.line("vm", (1060, 200), (1060, 240))
    s.box("drv", 940, 440, 150, 70, "Gripper servo", ["MG996R"], None)
    s.line("v6", (1000, 340), (1000, 440))
    s.text(1006, 400, "+6 V", "s")
    s.line("gnd", (1040, 340), (1040, 400))
    s.dot(1040, 400)
    s.line("gnd", (1070, 440), (1070, 400))
    # ground rail and star point
    s.line("gnd", (130, 400), (1070, 400))
    s.line("gnd", (130, 400), (130, 140))
    s.dot(130, 400)
    s.text(140, 420, "GND star point at the minus terminal of the motor PSU", "s")
    # CM4 supply
    s.box("pc", 20, 450, 190, 90, "USB-C PSU", ["5 V, ≥ 3 A"], ["separate mains adapter"])
    s.box("kit", 260, 450, 200, 90, "CM4-Duino + CM4", ["Type-C input"], None)
    s.line("v5", (210, 480), (260, 480))
    s.text(214, 472, "5 V", "s")
    s.box("pc", 520, 450, 200, 90, "Bus interface", ["DATA + GND to the drives"], None)
    s.line("w", (460, 495), (520, 495))
    s.line("gnd", (620, 450), (620, 400))
    s.dot(620, 400)
    s.text(628, 430, "bus GND = the only ground", "s")
    s.text(628, 444, "path of the CM4-Duino", "s")
    s.legend(760, 560, [("vm", "V_M"), ("v6", "6 V servo")])
    s.legend(900, 560, [("v5", "5 V logic"), ("gnd", "ground")])
    s.save("wiring-power.svg")


# ----------------------------------------------------------------- bus chain
def bus_chain():
    s = Svg(1100, 330, "DYNAMIXEL bus wiring: the CM4-Duino bus interface feeds DATA and GND "
                       "in a daisy chain to the J3 pads of drives 1 to 6 and to the gripper node")
    s.box("kit", 20, 30, 170, 110, "CM4-Duino", ["D14 TX, D15 RX"], ["3V3, GND"])
    s.box("pc", 230, 30, 170, 110, "Bus interface", ["U1–U3, R1"], ["see the circuit"])
    s.line("sig", (190, 70), (230, 70))
    s.line("sig", (190, 90), (230, 90))
    s.line("gnd", (190, 120), (230, 120))
    s.line("data", (400, 75), (1080, 75))
    s.line("gnd", (400, 115), (1080, 115))
    s.text(410, 66, "DATA", "n")
    s.text(410, 133, "GND", "s")
    for i in range(6):
        x = 440 + i * 95
        s.line("data", (x + 25, 75), (x + 25, 190))
        s.line("gnd", (x + 55, 115), (x + 55, 190))
        s.dot(x + 25, 75)
        s.dot(x + 55, 115)
        s.box("fab", x, 190, 85, 80, f"ID {i + 1}", ["J3-2, J3-5"], None, rx=6)
    x = 440 + 6 * 95
    s.line("nc", (x + 25, 75), (x + 25, 190))
    s.line("nc", (x + 55, 115), (x + 55, 190))
    s.box("fut", x, 190, 85, 80, "ID 7", ["gripper"], None, rx=6)
    s.text(20, 300, "Order on the cable does not matter (IDs are set in each drive). "
           "Keep the cable short (about 1.5 m along the arm) and away from the motor phases; "
           "twist DATA with GND.", "s")
    s.save("wiring-bus-chain.svg")


# ----------------------------------------------------------------- gripper servo
def gripper():
    s = Svg(1000, 430, "Gripper servo wiring: the gripper node on the DYNAMIXEL bus drives "
                       "the MG996R signal; the servo is powered from its own 6 V converter")
    s.box("fut", 20, 40, 260, 230, "Gripper node (ID 7)", ["virtual DYNAMIXEL"],
          ["separate project, MCU open"])
    bd = s.pin(40, 130, "bus DATA", w=150)
    bg = s.pin(40, 170, "GND", w=150)
    pw = s.pin(40, 220, "PWM out (3.3 V, 50 Hz)", w=200)
    s.box("fab", 20, 320, 170, 70, "DYNAMIXEL bus", ["DATA, GND"], None)
    s.line("data", (40 - 0, 130), (10, 130), (10, 340), (20, 340))
    s.line("gnd", (40, 170), (14, 170), (14, 370), (20, 370))
    s.box("pwr", 360, 40, 180, 90, "DC/DC 6 V", ["≥ 5 A, from V_M"], ["servo only"])
    s.box("drv", 700, 150, 270, 170, "MG996R", [], None)
    sig = s.pin(710, 200, "orange · signal", side="left", w=160)
    vp = s.pin(710, 240, "red · +6 V", side="left", w=160)
    vn = s.pin(710, 280, "brown · GND", side="left", w=160)
    s.line("sig", pw, (600, 220), (600, 200), sig)
    s.line("v6", (540, 70), (650, 70), (650, 240), vp)
    s.line("gnd", (540, 110), (630, 110), (630, 280), vn)
    s.line("gnd", bg, (300, 170), (300, 280), (630, 280))
    s.dot(630, 280)
    bot = s.cap(670, 240, "C2 470–1000 µF, ≥ 10 V", left=True)
    s.dot(670, 240)
    s.line("gnd", bot, (670, 280))
    s.dot(670, 280)
    s.line("gnd", (630, 280), (630, 360), (400, 360))
    s.text(260, 380, "to the GND star point (motor PSU minus)", "s")
    s.legend(760, 360, [("sig", "PWM signal"), ("v6", "+6 V"), ("gnd", "ground")])
    s.save("wiring-gripper-servo.svg")


if __name__ == "__main__":
    bus_interface()
    drive_node()
    power()
    bus_chain()
    gripper()
