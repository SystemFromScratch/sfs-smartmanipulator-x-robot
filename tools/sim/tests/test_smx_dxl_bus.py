# Copyright 2026 Anton Vynohradov
# SPDX-License-Identifier: Apache-2.0
"""Tests of tools/sim/smx_dxl_bus.py with fake drives (standard library only).

    python3 -m unittest discover -s tools/sim/tests -v

The protocol and ID tests run everywhere; the end-to-end tests need a pseudo-terminal
and are skipped on Windows (run them in WSL 2 or Linux).
"""

import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

try:
    import termios
    import tty
    HAVE_PTY = True
except ImportError:   # Windows
    HAVE_PTY = False

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "smx_dxl_bus.py")
sys.path.insert(0, os.path.join(HERE, ".."))

import smx_dxl_bus as bus  # noqa: E402


class FakeDrive:
    """A TCP server that answers like one XM430-W350 (PING, READ and WRITE of the ID)."""

    def __init__(self, dxl_id=bus.FACTORY_ID, model=1020, read_delay=0.0):
        self.id, self.model, self.read_delay = dxl_id, model, read_delay
        self.srv = socket.socket()
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(1)
        self.port = self.srv.getsockname()[1]
        self.received = []
        self._stop = False
        threading.Thread(target=self._serve, daemon=True).start()

    def _status(self, params=b""):
        body = bytes([bus.INST_STATUS, 0]) + params
        length = len(body) + 2
        frame = bus.HEADER + bytes([self.id, length & 0xFF, length >> 8]) + body
        crc = bus.crc16(frame)
        return frame + bytes([crc & 0xFF, crc >> 8])

    def _serve(self):
        while not self._stop:
            try:
                conn, _ = self.srv.accept()
            except OSError:
                return
            buf = b""
            with conn:
                while not self._stop:
                    try:
                        chunk = conn.recv(256)
                    except OSError:
                        break
                    if not chunk:
                        break
                    buf += chunk
                    while True:
                        pkt, buf = bus.parse_packet(buf)
                        if not pkt:
                            break
                        self.received.append(pkt)
                        reply = self._handle(pkt)
                        if reply:
                            conn.sendall(reply)

    def _handle(self, pkt):
        inst, p = pkt["instruction"], pkt["params"]
        if inst == bus.INST_SYNC_READ and pkt["id"] == 0xFE and self.id in p[4:]:
            time.sleep(self.read_delay)       # answers at once, not in turn
            return self._status(bytes([self.id, 0, 0, 0]))
        if pkt["id"] != self.id:
            return None              # not addressed: stay silent, like on the bus
        if inst == bus.INST_PING:
            return self._status(bytes([self.model & 0xFF, self.model >> 8, 52]))
        if inst == bus.INST_READ and p[0] == bus.ADDR_ID:
            return self._status(bytes([self.id]))
        if inst == bus.INST_WRITE and p[0] == bus.ADDR_ID:
            reply = self._status()
            self.id = p[2]
            return reply
        return None

    def close(self):
        self._stop = True
        self.srv.close()


class ProtocolTest(unittest.TestCase):
    def test_ping_packet_matches_robotis_example(self):
        # ROBOTIS e-Manual, Protocol 2.0, PING example for ID 1
        self.assertEqual(bus.packet(1, bus.INST_PING).hex(" "), "ff ff fd 00 01 03 00 01 19 4e")

    def test_stuffing_round_trip(self):
        raw = bytes([0x03, 0xFF, 0xFF, 0xFD, 0x10])
        stuffed = bus.stuff(raw)
        self.assertEqual(stuffed, bytes([0x03, 0xFF, 0xFF, 0xFD, 0xFD, 0x10]))
        self.assertEqual(bus.unstuff(stuffed), raw)

    def test_parse_skips_garbage_and_bad_crc(self):
        good = bus.packet(3, bus.INST_PING)
        bad = bytearray(bus.packet(2, bus.INST_PING))
        bad[-1] ^= 0xFF
        pkt, rest = bus.parse_packet(b"\x00\x12" + bytes(bad) + good + b"\xff\xff")
        self.assertEqual((pkt["id"], pkt["instruction"]), (3, bus.INST_PING))
        self.assertEqual(rest, b"\xff\xff")

    def test_split_frames(self):
        a, b = bus.packet(1, bus.INST_PING), bus.packet(2, bus.INST_PING)
        frames, rest = bus.split_frames(b"\x00" + a + b + b[:5])
        self.assertEqual(frames, [a, b])
        self.assertEqual(rest, b[:5])

    def test_parse_waits_for_complete_packet(self):
        frame = bus.packet(1, bus.INST_PING)
        pkt, rest = bus.parse_packet(frame[:6])
        self.assertIsNone(pkt)
        self.assertEqual(rest, frame[:6])


class AssignIdTest(unittest.TestCase):
    def test_moves_drive_from_factory_id(self):
        d = FakeDrive()
        ep = bus.Endpoint("127.0.0.1", d.port)
        ep.connect(1.0)
        self.assertTrue(bus.assign_id(ep, 4, retries=3, delay=0.01))
        self.assertEqual(d.id, 4)
        ep.close()
        d.close()

    def test_keeps_drive_that_already_has_its_id(self):
        d = FakeDrive(dxl_id=5)
        ep = bus.Endpoint("127.0.0.1", d.port)
        ep.connect(1.0)
        self.assertTrue(bus.assign_id(ep, 5, retries=3, delay=0.01))
        self.assertFalse(any(p["instruction"] == bus.INST_WRITE for p in d.received))
        ep.close()
        d.close()


def _open_serial(path):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY)
    tty.setraw(fd)
    attrs = termios.tcgetattr(fd)
    attrs[6][termios.VMIN], attrs[6][termios.VTIME] = 0, 1   # 0.1 s read timeout
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    return fd


def _read_status(fd, timeout=1.0):
    buf, deadline = b"", time.monotonic() + timeout
    while time.monotonic() < deadline:
        buf += os.read(fd, 256)
        pkt, buf = bus.parse_packet(buf)
        if pkt:
            return pkt, buf
    return None, buf


@unittest.skipUnless(HAVE_PTY, "needs a POSIX pseudo-terminal (Linux, WSL 2)")
class BusEndToEndTest(unittest.TestCase):
    def setUp(self):
        # the later the ID, the sooner it answers: the worst order for the host
        self.drives = [FakeDrive(read_delay=d) for d in (0.03, 0.015, 0.0)]
        self.tmp = tempfile.mkdtemp()
        self.link = os.path.join(self.tmp, "ttyDXL")
        ready = os.path.join(self.tmp, "ready")
        devices = ",".join(f"127.0.0.1:{d.port}" for d in self.drives)
        self.proc = subprocess.Popen(
            [sys.executable, TOOL, "--devices", devices, "--assign-ids", "1,2,3",
             "--link", self.link, "--ready-file", ready, "--connect-timeout", "5"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 10
        while not os.path.exists(ready):
            if self.proc.poll() is not None or time.monotonic() > deadline:
                self.fail("bus did not start: " + self.proc.stdout.read().decode())
            time.sleep(0.05)
        self.fd = _open_serial(self.link)

    def tearDown(self):
        os.close(self.fd)
        if self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(5)
        self.proc.stdout.close()
        for d in self.drives:
            d.close()

    def test_every_id_answers_through_the_pty(self):
        for dxl_id in (1, 2, 3):
            os.write(self.fd, bus.packet(dxl_id, bus.INST_PING))
            st, rest = _read_status(self.fd)
            self.assertIsNotNone(st, f"no answer from ID {dxl_id}")
            self.assertEqual(st["id"], dxl_id)
            self.assertEqual(st["params"][0] | st["params"][1] << 8, 1020)
            self.assertEqual(rest, b"", "the host must not receive its own packet (echo)")

    def test_other_drives_hear_the_answer(self):
        # Fast Sync Read: a drive must hear the status of the drive before it
        os.write(self.fd, bus.packet(1, bus.INST_PING))
        st, _ = _read_status(self.fd)
        self.assertEqual(st["id"], 1)
        deadline = time.monotonic() + 1.0
        heard = []
        while time.monotonic() < deadline and not heard:
            heard = [p for p in self.drives[1].received
                     if p["instruction"] == bus.INST_STATUS and p["id"] == 1]
            time.sleep(0.02)
        self.assertTrue(heard, "drive 2 did not hear the status packet of drive 1")
        own = [p for p in self.drives[0].received if p["instruction"] == bus.INST_STATUS]
        self.assertEqual(own, [], "a drive must not receive its own bytes back")

    def test_sync_read_answers_come_in_request_order(self):
        params = bytes([132, 0, 4, 0, 1, 2, 3])
        os.write(self.fd, bus.packet(0xFE, bus.INST_SYNC_READ, params))
        order, buf, deadline = [], b"", time.monotonic() + 1.0
        while len(order) < 3 and time.monotonic() < deadline:
            buf += os.read(self.fd, 256)
            while True:
                pkt, buf = bus.parse_packet(buf)
                if not pkt:
                    break
                order.append(pkt["id"])
        self.assertEqual(order, [1, 2, 3])

    def test_incomplete_read_is_reported(self):
        # ID 9 does not exist: the read stays incomplete until the host asks again
        os.write(self.fd, bus.packet(0xFE, bus.INST_SYNC_READ, bytes([132, 0, 4, 0, 1, 9])))
        time.sleep(0.2)
        os.write(self.fd, bus.packet(0xFE, bus.INST_SYNC_READ, bytes([132, 0, 4, 0, 1])))
        time.sleep(0.2)
        self.proc.terminate()
        out = self.proc.communicate(timeout=5)[0].decode()
        self.assertIn("read incomplete: missing ID 9", out)
        self.assertIn("1 of 2 reads incomplete", out)

    def test_fast_sync_read_is_not_passed_on(self):
        # Fast Sync Read of IDs 1-3, Present Position (address 132, 4 bytes)
        params = bytes([132, 0, 4, 0, 1, 2, 3])
        os.write(self.fd, bus.packet(0xFE, bus.INST_FAST_SYNC_READ, params))
        st, _ = _read_status(self.fd, timeout=0.3)
        self.assertIsNone(st, "the host must get no answer, so it falls back to Sync Read")
        for d in self.drives:
            self.assertFalse(any(p["instruction"] == bus.INST_FAST_SYNC_READ for p in d.received))
        # the bus still works afterwards
        os.write(self.fd, bus.packet(3, bus.INST_PING))
        st, _ = _read_status(self.fd)
        self.assertEqual(st["id"], 3)

    def test_unknown_id_stays_silent(self):
        os.write(self.fd, bus.packet(9, bus.INST_PING))
        st, _ = _read_status(self.fd, timeout=0.3)
        self.assertIsNone(st)

    def test_host_reopening_the_port_keeps_the_bus(self):
        os.close(self.fd)
        self.fd = _open_serial(self.link)
        os.write(self.fd, bus.packet(2, bus.INST_PING))
        st, _ = _read_status(self.fd)
        self.assertEqual(st["id"], 2)


if __name__ == "__main__":
    unittest.main()
