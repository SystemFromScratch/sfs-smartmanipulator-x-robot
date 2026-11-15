#!/usr/bin/env python3
# Copyright 2026 Anton Vynohradov
# SPDX-License-Identifier: Apache-2.0
"""Virtual DYNAMIXEL bus for the SIL setup of SmartManipulator-X.

Joins several simulated doppelstep drives (Zephyr native_sim, each started with
``tools/sim/run_native.py run --tcp <port>`` in the doppelstep repository) into one
half-duplex Protocol 2.0 bus and exposes it to the Robot PC as a serial device:

    DynamixelSDK  <->  /dev/ttyDXL (pseudo-terminal)  <->  this tool  <->  TCP  <->  drive 1..N

* Bytes the host writes to the pseudo-terminal go to every drive, like on a shared wire.
* Bytes a drive sends go to the host *and to every other drive*, as on the real wire.
  A drive needs this to take its turn in a Sync Read or Bulk Read (it answers after the
  status packet of the ID before it), and Fast Sync/Bulk Read chaining would need it.
* By default the bus behaves like the wire and leaves the protocol to the drives:
  Fast Sync/Bulk Read are passed on (``--fast-read forward``) and answers reach the host
  as they arrive (``--read-order arrival``). doppelstep with the X430 emulator 1.1.0 or
  later takes turns in a Sync/Bulk Read and stays silent on a Fast Sync/Bulk Read of
  several drives, so the ROBOTIS hardware interface falls back to Sync Read.
* For older firmware, whose drives answer at once, two workarounds remain:
  ``--fast-read drop`` keeps Fast Sync/Bulk Read from the drives (each would answer
  with its own packet), and ``--read-order request`` passes Sync/Bulk Read answers to
  the host in the order of the request (DynamixelSDK drops an answer that arrives
  before its turn).
* No echo: the host does not receive its own packets (the bus interface of the
  CM4-Duino suppresses the echo in hardware, see docs/hardware/wiring.md), and a
  drive does not receive its own bytes back.

A freshly started drive answers on the factory ID 1. ``--assign-ids`` gives each drive
its joint ID before the bus is opened to the host, over that drive's own TCP connection.

Usage (inside the Robot PC container, see docker/docker-compose.sil.yml):

    smx_dxl_bus.py --link /dev/ttyDXL \\
        --devices host.docker.internal:5555,host.docker.internal:5556 \\
        --assign-ids 1,2

Only the Python standard library is used. The bus needs a POSIX system (Linux, WSL 2,
the Robot PC container) for its pseudo-terminal; the protocol helpers also import on
Windows.
"""

import argparse
import errno
import logging
import os
import selectors
import signal
import socket
import sys
import time

LOG = logging.getLogger("smx_dxl_bus")

# ---------------------------------------------------------------- Protocol 2.0
HEADER = b"\xff\xff\xfd\x00"
INST_PING = 0x01
INST_READ = 0x02
INST_WRITE = 0x03
INST_STATUS = 0x55
INST_SYNC_READ = 0x82
INST_BULK_READ = 0x92
INST_FAST_SYNC_READ = 0x8A
INST_FAST_BULK_READ = 0x9A
FAST_READS = (INST_FAST_SYNC_READ, INST_FAST_BULK_READ)
ADDR_MODEL_NUMBER = 0  # 2 bytes
ADDR_ID = 7            # 1 byte, EEPROM area
FACTORY_ID = 1


def _crc_table():
    table = []
    for i in range(256):
        crc = i << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x8005) if crc & 0x8000 else (crc << 1)
        table.append(crc & 0xFFFF)
    return table


_CRC_TABLE = _crc_table()


def crc16(data):
    """CRC-16 of DYNAMIXEL Protocol 2.0 (polynomial 0x8005, initial value 0)."""
    crc = 0
    for b in data:
        crc = ((crc << 8) ^ _CRC_TABLE[((crc >> 8) ^ b) & 0xFF]) & 0xFFFF
    return crc


def stuff(params):
    """Byte stuffing: FF FF FD inside the instruction and parameters gets an extra FD."""
    out = bytearray()
    i = 0
    while i < len(params):
        out.append(params[i])
        if params[i:i + 3] == b"\xff\xff\xfd":
            out += b"\xff\xfd\xfd"
            i += 3
            continue
        i += 1
    return bytes(out)


def unstuff(data):
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i:i + 4] == b"\xff\xff\xfd\xfd":
            out += b"\xff\xff\xfd"
            i += 4
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def split_frames(buf):
    """Split a byte stream into complete raw packets. Returns (frames, rest)."""
    frames = []
    while True:
        start = buf.find(HEADER)
        if start < 0:
            return frames, buf[-3:] if len(buf) > 3 else buf
        buf = buf[start:]
        if len(buf) < 7:
            return frames, buf
        total = 7 + (buf[5] | (buf[6] << 8))
        if len(buf) < total:
            return frames, buf
        frames.append(buf[:total])
        buf = buf[total:]


def packet(dxl_id, instruction, params=b""):
    """Build an instruction packet."""
    body = stuff(bytes([instruction]) + bytes(params))
    length = len(body) + 2
    frame = HEADER + bytes([dxl_id, length & 0xFF, length >> 8]) + body
    crc = crc16(frame)
    return frame + bytes([crc & 0xFF, crc >> 8])


def parse_packet(buf):
    """Find the first complete packet in buf.

    Returns (packet, rest): packet is a dict with id, instruction, params, error (for
    status packets) or None when buf holds no complete packet yet. Bytes before a header
    and packets with a wrong CRC are dropped.
    """
    while True:
        start = buf.find(HEADER)
        if start < 0:
            # keep a possible partial header at the end
            return None, buf[-3:] if len(buf) > 3 else buf
        buf = buf[start:]
        if len(buf) < 7:
            return None, buf
        length = buf[5] | (buf[6] << 8)
        total = 7 + length
        if len(buf) < total:
            return None, buf
        frame, rest = buf[:total], buf[total:]
        if crc16(frame[:-2]) != (frame[-2] | (frame[-1] << 8)):
            LOG.debug("dropping packet with wrong CRC: %s", frame.hex(" "))
            buf = buf[1:]
            continue
        body = unstuff(frame[7:-2])
        pkt = {"id": frame[4], "instruction": body[0]}
        if body[0] == INST_STATUS:
            pkt["error"] = body[1]
            pkt["params"] = body[2:]
        else:
            pkt["params"] = body[1:]
        return pkt, rest


# ---------------------------------------------------------------- drive endpoints
class Endpoint:
    """One simulated drive reached over TCP."""

    def __init__(self, host, port):
        self.host, self.port = host, port
        self.sock = None

    @property
    def name(self):
        return f"{self.host}:{self.port}"

    def connect(self, timeout):
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def transact(self, request, timeout=0.5):
        """Send one instruction and wait for its status packet (blocking, setup only)."""
        self.sock.settimeout(timeout)
        self.sock.sendall(request)
        buf = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                chunk = self.sock.recv(256)
            except socket.timeout:
                break
            if not chunk:
                raise ConnectionError(f"{self.name} closed the connection")
            buf += chunk
            pkt, buf = parse_packet(buf)
            if pkt and pkt["instruction"] == INST_STATUS:
                return pkt
        return None

    def ping(self, dxl_id):
        """Model number of the device on dxl_id, or None if it does not answer."""
        st = self.transact(packet(dxl_id, INST_PING))
        if st and st["id"] == dxl_id and st["error"] == 0 and len(st["params"]) >= 2:
            return st["params"][0] | (st["params"][1] << 8)
        return None

    def write_id(self, old_id, new_id):
        st = self.transact(packet(old_id, INST_WRITE, bytes([ADDR_ID, 0, new_id])))
        return bool(st) and st["error"] == 0


def assign_id(ep, target, retries=20, delay=0.25):
    """Make the drive on ep answer on target: keep it if it already does, else move it
    from the factory ID. Retries while the simulated drive is still starting."""
    for _ in range(retries):
        model = ep.ping(target)
        if model is not None:
            LOG.info("%s: ID %d present (model %d)", ep.name, target, model)
            return True
        model = ep.ping(FACTORY_ID) if target != FACTORY_ID else None
        if model is not None:
            if ep.write_id(FACTORY_ID, target) and ep.ping(target) is not None:
                LOG.info("%s: ID %d -> %d (model %d)", ep.name, FACTORY_ID, target, model)
                return True
            LOG.warning("%s: writing ID %d failed", ep.name, target)
        time.sleep(delay)
    return False


# ---------------------------------------------------------------- pseudo-terminal
class PseudoTerminal:
    """The host side: a pty whose slave end is published under a stable link name."""

    def __init__(self, link):
        import tty  # POSIX only

        self.master, self._slave = os.openpty()
        tty.setraw(self._slave)       # no echo, no line discipline
        self.slave_name = os.ttyname(self._slave)
        self.link = link
        if link:
            try:
                os.unlink(link)
            except FileNotFoundError:
                pass
            os.symlink(self.slave_name, link)
        os.set_blocking(self.master, False)
        # self._slave stays open: otherwise the master reads EIO whenever the host
        # closes the port, and data written meanwhile is lost.

    def close(self):
        if self.link:
            try:
                os.unlink(self.link)
            except OSError:
                pass
        os.close(self.master)
        os.close(self._slave)


# ---------------------------------------------------------------- bus
class Bus:
    READ_ORDER_TIMEOUT = 0.1    # s; give up waiting for a missing answer (keep it below
                                # the host's packet timeout, else late answers leak
                                # into the next read)

    def __init__(self, pty, endpoints, connect_timeout=2.0, fast_read="forward",
                 read_order="arrival"):
        self.pty = pty
        self.fast_read = fast_read
        self.read_order = read_order
        self._order = []          # IDs whose answers are still due, in request order
        self._held = {}           # ID -> status frame that arrived before its turn
        self._order_deadline = 0.0
        self._drive_buf = {}
        self._host_buf = b""
        self.endpoints = endpoints
        self.connect_timeout = connect_timeout
        self.sel = selectors.DefaultSelector()
        self.sel.register(pty.master, selectors.EVENT_READ, "host")
        self.stats = {"to_drives": 0, "to_host": 0, "fast_reads_dropped": 0,
                      "reordered": 0, "reads": 0, "reads_incomplete": 0,
                      "stale_dropped": 0}
        self._running = True
        # read diagnostics: one Sync/Bulk Read at a time
        self._read_t0 = None      # monotonic time of the request
        self._read_ids = []       # IDs asked for
        self._read_seen = {}      # ID -> answer delay [s]
        self._lat = []            # delay of the last answer of each complete read [s]
        self._summary_t = time.monotonic()

    def _attach(self, ep):
        ep.sock.settimeout(None)
        ep.sock.setblocking(False)
        self.sel.register(ep.sock, selectors.EVENT_READ, ep)

    def attach_all(self):
        for ep in self.endpoints:
            if ep.sock:
                self._attach(ep)

    def _drop(self, ep, why):
        LOG.warning("%s disconnected (%s); reconnecting", ep.name, why)
        try:
            self.sel.unregister(ep.sock)
        except (KeyError, ValueError):
            pass
        ep.close()

    def _reconnect(self):
        for ep in self.endpoints:
            if ep.sock is None:
                try:
                    ep.connect(self.connect_timeout)
                    self._attach(ep)
                    LOG.info("%s reconnected", ep.name)
                except OSError:
                    pass

    def _write_host(self, data):
        view = memoryview(data)
        while view:
            try:
                n = os.write(self.pty.master, view)
                view = view[n:]
            except BlockingIOError:
                time.sleep(0.0005)

    def _start_read(self, frame):
        """Remember the IDs of a Sync Read or Bulk Read request (diagnostics, ordering)."""
        if len(frame) < 10:
            return
        inst, params = frame[7], unstuff(frame[8:-2])
        if inst == INST_SYNC_READ:
            ids = list(params[4:])
        elif inst == INST_BULK_READ:
            ids = list(params[0::5])
        else:
            return
        now = time.monotonic()
        self._close_read(now)
        if self.read_order == "request":
            self._order, self._held = ids, {}
            self._order_deadline = now + self.READ_ORDER_TIMEOUT
        self._read_t0, self._read_ids, self._read_seen = now, ids, {}
        self.stats["reads"] += 1

    def _close_read(self, now):
        """A new request (or the summary) ends the previous read: report what was missing."""
        if self._read_t0 is None:
            return
        if self._held:
            # answers held back for an earlier ID that never came: the host has moved on,
            # so they are stale now and would only confuse the next read
            self.stats["stale_dropped"] += len(self._held)
        missing = [i for i in self._read_ids if i not in self._read_seen]
        if missing:
            self.stats["reads_incomplete"] += 1
            got = " ".join(f"{i}:{self._read_seen[i] * 1e3:.1f}"
                           for i in self._read_ids if i in self._read_seen)
            LOG.warning("read incomplete: missing ID %s after %.1f ms (host asked again); "
                        "answered ID:ms %s",
                        ",".join(map(str, missing)), (now - self._read_t0) * 1e3,
                        got or "-")
        elif self._read_seen:
            self._lat.append(max(self._read_seen.values()))
        self._read_t0, self._read_ids, self._read_seen = None, [], {}

    def _summary(self, now, every=10.0):
        if now - self._summary_t < every:
            return
        self._summary_t = now
        lat = sorted(self._lat)
        self._lat = []
        if lat:
            pick = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))] * 1e3
            LOG.info("reads: %d total, %d incomplete, %d stale answers dropped; "
                     "last answer after p50 %.1f / p95 %.1f / max %.1f ms",
                     self.stats["reads"], self.stats["reads_incomplete"],
                     self.stats["stale_dropped"], pick(0.5), pick(0.95), lat[-1] * 1e3)

    def _to_host(self, frame):
        dxl_id, is_status = frame[4], len(frame) > 7 and frame[7] == INST_STATUS
        if (is_status and self._read_t0 is not None and dxl_id in self._read_ids
                and dxl_id not in self._read_seen):
            self._read_seen[dxl_id] = time.monotonic() - self._read_t0
        if self._order and is_status and dxl_id in self._order:
            if dxl_id != self._order[0]:
                self._held[dxl_id] = frame
                self.stats["reordered"] += 1
                return
            self._order.pop(0)
            self._write_host(frame)
            while self._order and self._order[0] in self._held:
                self._write_host(self._held.pop(self._order.pop(0)))
            return
        self._write_host(frame)

    def _flush_order(self):
        """Deadline passed: send what arrived, in request order, and stop waiting."""
        for dxl_id in self._order:
            if dxl_id in self._held:
                self._write_host(self._held.pop(dxl_id))
        self._order, self._held = [], {}

    def stop(self, *_):
        self._running = False

    def run(self):
        last_retry = time.monotonic()
        while self._running:
            for key, _ in self.sel.select(timeout=0.2):
                if key.data == "host":
                    try:
                        data = os.read(self.pty.master, 4096)
                    except (BlockingIOError, InterruptedError):
                        continue
                    except OSError as e:
                        if e.errno == errno.EIO:
                            continue
                        raise
                    frames, self._host_buf = split_frames(self._host_buf + data)
                    for frame in frames:
                        if self.fast_read == "drop" and frame[7] in FAST_READS:
                            self.stats["fast_reads_dropped"] += 1
                            if self.stats["fast_reads_dropped"] == 1:
                                LOG.info("dropping Fast Sync/Bulk Read (see --fast-read)")
                            continue
                        self._start_read(frame)
                        self.stats["to_drives"] += len(frame)
                        for ep in self.endpoints:
                            if ep.sock:
                                try:
                                    ep.sock.sendall(frame)
                                except OSError as e:
                                    self._drop(ep, e)
                else:
                    ep = key.data
                    try:
                        data = ep.sock.recv(4096)
                    except (BlockingIOError, InterruptedError):
                        continue
                    except OSError as e:
                        self._drop(ep, e)
                        continue
                    if not data:
                        self._drop(ep, "closed")
                        continue
                    self.stats["to_host"] += len(data)
                    frames, self._drive_buf[ep] = split_frames(self._drive_buf.get(ep, b"") + data)
                    for frame in frames:
                        self._to_host(frame)
                    # the other drives hear it too (Fast Sync/Bulk Read chaining)
                    for other in self.endpoints:
                        if other is not ep and other.sock:
                            try:
                                other.sock.sendall(data)
                            except OSError as e:
                                self._drop(other, e)
            if self._order and time.monotonic() > self._order_deadline:
                self._flush_order()
            self._summary(time.monotonic())
            if time.monotonic() - last_retry > 1.0:
                last_retry = time.monotonic()
                self._reconnect()


# ---------------------------------------------------------------- command line
def parse_devices(text):
    eps = []
    for item in filter(None, (s.strip() for s in text.split(","))):
        host, _, port = item.rpartition(":")
        if not host or not port.isdigit():
            raise argparse.ArgumentTypeError(f"bad device '{item}', expected host:port")
        eps.append(Endpoint(host, int(port)))
    if not eps:
        raise argparse.ArgumentTypeError("no devices given")
    return eps


def parse_ids(text):
    try:
        ids = [int(s) for s in text.split(",") if s.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f"bad ID list '{text}'") from None
    if any(not 0 <= i <= 252 for i in ids):
        raise argparse.ArgumentTypeError("IDs must be 0..252")
    return ids


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--devices", required=True, type=parse_devices,
                    help="comma-separated host:port of the simulated drives, in ID order")
    ap.add_argument("--assign-ids", type=parse_ids, default=None,
                    help="comma-separated IDs, one per device; moves each drive from the "
                         "factory ID 1 to its joint ID before the bus opens")
    ap.add_argument("--link", default="/dev/ttyDXL",
                    help="path of the serial device for the host (default /dev/ttyDXL)")
    ap.add_argument("--connect-timeout", type=float, default=60.0,
                    help="seconds to wait for every drive at start (default 60)")
    ap.add_argument("--fast-read", choices=("forward", "drop"), default="forward",
                    help="Fast Sync/Bulk Read from the host: forward to the drives (default, "
                         "as on the wire) or drop (workaround for drives without the X430 "
                         "emulator 1.1.0: the host falls back to Sync Read)")
    ap.add_argument("--read-order", choices=("arrival", "request"), default="arrival",
                    help="answers to Sync/Bulk Read: as they arrive (default, as on the "
                         "wire; the drives take turns) or put in the ID order of the "
                         "request (workaround for drives that answer at once)")
    ap.add_argument("--ready-file", default=None,
                    help="file created once the bus is up (for start scripts)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="[smx_dxl_bus] %(levelname)s %(message)s")

    if args.assign_ids is not None and len(args.assign_ids) != len(args.devices):
        ap.error("--assign-ids needs one ID per device")

    deadline = time.monotonic() + args.connect_timeout
    for ep in args.devices:
        while True:
            try:
                ep.connect(timeout=2.0)
                LOG.info("connected to %s", ep.name)
                break
            except OSError as e:
                if time.monotonic() > deadline:
                    LOG.error("cannot reach %s: %s", ep.name, e)
                    return 2
                time.sleep(0.5)

    if args.assign_ids is not None:
        for ep, target in zip(args.devices, args.assign_ids):
            if not assign_id(ep, target):
                LOG.error("%s: no drive answers on ID %d or on the factory ID %d",
                          ep.name, target, FACTORY_ID)
                return 3

    pty = PseudoTerminal(args.link)
    bus = Bus(pty, args.devices, fast_read=args.fast_read, read_order=args.read_order)
    bus.attach_all()
    signal.signal(signal.SIGINT, bus.stop)
    signal.signal(signal.SIGTERM, bus.stop)
    LOG.info("bus up: %s -> %s, %d drive(s)", args.link, pty.slave_name, len(args.devices))
    if args.ready_file:
        with open(args.ready_file, "w", encoding="ascii") as f:
            f.write(pty.slave_name + "\n")
    try:
        bus.run()
    finally:
        LOG.info("bus down: %d bytes to the drives, %d bytes to the host, "
                 "%d Fast Sync/Bulk Read dropped, %d answers put in order, "
                 "%d of %d reads incomplete",
                 bus.stats["to_drives"], bus.stats["to_host"],
                 bus.stats["fast_reads_dropped"], bus.stats["reordered"],
                 bus.stats["reads_incomplete"], bus.stats["reads"])
        pty.close()
        for ep in args.devices:
            ep.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
