# Copyright 2026 Anton Vynohradov
# SPDX-License-Identifier: Apache-2.0
"""Tests of tools/diagnostics/smx_drive_setup.py with a fake drive over TCP.

    python3 -m unittest discover -s tools/sim/tests -v
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "diagnostics"))

import smx_drive_setup as setup_tool  # noqa: E402
from test_smx_dxl_bus import FakeDrive  # noqa: E402


class DriveSetupTest(unittest.TestCase):
    def setUp(self):
        self.lines = []

    def run_setup(self, drive, target_id, baud=1000000, **kw):
        ep = setup_tool.TcpEndpoint("127.0.0.1", drive.port)
        try:
            return setup_tool.setup(ep, target_id, baud, log=self.lines.append, **kw)
        finally:
            ep.close()
            drive.close()

    def test_factory_drive_gets_id_and_baud_rate(self):
        d = FakeDrive()
        d.regs[64] = 1                      # torque on: the tool switches it off first
        self.assertTrue(self.run_setup(d, 3))
        self.assertEqual((d.id, d.regs[8], d.regs[64]), (3, 3, 0))
        self.assertIn("OK: ID 3 at 1000000 bps (model 1020)", self.lines)

    def test_drive_that_is_set_up_is_left_alone(self):
        d = FakeDrive(dxl_id=4)
        d.regs[8] = 3
        # over TCP every baud rate reaches the drive: the factory ID is tried first
        self.assertTrue(self.run_setup(d, 4))
        self.assertEqual(d.id, 4)

    def test_other_baud_rate_only(self):
        d = FakeDrive(dxl_id=2)
        self.assertTrue(self.run_setup(d, 2, baud=115200))
        self.assertEqual((d.id, d.regs[8]), (2, 2))

    def test_no_drive_found(self):
        d = FakeDrive(dxl_id=9)
        self.assertFalse(self.run_setup(d, 3))
        self.assertTrue(self.lines[-1].startswith("no drive answers"))

    def test_command_line_rejects_bad_id(self):
        with self.assertRaises(SystemExit):
            setup_tool.main(["--tcp", "127.0.0.1:1", "--id", "300"])


if __name__ == "__main__":
    unittest.main()
