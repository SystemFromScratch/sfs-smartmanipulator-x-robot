#!/usr/bin/env python3
# Copyright 2026 Anton Vynohradov
# SPDX-License-Identifier: Apache-2.0
"""Give one DYNAMIXEL drive its joint ID and the bus baud rate (SmartManipulator-X).

A doppelstep drive (like an X series servo) leaves the factory with ID 1 at 57600 bps.
On the arm all drives share one bus, so each one needs its joint ID (1-6) and the bus
baud rate (1 Mbps, decision D8) once, stored in its EEPROM area. Connect **one drive at a
time** and run:

    smx_drive_setup.py --port /dev/ttyDXL --id 3                # real bus, 57600 -> 1 Mbps
    smx_drive_setup.py --tcp localhost:5555 --id 3              # one simulated drive (SIL)

Steps: find the drive (factory ID and baud first, then the target ID and baud), switch
its torque off (the EEPROM area is locked while the torque is on), write the ID (7),
write the Baud Rate (8), then find it again on the new ID and baud rate. A drive that
already has both is left unchanged.

Only the Python standard library is used; the protocol helpers come from
tools/sim/smx_dxl_bus.py.
"""

import argparse
import os
import select
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))

import smx_dxl_bus as dxl  # noqa: E402

ADDR_BAUD_RATE = 8
ADDR_TORQUE_ENABLE = 64
# Baud Rate (8) codes of the X430 Control Table (ROBOTIS e-Manual)
BAUD_CODES = {9600: 0, 57600: 1, 115200: 2, 1000000: 3, 2000000: 4, 3000000: 5,
              4000000: 6, 4500000: 7}


class SerialEndpoint(dxl.Endpoint):
    """One drive on a serial port (POSIX termios), with the interface of dxl.Endpoint."""

    def __init__(self, path):
        super().__init__(path, 0)
        self.path, self.fd = path, None

    @property
    def name(self):
        return self.path

    def open(self, baud):
        import termios
        import tty

        rate = getattr(termios, f"B{baud}", None)
        if rate is None:
            raise ValueError(f"baud rate {baud} is not supported by this system")
        self.close()
        self.fd = os.open(self.path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        tty.setraw(self.fd)
        attrs = termios.tcgetattr(self.fd)
        attrs[4] = attrs[5] = rate
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def transact(self, request, timeout=0.5):
        os.write(self.fd, request)
        buf, deadline = b"", time.monotonic() + timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self.fd], [], [], left)[0]:
                return None
            buf += os.read(self.fd, 256)
            pkt, buf = dxl.parse_packet(buf)
            if pkt and pkt["instruction"] == dxl.INST_STATUS:
                return pkt


class TcpEndpoint(dxl.Endpoint):
    """One simulated drive over TCP; the baud rate does not matter there."""

    def open(self, baud):
        self.close()
        self.connect(timeout=2.0)


def write_byte(ep, dxl_id, address, value):
    st = ep.transact(dxl.packet(dxl_id, dxl.INST_WRITE, bytes([address, 0, value])))
    return bool(st) and st["error"] == 0


def read_byte(ep, dxl_id, address):
    """One register byte, or None."""
    st = ep.transact(dxl.packet(dxl_id, dxl.INST_READ, bytes([address, 0, 1, 0])))
    if st and st["error"] == 0 and len(st["params"]) >= 1:
        return st["params"][0]
    return None


def find(ep, candidates):
    """First (id, baud, model) among the (id, baud) candidates that answers a PING."""
    for dxl_id, baud in candidates:
        ep.open(baud)
        model = ep.ping(dxl_id)
        if model is not None:
            return dxl_id, baud, model
    return None


def setup(ep, target_id, target_baud, from_id=dxl.FACTORY_ID, from_baud=57600, log=print):
    """Gives the drive on @p ep the ID @p target_id at @p target_baud. True on success."""
    code = BAUD_CODES[target_baud]
    found = find(ep, [(from_id, from_baud), (target_id, target_baud),
                      (target_id, from_baud), (from_id, target_baud)])
    if found is None:
        log(f"no drive answers on ID {from_id} or {target_id} at {from_baud} or "
            f"{target_baud} bps; is exactly one drive connected and powered?")
        return False
    dxl_id, baud, model = found
    stored = read_byte(ep, dxl_id, ADDR_BAUD_RATE)
    log(f"found ID {dxl_id} at {baud} bps (model {model}, Baud Rate code {stored})")
    if (dxl_id, stored) == (target_id, code):
        log("already set up: nothing to do")
        return True
    if not write_byte(ep, dxl_id, ADDR_TORQUE_ENABLE, 0):
        log("could not switch the torque off")
        return False
    if dxl_id != target_id:
        if not write_byte(ep, dxl_id, dxl.ADDR_ID, target_id):
            log(f"writing ID {target_id} failed")
            return False
        log(f"ID {dxl_id} -> {target_id}")
    if stored != code:
        # The drive answers at the old rate, then switches.
        if not write_byte(ep, target_id, ADDR_BAUD_RATE, code):
            log(f"writing Baud Rate {code} ({target_baud} bps) failed")
            return False
        log(f"Baud Rate code {stored} -> {code} ({target_baud} bps)")
        time.sleep(0.05)
    found = find(ep, [(target_id, target_baud)])
    if found is None:
        log(f"the drive does not answer on ID {target_id} at {target_baud} bps")
        return False
    log(f"OK: ID {target_id} at {target_baud} bps (model {found[2]})")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--port", help="serial device of the bus (one drive connected)")
    where.add_argument("--tcp", help="host:port of one simulated drive")
    ap.add_argument("--id", type=int, required=True, help="joint ID to give the drive (1-252)")
    ap.add_argument("--baud", type=int, default=1000000, choices=sorted(BAUD_CODES),
                    help="bus baud rate to give the drive (default 1000000, decision D8)")
    ap.add_argument("--from-id", type=int, default=dxl.FACTORY_ID,
                    help="ID of the drive now (default: factory ID 1)")
    ap.add_argument("--from-baud", type=int, default=57600, choices=sorted(BAUD_CODES),
                    help="baud rate of the drive now (default: factory 57600)")
    args = ap.parse_args(argv)
    if not 0 <= args.id <= 252:
        ap.error("--id must be 0..252")

    if args.port:
        ep = SerialEndpoint(args.port)
    else:
        host, _, port = args.tcp.rpartition(":")
        ep = TcpEndpoint(host, int(port))
    try:
        ok = setup(ep, args.id, args.baud, args.from_id, args.from_baud)
    finally:
        ep.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
