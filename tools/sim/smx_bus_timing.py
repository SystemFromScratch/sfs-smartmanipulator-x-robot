#!/usr/bin/env python3
# Copyright 2026 Anton Vynohradov
# SPDX-License-Identifier: Apache-2.0
"""Measure answer times on a DYNAMIXEL bus (SIL diagnostics).

Opens the serial device (for example /dev/ttyDXL of smx_dxl_bus.py), pings every ID and
sends one Sync Read of Present Position to all of them, then prints when each status
packet arrived. Shows whether the drives answer a Sync Read in turn and how long the
whole answer takes, to compare with the packet timeout of DynamixelSDK.

    smx_bus_timing.py --port /dev/ttyDXL --ids 1,2,3,4,5,6
"""

import argparse
import os
import sys
import termios
import time
import tty

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smx_dxl_bus as bus  # noqa: E402

INST_SYNC_READ = 0x82
ADDR_PRESENT_POSITION = 132


def open_port(path):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY)
    tty.setraw(fd)
    attrs = termios.tcgetattr(fd)
    attrs[6][termios.VMIN], attrs[6][termios.VTIME] = 0, 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    return fd


def collect(fd, count, timeout):
    """Read status packets until count arrived or timeout; returns [(ms, packet)]."""
    t0, buf, out = time.monotonic(), b"", []
    while len(out) < count and time.monotonic() - t0 < timeout:
        chunk = os.read(fd, 512)
        if not chunk:
            time.sleep(0.0002)
            continue
        buf += chunk
        while True:
            pkt, buf = bus.parse_packet(buf)
            if not pkt:
                break
            out.append(((time.monotonic() - t0) * 1000.0, pkt))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", default="/dev/ttyDXL")
    ap.add_argument("--ids", default="1,2,3,4,5,6")
    ap.add_argument("--repeat", type=int, default=5)
    args = ap.parse_args()
    ids = [int(i) for i in args.ids.split(",")]
    fd = open_port(args.port)

    print("PING, one ID at a time:")
    for i in ids:
        os.write(fd, bus.packet(i, bus.INST_PING))
        got = collect(fd, 1, 0.5)
        print(f"  ID {i}: " + (f"{got[0][0]:6.1f} ms" if got else "no answer within 500 ms"))

    params = bytes([ADDR_PRESENT_POSITION, 0, 4, 0]) + bytes(ids)
    for n in range(args.repeat):
        os.write(fd, bus.packet(0xFE, INST_SYNC_READ, params))
        got = collect(fd, len(ids), 0.5)
        arrivals = ", ".join(f"ID {p['id']} {t:5.1f}" for t, p in got)
        missing = [i for i in ids if i not in [p["id"] for _, p in got]]
        total = got[-1][0] if got else float("nan")
        print(f"Sync Read #{n + 1}: {len(got)}/{len(ids)} answers, last after {total:6.1f} ms"
              f" [{arrivals}]" + (f", missing {missing}" if missing else ""))
        time.sleep(0.05)
    # DynamixelSDK: timeout = bytes * tx_time_per_byte + 2 * LATENCY_TIMER(16 ms) + 2 ms
    for baud in (1000000, 57600):
        per_byte = 1000.0 / baud * 10.0
        n_bytes = (11 + 4) * len(ids)
        print(f"DynamixelSDK Sync Read timeout at {baud} bps: "
              f"{n_bytes * per_byte + 2 * 16 + 2:5.1f} ms")
    os.close(fd)


if __name__ == "__main__":
    main()
